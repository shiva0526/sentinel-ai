import sys
from app.graph.builder import build_pipeline

from langgraph.checkpoint.memory import MemorySaver

def main():
    if len(sys.argv) < 2:
        print("Usage: python run_pipeline.py <repo_url>")
        return
    
    repo_url = sys.argv[1]
    checkpointer = MemorySaver()
    pipeline = build_pipeline(checkpointer=checkpointer)
    
    config = {"configurable": {"thread_id": "1"}}
    
    print(f"Running pipeline for {repo_url}...")
    
    # Run until interrupt (after Review)
    pipeline.invoke({
        "repo_url": repo_url,
        "iterations": 0
    }, config=config)
    
    # Get current state
    snapshot = pipeline.get_state(config)
    state = snapshot.values
    
    if state.get("test_status") == "PASS":
        print("\n" + "="*50)
        print("🛡️ SENTINEL AI: VULNERABILITY FOUND AND VALIDATED")
        print(f"Vulnerability: {state.get('cve_id')}")
        print(f"File: {state.get('vulnerable_file')}")
        print("\n--- Proposed Patch ---")
        print(state.get('proposed_patch'))
        print("----------------------")
        
        # Ask for approval
        ans = input("\n[?] Do you want to push this patched code to GitHub? (y/n): ").lower()
        
        if ans == 'y':
            print("🚀 Approval granted. Pushing to GitHub...")
            # Update state with approval
            pipeline.update_state(config, {"deployment_approved": True})
            # Resume graph
            pipeline.invoke(None, config=config) # This resumes the graph and triggers check_approval -> Deployer
            print("✅ Deployment complete.")
        else:
            print("🛑 Deployment cancelled by user.")
    else:
        print("\n" + "="*50)
        print("Pipeline finished without finding a validated fix.")
        print(f"Test Status: {state.get('test_status')}")


if __name__ == "__main__":
    main()
