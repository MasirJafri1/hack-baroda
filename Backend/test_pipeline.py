import os
import json
from dotenv import load_dotenv
from graph import app

# Load environment variables
load_dotenv()

# Define Synthetic Git Diffs
SAFE_DIFF = """diff --git a/tests/test_calculator.py b/tests/test_calculator.py
index 451bf32..e49a888 100644
--- a/tests/test_calculator.py
+++ b/tests/test_calculator.py
@@ -1,6 +1,9 @@
 from app.calculator import add
 
 def test_add_integers():
     assert add(1, 2) == 3
+
+def test_add_negatives():
+    assert add(-1, -1) == -2
"""

RISKY_INFRA_DIFF = """diff --git a/infra/security.tf b/infra/security.tf
index a9f8e43..b8e7c12 100644
--- a/infra/security.tf
+++ b/infra/security.tf
@@ -10,8 +10,8 @@ resource "aws_security_group" "web_server_sg" {
   ingress {
     description      = "SSH from administration network"
     from_port        = 22
     to_port          = 22
     protocol         = "tcp"
-    cidr_blocks      = ["10.0.0.0/8"]
+    cidr_blocks      = ["0.0.0.0/0"]
   }
 }
"""

RISKY_CODE_DIFF = """diff --git a/app/websocket_handler.py b/app/websocket_handler.py
index 92c81da..a83b2ef 100644
--- a/app/websocket_handler.py
+++ b/app/websocket_handler.py
@@ -12,11 +12,12 @@ class ConnectionManager:
 
-    async def connect(self, websocket: WebSocket):
-        await websocket.accept()
-        self.active_connections.append(websocket)
-
-    async def disconnect(self, websocket: WebSocket):
-        self.active_connections.remove(websocket)
+    async def handle_connection(self, websocket: WebSocket):
+        # WebSocket handler refactoring
+        await websocket.accept()
+        self.active_connections.append(websocket)
+        while True:
+            data = await websocket.receive_text()
+            # Process incoming message without try-except block
+            await self.send_personal_message(f"Message received: {data}", websocket)
"""

def print_banner(title: str):
    print("\n" + "=" * 80)
    print(f" {title.center(78)} ")
    print("=" * 80)

def run_scenario(name: str, git_diff: str):
    print_banner(f"RUNNING SCENARIO: {name}")
    
    # Verify API key
    if not os.getenv("GROQ_API_KEY"):
        print("[WARNING] GROQ_API_KEY is not set in the environment. The LLM nodes will fail.")
        print("Please configure your .env file or export GROQ_API_KEY in the environment first.")
        return

    # Initialize input state
    inputs = {
        "git_diff": git_diff,
        "metadata": {
            "author": "masir.jafri",
            "timestamp": "2026-06-07T14:00:00Z"
        },
        "hindsight_session_id": "",
        "risk_flag": False,
        "risk_reason": "",
        "retrieval_queries": [],
        "retrieved_logs": [],
        "agent_analyses": {},
        "loop_count": 0,
        "final_audit": ""
    }

    # Run LangGraph pipeline
    try:
        final_state = app.invoke(inputs)
        
        print("\n" + "-" * 50)
        print(" PIPELINE EXECUTION SUMMARY ".center(50, "-"))
        print("-" * 50)
        print(f"Hindsight Session ID : {final_state.get('hindsight_session_id')}")
        print(f"Risk Flagged by V1   : {final_state.get('risk_flag')}")
        print(f"Total loop passes    : {final_state.get('loop_count')}")
        print("-" * 50)
        
        print("\n--- FINAL AUDIT REPORT ---")
        print(final_state.get("final_audit", "No audit report compiled."))
        print("-" * 80 + "\n")
        
    except Exception as e:
        print(f"\n[ERROR] Pipeline run encountered an exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print_banner("Hindsight DevOps Pipeline Agent Testing Suite")
    print(f"Workspace Path: {os.getcwd()}")
    print("This suite executes multiple synthetic code-change test cases through the LangGraph pipeline.")
    
    # Ask which scenario to run, or run all of them
    print("\nAvailable Scenarios:")
    print("1. Run Scenario 1: Clean Code Change (Expect fast bypass)")
    print("2. Run Scenario 2: Unsafe Infra Code Change (Expect Security Block)")
    print("3. Run Scenario 3: Unsafe WebSocket Code Change (Expect Logic Block + Reflection)")
    print("4. Run All Scenarios sequentially")
    
    choice = input("\nEnter scenario number [1-4]: ").strip()
    
    if choice == "1":
        run_scenario("Clean Code Change", SAFE_DIFF)
    elif choice == "2":
        run_scenario("Unsafe Infra Code Change", RISKY_INFRA_DIFF)
    elif choice == "3":
        run_scenario("Unsafe WebSocket Code Change", RISKY_CODE_DIFF)
    elif choice == "4" or choice == "":
        run_scenario("Clean Code Change", SAFE_DIFF)
        run_scenario("Unsafe Infra Code Change", RISKY_INFRA_DIFF)
        run_scenario("Unsafe WebSocket Code Change", RISKY_CODE_DIFF)
    else:
        print("Invalid option selected. Exiting.")
