# 🛡️ SentinelAI — Autonomous Purple Team Security Platform

SentinelAI is a **multi-agent, AI-powered security pipeline** that autonomously detects, patches, exploits, and validates vulnerabilities in Python source code.

## Architecture

```
Frontend (React)  →  Orchestrator (Python/LangGraph)  →  Sentinel Core (Detection Engine)
                                                      →  LLM (Gemini — Validation + Patching)
                                                      →  Arena (Go — Docker Sandbox)
```

## Project Structure

```
sentinel-ai/
├── arena/                           # 🏟️ Execution Sandbox (Go)
│   ├── cmd/server.go                # Entry point
│   └── internal/
│       ├── docker/docker.go         # Container execution logic
│       ├── executor/executor.go     # /execute handler
│       ├── search/search.go         # /search (DuckDuckGo OSINT)
│       └── models/models.go         # Request/Response structs
│
├── orchestrator/                    # 🧠 AI Pipeline (LangGraph + FastAPI)
│   ├── app/
│   │   ├── main.py                  # FastAPI entrypoint
│   │   ├── graph/                   # LangGraph workflow
│   │   │   ├── state.py             # WarRoomState definition
│   │   │   ├── builder.py           # Graph construction
│   │   │   └── edges.py             # Conditional routing
│   │   ├── agents/                  # All AI agents
│   │   │   ├── hunter.py            # 🔍 Rule engine + LLM fallback
│   │   │   ├── triage.py            # 📋 AST preprocessing
│   │   │   ├── mechanic.py          # 🔧 Blue Team patch generator
│   │   │   ├── hacker.py            # 💀 Red Team exploit writer
│   │   │   └── validator.py         # 🧪 Arena sandbox test
│   │   ├── services/                # Service layer
│   │   │   ├── llm_service.py       # Gemini wrapper + fallback
│   │   │   ├── arena_client.py      # Go sandbox HTTP client
│   │   │   └── detector_client.py   # Sentinel Core wrapper
│   │   └── core/
│   │       ├── config.py            # Environment handling
│   │       └── constants.py
│   ├── tests/
│   └── requirements.txt
│
├── sentinel_core/                   # 🔬 Rule-Based Detection Engine
│   ├── detector/
│   │   ├── ast_parser.py            # AST node extraction
│   │   ├── flow_tracker.py          # Taint-style data flow tracking
│   │   ├── rules.py                 # 6 security rules (SQLi, XSS, etc.)
│   │   ├── analyzer.py              # Pipeline orchestrator
│   │   └── models.py                # Data models
│   ├── interfaces/
│   │   └── detector_service.py      # Clean public API
│   ├── utils/
│   │   ├── patterns.py              # Pattern constants
│   │   └── helpers.py               # Utility functions
│   └── tests/
│       └── test_detector.py         # Unit tests
│
├── frontend/                        # 🖥️ React War Room Dashboard
│   └── src/
│       ├── pages/dashboard.tsx      # Main dashboard
│       ├── services/api.ts          # API client
│       ├── components/              # UI components
│       └── hooks/                   # React hooks
│
├── shared/                          # 🔁 Cross-service contracts
│   ├── schemas/
│   │   ├── vulnerability.py         # Vulnerability data models
│   │   ├── execution.py             # Sandbox request/response
│   │   └── api_models.py            # REST API models
│   └── constants.py
│
├── infra/                           # ⚙️ DevOps / Docker
│   ├── docker-compose.yml
│   ├── orchestrator.Dockerfile
│   ├── arena.Dockerfile
│   └── env/.env.example
│
└── scripts/                         # 🧪 Utility scripts
    ├── run_all.sh
    ├── test_arena.py
    └── seed_examples.py
```

## Quick Start

### 1. Set up environment
```bash
cp infra/env/.env.example orchestrator/.env
# Fill in your Gemini API keys
```

### 2. Start services

**Option A: Docker Compose**
```bash
cd infra
docker-compose up --build
```

**Option B: Manual**
```bash
# Terminal 1 — Arena (Go sandbox)
cd arena && go run cmd/server.go

# Terminal 2 — Orchestrator (Python)
cd orchestrator && pip install -r requirements.txt && python -m app.main

# Terminal 3 — Frontend (React)
cd frontend && npm install && npm run dev
```

### 3. Use it
Open `http://localhost:5173` and paste a GitHub raw file URL.

## Detection Rules

| Rule | CWE | Detects |
|------|-----|---------|
| SQL Injection | CWE-89 | Input → SQL string → execute() |
| Command Injection | CWE-78 | Input → os.system(), subprocess.* |
| Code Injection | CWE-94 | Input → eval(), exec() |
| XSS | CWE-79 | Input → render_template_string() |
| Hardcoded Secrets | CWE-798 | Passwords, API keys, tokens |
| Insecure Deserialization | CWE-502 | Input → pickle.loads(), yaml.load() |

## Pipeline Flow

```
[Hunter] → Rule-Based Detection → LLM Validation
    ↓
[Triage] → AST Blueprint
    ↓
[Mechanic] → Blue Team generates secure patch
    ↓
[Hacker] → Red Team writes exploit
    ↓
[Validator] → Sandbox execution test
    ↓
PASS → Deploy  |  FAIL → Retry Mechanic
```

## Testing

```bash
# Test detection engine
python sentinel_core/tests/test_detector.py

# Test arena connectivity
python scripts/test_arena.py

# Test orchestrator
python orchestrator/tests/test_pipeline.py
```
