package executor

import (
	"context"
	"encoding/json"
	"net/http"
	"strings"

	"sentinel-arena/internal/docker"
	"sentinel-arena/internal/models"
)

// Handle processes POST /execute requests.
// It injects app_code and exploit_payload into a Docker sandbox and returns the result.
func Handle(w http.ResponseWriter, r *http.Request) {
	var req models.ExecutionRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}

	files := map[string]string{
		"combined.py": req.CombinedCode,
	}
	cmd := "python combined.py"

	result, err := docker.RunInSandbox(context.Background(), files, cmd)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	stdout := result.Stdout
	stderr := result.Stderr

	var success bool
	var reason string

	if strings.Contains(stdout, "EXPLOIT_SUCCESS") {
		success = false
		reason = "EXPLOIT_SUCCESS"
	} else if strings.Contains(stdout, "EXPLOIT_FAILED") {
		success = true
		reason = "EXPLOIT_FAILED"
	} else if len(stderr) > 0 {
		success = false
		reason = "RUNTIME_ERROR"
	} else {
		success = false
		reason = "UNKNOWN"
	}

	resp := models.ExecutionResult{
		Success: success,
		Output:  stdout,
		Error:   stderr,
		Reason:  reason,
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(resp)
}
