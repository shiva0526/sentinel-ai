import requests

def test_sandbox():
    print("🤖 Validator Agent: Sending code to the Arena...")

    # Fake patched code from the Blue Team
    patched_code = """
import time
print('App is running securely on port 3000!')
time.sleep(3)
"""

    # Fake exploit payload from the Red Team (intentionally causing an error)
    exploit_payload = """
print('Attacking the app...')
raise Exception('BOOM! The Exploit crashed the app!')
"""

    # Send it to the Go server
    try:
        response = requests.post("http://localhost:8080/execute", json={
            "language": "python",
            "app_code": patched_code,
            "exploit_payload": exploit_payload
        })
        
        if response.status_code != 200:
            print(f"⚠️ Server returned HTTP {response.status_code}:")
            print(response.text)
            return

        result = response.json()
        
        if result["success"]:
            print("✅ TEST PASSED: The app survived the exploit.")
            print("Output:\n", result["output"])
        else:
            print("❌ TEST FAILED: The exploit broke the app!")
            print("Crash Logs to send back to Blue Team:\n", result["error"])
            
    except Exception as e:
        print("Failed to connect to the Go Arena. Is it running?", e)

if __name__ == "__main__":
    test_sandbox()