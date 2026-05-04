import os
import re
import requests
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import TypedDict, Optional
from dotenv import load_dotenv
from google import genai
from google.genai import errors as genai_errors
from langgraph.graph import StateGraph, END

# Import the AST tool we just built!
from ast_tool import generate_ast_blueprint

# Import the new Phase 1 PentAGI translated agents
from recon_agents import recon_pentester_agent, recon_reflector_agent, recon_searcher_agent

# Import the new Hunter Agent
from hunter_agent import run_pentagi_hunter

# 0. Setup AI
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

# Create two separate brains with isolated rate-limit quotas!
client_blue = genai.Client(api_key=os.getenv("GEMINI_API_KEY_BLUE"))
client_red = genai.Client(api_key=os.getenv("GEMINI_API_KEY_RED"))

# Fallback model chain: try each in order if the previous is overloaded
FALLBACK_MODELS = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash"]

def generate_with_fallback(ai_client, prompt: str) -> str:
    """Try each model in FALLBACK_MODELS. On 503 ServerError, fall to the next."""
    for model_name in FALLBACK_MODELS:
        try:
            print(f"    ⚡ Trying {model_name}...")
            response = ai_client.models.generate_content(model=model_name, contents=prompt)
            return response.text.strip()
        except genai_errors.ServerError as e:
            print(f"    ⚠️  {model_name} unavailable (503), falling back...")
            continue
    raise RuntimeError("All Gemini models are currently unavailable. Please try again later.")

# 1. THE STATE & API MODELS
class HuntRequest(BaseModel):
    repo_url: str

class WarRoomState(TypedDict):
    repo_url: str                # <--- ADD THIS
    cve_id: Optional[str]
    vulnerable_file: Optional[str]
    original_code: Optional[str]
    ast_graph: Optional[str]
    proposed_patch: Optional[str]
    exploit_payload: Optional[str]
    test_logs: Optional[str]
    test_status: Optional[str]
    iterations: int

# 2. THE NODES (Agents)
def triage_agent(state: WarRoomState):
    print("\n🕵️  [1] Triage Agent: Fetching the vulnerable code...")
    # A classic SQL Injection vulnerability
    vuln_code = """
def login(username, password):
    db_query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"
    return execute_query(db_query)
"""
    return {"original_code": vuln_code.strip()}

def ast_agent(state: WarRoomState):
    print("🗺️  [2] AST Agent: Mapping code blueprint...")
    # Actually use our tool now!
    blueprint = generate_ast_blueprint(state["original_code"])
    return {"ast_graph": blueprint}

def mechanic_agent(state: WarRoomState):
    print("🔧 [3] Mechanic (Blue Team): AI is writing a secure patch...")
    
    # Check if we are on a retry because the Sandbox failed
    feedback = ""
    if state.get("test_status") == "FAIL":
        feedback = f"\nWARNING: Your previous patch FAILED the Sandbox test. Crash logs:\n{state['test_logs']}\nFix the error!"

    prompt = f"""
    You are an expert DevSecOps Engineer. Your job is to patch vulnerable Python code.
    Use the provided Abstract Syntax Tree (AST) to understand the structure.
    
    Vulnerable Code:
    ```python
    {state['original_code']}
    ```
    
    AST Blueprint:
    {state['ast_graph']}
    {feedback}
    
    Rewrite the code to be secure (e.g., prevent SQL injection, sanitize inputs).
    ONLY output the raw, patched Python code. Do not include markdown formatting like ```python. 
    Do not explain your code. Just return the code.
    """
    
    # Ask Gemini to fix it (Blue Team's client)!
    patched_code = generate_with_fallback(client_blue, prompt)
    
    # Clean up markdown if Gemini accidentally includes it
    patched_code = re.sub(r"^```python\n|```$", "", patched_code, flags=re.MULTILINE).strip()
    
    print("\n--- AI PATCH GENERATED ---")
    print(patched_code)
    print("--------------------------\n")
    
    return {"proposed_patch": patched_code}

def hacker_agent(state: WarRoomState):
    print("🥷  [4] Hacker (Red Team): AI is reverse-engineering the patch to write an exploit...")

    prompt = f"""
    You are an expert Red Team Security Researcher. 
    Your goal is to write a Python exploit payload to test if a recent security patch is truly effective.
    
    Original Vulnerable Code:
    ```python
    {state['original_code']}
    ```
    
    Patched Code (Blue Team):
    ```python
    {state['proposed_patch']}
    ```
    
    Write a Python script that attempts to attack the patched code. 
    Assume the patched function `login(username, password)` is available in your environment.
    
    Write a script that calls `login()` using a classic SQL Injection payload (e.g., "' OR 1=1 --").
    If your payload successfully tricks the login function into returning data, print "BOOM! EXPLOIT SUCCESSFUL."
    
    ONLY output raw Python code. Do not include markdown formatting like ```python. 
    Do not explain your code. Just return the executable code.
    """
    
    # Ask Gemini to hack it (Red Team's client)!
    exploit_payload = generate_with_fallback(client_red, prompt)
    
    # Clean up markdown if Gemini accidentally includes it
    exploit_payload = re.sub(r"^```python\n|```$", "", exploit_payload, flags=re.MULTILINE).strip()
    
    print("\n--- AI EXPLOIT PAYLOAD GENERATED ---")
    print(exploit_payload)
    print("------------------------------------\n")
    
    return {"exploit_payload": exploit_payload}

def validator_agent(state: WarRoomState):
    print("⚖️  [5] Referee: Sending the Patch and Exploit to the Go Arena...")
    iters = state.get("iterations", 0) + 1

    try:
        # Fire the code over to your Go/Docker Sandbox
        response = requests.post("http://localhost:8080/execute", json={
            "language": "python",
            "app_code": state['proposed_patch'],
            "exploit_payload": state['exploit_payload']
        })
        
        # Check if the Go server itself crashed
        if response.status_code != 200:
            print(f"   ⚠️ Sandbox Error ({response.status_code}): {response.text}")
            return {"test_status": "FAIL", "iterations": iters, "test_logs": f"Sandbox Error: {response.text}"}
            
        result = response.json()
        
        # Did the exploit crash the patched app?
        if result["success"]:
            print("   ✅ Referee: The patch held! The Hacker failed to exploit it.")
            return {"test_status": "PASS", "iterations": iters, "test_logs": "Execution successful. No crash detected."}
        else:
            print("   ❌ Referee: The Hacker broke the patch! Sending the crash logs back to the Blue Team.")
            return {"test_status": "FAIL", "iterations": iters, "test_logs": result["error"]}
            
    except Exception as e:
        print(f"   ⚠️ Failed to connect to Go Sandbox. Is it running? Error: {e}")
        return {"test_status": "FAIL", "iterations": iters, "test_logs": str(e)}

# 3. CONDITIONAL ROUTING
def check_sandbox_results(state: WarRoomState):
    if state["test_status"] == "PASS":
        return "end"
    else:
        return "retry"

# Create a wrapper so it matches the LangGraph node signature
def hunter_node(state: WarRoomState):
    # Pass the blue team client to the hunter
    return run_pentagi_hunter(state, client_blue)

# 4. BUILD THE GRAPH
workflow = StateGraph(WarRoomState)

workflow.add_node("Hunter", hunter_node)            # <--- NEW ENTRY NODE
workflow.add_node("Triage", triage_agent)
workflow.add_node("AST_Analyzer", ast_agent)
workflow.add_node("Mechanic", mechanic_agent)
workflow.add_node("Hacker", hacker_agent)
workflow.add_node("Validator", validator_agent)

workflow.set_entry_point("Hunter")                  # <--- START AT THE HUNT
workflow.add_edge("Hunter", "Triage")               # Hunt -> Triage
workflow.add_edge("Triage", "AST_Analyzer")
workflow.add_edge("AST_Analyzer", "Mechanic")
workflow.add_edge("Mechanic", "Hacker")
workflow.add_edge("Hacker", "Validator")

workflow.add_conditional_edges("Validator", check_sandbox_results, {"end": END, "retry": "Mechanic"})

app = workflow.compile()

# 5. FASTAPI MICROSERVICE EXPORT
fastapi_app = FastAPI(title="SentinelAI Defensive Pipeline")

fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins (like our React frontend)
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, OPTIONS, etc.)
    allow_headers=["*"],  # Allows all headers
)

@fastapi_app.post("/hunt")
def trigger_full_pipeline(request: HuntRequest):
    print(f"🚀 SentinelAI initialized targeting: {request.repo_url}...")
    
    initial_state = {
        "repo_url": request.repo_url,
        "iterations": 0
    }
    
    try:
        final_state = app.invoke(initial_state)
        return {
            "status": "success",
            "vulnerability_found": final_state.get("cve_id"),
            "secure_patch": final_state.get("proposed_patch"),
            "test_status": final_state.get("test_status")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline failed: {str(e)}")

if __name__ == "__main__":
    print("🚀 Starting SentinelAI Pipeline...\n")
    # For testing, we can run uvicorn locally
    print("🛡️ Starting SentinelAI Microservice on port 8000...")
    uvicorn.run(fastapi_app, host="0.0.0.0", port=8000)