# =========================================
# AUTONOMOUS AI CODING AGENT (FAST + SMART)
# =========================================

import os
import sys
import io
from dotenv import load_dotenv
from langchain_ollama import ChatOllama

load_dotenv()

# =========================================
# LLM
# =========================================
llm = ChatOllama(
    model=os.getenv("MODEL_NAME", "qwen3:1.7b"),
    base_url=os.getenv("OLLAMA_HOST", "http://localhost:11434"),
    temperature=0,
)

# =========================================
# TOOLS
# =========================================
def read_file(filename):
    try:
        with open(filename, "r") as f:
            return f.read()
    except Exception as e:
        return f"ERROR: {str(e)}"


def write_file(filename, content):
    try:
        with open(filename, "w") as f:
            f.write(content)
        return f"Saved to {filename}"
    except Exception as e:
        return f"ERROR: {str(e)}"


def run_python(code):
    old_stdout = sys.stdout
    sys.stdout = buffer = io.StringIO()

    try:
        exec(code, {})
        return buffer.getvalue() or "No output"
    except Exception as e:
        return f"ERROR: {str(e)}"
    finally:
        sys.stdout = old_stdout


# =========================================
# STREAMING
# =========================================
def stream_llm(prompt):
    output = ""
    for chunk in llm.stream(prompt):
        if hasattr(chunk, "content") and chunk.content:
            print(chunk.content, end="", flush=True)
            output += chunk.content
    print("\n")
    return output


# =========================================
# BRAIN (DECIDES WHAT TO DO)
# =========================================
def decide_action(user_input):
    print("🧠 Planning...\n")

    prompt = f"""
You are an autonomous coding agent.

User request:
{user_input}

Decide next action.

Respond in STRICT JSON format:

{{
  "action": "write/run/read/respond",
  "filename": "optional",
  "content": "code or text",
  "reason": "short reason"
}}
"""

    response = ""
    for chunk in llm.stream(prompt):
        if hasattr(chunk, "content") and chunk.content:
            print(chunk.content, end="", flush=True)
            response += chunk.content

    print("\n")
    return response


# =========================================
# EXECUTOR
# =========================================
import json

def execute_action(action_json):
    try:
        data = json.loads(action_json)
    except:
        return "❌ Invalid JSON from model"

    action = data.get("action")
    filename = data.get("filename", "generated.py")
    content = data.get("content", "")

    print(f"⚙️ Action: {action}")
    print(f"📄 Reason: {data.get('reason')}\n")

    if action == "write":
        print("📝 Writing file...\n")
        return write_file(filename, content)

    elif action == "run":
        print("🐍 Running code...\n")
        return run_python(content)

    elif action == "read":
        print("📂 Reading file...\n")
        return read_file(filename)

    elif action == "respond":
        return content

    return "❌ Unknown action"


# =========================================
# MAIN LOOP (AUTONOMOUS)
# =========================================
def run():
    print("\n🔥 AUTONOMOUS AGENT STARTED\n")
    print("📍 Directory:", os.getcwd(), "\n")

    while True:
        user_input = input("YOU: ")

        if user_input.lower() == "exit":
            break

        # STEP 1: PLAN
        action_json = decide_action(user_input)

        # STEP 2: EXECUTE
        result = execute_action(action_json)

        print("\n🤖 RESULT:\n", result)

        # STEP 3: SELF-IMPROVE LOOP
        if "ERROR" in str(result):
            print("\n🧠 Fixing error...\n")

            fix_prompt = f"""
Fix this error:

{result}

Code:
{action_json}

Return corrected JSON only.
"""

            fixed = stream_llm(fix_prompt)
            result = execute_action(fixed)

            print("\n✅ FIXED RESULT:\n", result)

        print("\n" + "=" * 60 + "\n")


# =========================================
# ENTRY
# =========================================
if __name__ == "__main__":
    run()