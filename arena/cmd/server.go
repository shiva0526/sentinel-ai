package main

import (
	"fmt"
	"log"
	"net/http"

	"sentinel-arena/internal/executor"
	"sentinel-arena/internal/search"
)

func main() {
	http.HandleFunc("/execute", executor.Handle)
	http.HandleFunc("/search", search.Handle)

	fmt.Println("🛡️ SentinelAI Arena Engine running on http://localhost:8080 ...")
	log.Fatal(http.ListenAndServe(":8080", nil))
}
