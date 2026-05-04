package models

// ExecutionRequest is sent by the Orchestrator to run code in the sandbox.
type ExecutionRequest struct {
	Language     string `json:"language"`
	CombinedCode string `json:"combined_code"`
}

// ExecutionResult is returned after sandbox execution completes.
type ExecutionResult struct {
	Success bool   `json:"success"`
	Output  string `json:"output"`
	Error   string `json:"error"`
	Reason  string `json:"reason"`
}

// SearchRequest is sent to trigger a DuckDuckGo OSINT search.
type SearchRequest struct {
	Query string `json:"query"`
}

// SearchResult represents a single web search result.
type SearchResult struct {
	Title       string `json:"title"`
	URL         string `json:"url"`
	Description string `json:"description"`
}
