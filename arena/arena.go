package main

import (
	"archive/tar"
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"net/url"
	"regexp"
	"strings"
	"time"

	"github.com/docker/docker/api/types/container"
	"github.com/docker/docker/api/types/image"
	"github.com/docker/docker/client"
	"github.com/docker/docker/pkg/stdcopy"
)

type ExecutionRequest struct {
	Language       string `json:"language"`
	AppCode        string `json:"app_code"`
	ExploitPayload string `json:"exploit_payload"`
}

type ExecutionResult struct {
	Success bool   `json:"success"`
	Output  string `json:"output"`
	Error   string `json:"error"`
}

func executeInSandbox(w http.ResponseWriter, r *http.Request) {
	var req ExecutionRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}

	ctx := context.Background()
	cli, err := client.NewClientWithOpts(client.FromEnv, client.WithAPIVersionNegotiation())
	if err != nil {
		http.Error(w, "Failed to connect to Docker", http.StatusInternalServerError)
		return
	}

	// Pull the Python image if you don't have it locally
	cli.ImagePull(ctx, "python:3.10-slim", image.PullOptions{})

	// 1. Create the secure container
	resp, err := cli.ContainerCreate(ctx, &container.Config{
		Image:      "python:3.10-slim",
		WorkingDir: "/app",
		Cmd:        []string{"sh", "-c", "python app.py & sleep 1 && python exploit.py"},
		Tty:        false,
	}, &container.HostConfig{
		AutoRemove:  false,  // We handle removal manually via defer
		NetworkMode: "none", // No internet access
	}, nil, nil, "")

	if err != nil {
		http.Error(w, fmt.Sprintf("Failed to create sandbox: %v", err), http.StatusInternalServerError)
		return
	}
	defer cli.ContainerRemove(ctx, resp.ID, container.RemoveOptions{Force: true})

	// 2. Inject the code files into the container
	if err := injectFileToContainer(ctx, cli, resp.ID, "app.py", req.AppCode); err != nil {
		http.Error(w, fmt.Sprintf("Failed to inject app.py: %v", err), http.StatusInternalServerError)
		return
	}
	if err := injectFileToContainer(ctx, cli, resp.ID, "exploit.py", req.ExploitPayload); err != nil {
		http.Error(w, fmt.Sprintf("Failed to inject exploit.py: %v", err), http.StatusInternalServerError)
		return
	}

	// 3. Start the container
	if err := cli.ContainerStart(ctx, resp.ID, container.StartOptions{}); err != nil {
		http.Error(w, fmt.Sprintf("Failed to start sandbox: %v", err), http.StatusInternalServerError)
		return
	}

	// 4. Wait for execution (10 second timeout)
	statusCh, errCh := cli.ContainerWait(ctx, resp.ID, container.WaitConditionNotRunning)
	select {
	case <-errCh:
	case <-statusCh:
	case <-time.After(10 * time.Second):
		cli.ContainerKill(ctx, resp.ID, "SIGKILL")
	}

	// 5. Capture the output
	out, err := cli.ContainerLogs(ctx, resp.ID, container.LogsOptions{ShowStdout: true, ShowStderr: true})
	var stdoutBuf, stderrBuf bytes.Buffer
	if err != nil {
		http.Error(w, fmt.Sprintf("Failed to read container logs: %v", err), http.StatusInternalServerError)
		return
	}
	if out != nil {
		defer out.Close()
		stdcopy.StdCopy(&stdoutBuf, &stderrBuf, out)
	}

	result := ExecutionResult{
		Success: stderrBuf.Len() == 0,
		Output:  stdoutBuf.String(),
		Error:   stderrBuf.String(),
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(result)
}

func injectFileToContainer(ctx context.Context, cli *client.Client, containerID, filename, content string) error {
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
	if err := cli.CopyToContainer(ctx, containerID, "/app", &buf, container.CopyToContainerOptions{}); err != nil {
		return fmt.Errorf("copy to container: %w", err)
	}
	return nil
}

func main() {
	http.HandleFunc("/execute", executeInSandbox)
	http.HandleFunc("/search", searchWeb)
	fmt.Println("🛡️ SentinelAI Arena Engine running on http://localhost:8080 ...")
	log.Fatal(http.ListenAndServe(":8080", nil))
}

// ==========================================
// OSINT CAPABILITIES (Extracted from PentAGI)
// ==========================================

type SearchRequest struct {
	Query string `json:"query"`
}

type SearchResult struct {
	Title       string `json:"title"`
	URL         string `json:"url"`
	Description string `json:"description"`
}

func searchWeb(w http.ResponseWriter, r *http.Request) {
	var req SearchRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}

	results, err := performDuckDuckGoSearch(r.Context(), req.Query, 5)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(results)
}

func performDuckDuckGoSearch(ctx context.Context, query string, maxResults int) ([]SearchResult, error) {
	formData := url.Values{}
	formData.Set("q", query)
	formData.Set("b", "")
	formData.Set("df", "")

	req, err := http.NewRequestWithContext(ctx, "POST", "https://html.duckduckgo.com/html/", strings.NewReader(formData.Encode()))
	if err != nil {
		return nil, err
	}
	req.Header.Set("User-Agent", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
	req.Header.Set("Content-Type", "application/x-www-form-urlencoded")

	client := &http.Client{Timeout: 10 * time.Second}
	resp, err := client.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, err
	}

	return parseHTMLRegex(body, maxResults), nil
}

func parseHTMLRegex(body []byte, maxResults int) []SearchResult {
	htmlStr := string(body)
	if strings.Contains(htmlStr, "No results found") {
		return []SearchResult{}
	}

	results := make([]SearchResult, 0)
	resultPattern := regexp.MustCompile(`(?s)<div class="result results_links[^"]*">.*?<div class="clear"></div>\s*</div>\s*</div>`)
	resultBlocks := resultPattern.FindAllString(htmlStr, -1)

	titlePattern := regexp.MustCompile(`<a[^>]+class="result__a"[^>]+href="([^"]+)"[^>]*>([^<]+)</a>`)
	snippetPattern := regexp.MustCompile(`(?s)<a[^>]+class="result__snippet"[^>]+href="[^"]*">(.+?)</a>`)

	for _, block := range resultBlocks {
		if len(results) >= maxResults {
			break
		}
		titleMatches := titlePattern.FindStringSubmatch(block)
		if len(titleMatches) < 3 {
			continue
		}

		resultURL := titleMatches[1]
		title := cleanText(titleMatches[2])

		description := ""
		snippetMatches := snippetPattern.FindStringSubmatch(block)
		if len(snippetMatches) > 1 {
			description = cleanText(snippetMatches[1])
		}

		if title == "" || resultURL == "" {
			continue
		}

		results = append(results, SearchResult{
			Title:       title,
			URL:         resultURL,
			Description: description,
		})
	}
	return results
}

func cleanText(text string) string {
	re := regexp.MustCompile(`<[^>]*>`)
	text = re.ReplaceAllString(text, "")
	text = strings.ReplaceAll(text, "&amp;", "&")
	text = strings.ReplaceAll(text, "&lt;", "<")
	text = strings.ReplaceAll(text, "&gt;", ">")
	text = strings.ReplaceAll(text, "&quot;", "\"")
	text = strings.ReplaceAll(text, "&#39;", "'")
	
	text = strings.TrimSpace(text)
	text = regexp.MustCompile(`\s+`).ReplaceAllString(text, " ")
	return text
}