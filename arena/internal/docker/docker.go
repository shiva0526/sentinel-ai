package docker

import (
	"archive/tar"
	"bytes"
	"context"
	"fmt"
	"time"

	"github.com/docker/docker/api/types/container"
	"github.com/docker/docker/api/types/image"
	"github.com/docker/docker/client"
	"github.com/docker/docker/pkg/stdcopy"
)

const (
	SandboxImage   = "python:3.10-slim"
	SandboxWorkDir = "/app"
	ExecTimeout    = 10 * time.Second
)

// SandboxResult holds stdout and stderr captured from a container run.
type SandboxResult struct {
	Stdout string
	Stderr string
}

// RunInSandbox creates a network-isolated Docker container, injects the
// given files, executes the command, and returns captured output.
// The container is always force-removed after execution.
func RunInSandbox(ctx context.Context, files map[string]string, cmd string) (*SandboxResult, error) {
	cli, err := client.NewClientWithOpts(client.FromEnv, client.WithAPIVersionNegotiation())
	if err != nil {
		return nil, fmt.Errorf("docker connect: %w", err)
	}

	// Pull the image (no-op if cached)
	cli.ImagePull(ctx, SandboxImage, image.PullOptions{})

	// Create a hardened container
	resp, err := cli.ContainerCreate(ctx, &container.Config{
		Image:      SandboxImage,
		WorkingDir: SandboxWorkDir,
		Cmd:        []string{"sh", "-c", cmd},
		Tty:        false,
	}, &container.HostConfig{
		AutoRemove:  false,
		NetworkMode: "none", // No internet access
	}, nil, nil, "")
	if err != nil {
		return nil, fmt.Errorf("container create: %w", err)
	}
	defer cli.ContainerRemove(ctx, resp.ID, container.RemoveOptions{Force: true})

	// Inject files
	for name, content := range files {
		if err := injectFile(ctx, cli, resp.ID, name, content); err != nil {
			return nil, fmt.Errorf("inject %s: %w", name, err)
		}
	}

	// Start
	if err := cli.ContainerStart(ctx, resp.ID, container.StartOptions{}); err != nil {
		return nil, fmt.Errorf("container start: %w", err)
	}

	// Wait with timeout
	statusCh, errCh := cli.ContainerWait(ctx, resp.ID, container.WaitConditionNotRunning)
	select {
	case <-errCh:
	case <-statusCh:
	case <-time.After(ExecTimeout):
		cli.ContainerKill(ctx, resp.ID, "SIGKILL")
	}

	// Capture logs
	out, err := cli.ContainerLogs(ctx, resp.ID, container.LogsOptions{ShowStdout: true, ShowStderr: true})
	if err != nil {
		return nil, fmt.Errorf("container logs: %w", err)
	}
	var stdoutBuf, stderrBuf bytes.Buffer
	if out != nil {
		defer out.Close()
		stdcopy.StdCopy(&stdoutBuf, &stderrBuf, out)
	}

	return &SandboxResult{
		Stdout: stdoutBuf.String(),
		Stderr: stderrBuf.String(),
	}, nil
}

// injectFile creates a tar archive with a single file and copies it into the container.
func injectFile(ctx context.Context, cli *client.Client, containerID, filename, content string) error {
	var buf bytes.Buffer
	tw := tar.NewWriter(&buf)
	if err := tw.WriteHeader(&tar.Header{Name: filename, Mode: 0644, Size: int64(len(content))}); err != nil {
		return fmt.Errorf("tar header: %w", err)
	}
	if _, err := tw.Write([]byte(content)); err != nil {
		return fmt.Errorf("tar write: %w", err)
	}
	if err := tw.Close(); err != nil {
		return fmt.Errorf("tar close: %w", err)
	}
	return cli.CopyToContainer(ctx, containerID, SandboxWorkDir, &buf, container.CopyToContainerOptions{})
}
