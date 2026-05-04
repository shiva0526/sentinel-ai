package search

import (
	"context"
	"encoding/json"
	"io"
	"net/http"
	"net/url"
	"regexp"
	"strings"
	"time"

	"sentinel-arena/internal/models"
)

// Handle processes POST /search requests.
// It scrapes DuckDuckGo's HTML interface and returns structured results.
func Handle(w http.ResponseWriter, r *http.Request) {
	var req models.SearchRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}

	results, err := PerformSearch(r.Context(), req.Query, 5)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(results)
}

// PerformSearch queries DuckDuckGo's HTML endpoint and parses the results.
func PerformSearch(ctx context.Context, query string, maxResults int) ([]models.SearchResult, error) {
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

func parseHTMLRegex(body []byte, maxResults int) []models.SearchResult {
	htmlStr := string(body)
	if strings.Contains(htmlStr, "No results found") {
		return []models.SearchResult{}
	}

	results := make([]models.SearchResult, 0)
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

		results = append(results, models.SearchResult{
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
