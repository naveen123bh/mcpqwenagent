import asyncio
import time
from langchain_ollama import ChatOllama

from mcp.client.stdio import stdio_client, StdioServerParameters
from mcp import ClientSession


# =========================
# STREAM REAL TOKENS
# =========================
def stream_llm(llm, prompt):
    for chunk in llm.stream(prompt):
        if hasattr(chunk, "content") and chunk.content:
            print(chunk.content, end="", flush=True)
    print()


# =========================
# SIMPLE MEMORY
# =========================
memory = []


# =========================
# PERMISSION SYSTEM 🔒
# =========================
def ask_permission(tool_name, args):
    print("\n⚠️ Permission required!")
    print(f"Tool: {tool_name}")
    print(f"Arguments: {args}")
    
    choice = input("Allow? (y/n): ").strip().lower()
    return choice == "y"


# =========================
# LLM
# =========================
llm = ChatOllama(
    model="qwen3:1.7b",
    temperature=0
)


# =========================
# PLANNER
# =========================
def create_plan(user_input):
    prompt = f"""
You are an AI planner.

Break the task into steps.

User task: {user_input}

Return steps like:
1. ...
2. ...
"""
    print("\n🧠 Planning...")
    stream_llm(llm, prompt)


# =========================
# MAIN LOOP
# =========================
async def run():

    print("\n🔥 REAL MCP AUTO-AGENT STARTED\n")

    server = StdioServerParameters(
        command="python",
        args=["mcp_server.py"]
    )

    async with stdio_client(server) as (read, write):
        async with ClientSession(read, write) as session:

            await session.initialize()

            while True:
                user_input = input("YOU: ")
                if user_input.lower() == "exit":
                    break

                memory.append(f"User: {user_input}")

                # =========================
                # STEP 1: PLAN
                # =========================
                create_plan(user_input)

                # =========================
                # STEP 2: GET TOOLS
                # =========================
                tools = await session.list_tools()

                tool_list = [
                    {
                        "type": "function",
                        "function": {
                            "name": t.name,
                            "description": t.description,
                            "parameters": t.inputSchema
                        }
                    }
                    for t in tools.tools
                ]

                # =========================
                # STEP 3: EXECUTION LOOP
                # =========================
                for step in range(5):  # increased steps + safety

                    print(f"\n🔄 Step {step+1} thinking...\n")

                    prompt = f"""
You are an AI agent with controlled filesystem access.

Rules:
- Use tools when needed
- Always think step-by-step
- File operations require user permission (handled externally)

Memory:
{memory}

User request:
{user_input}

Decide next action.
"""

                    response = llm.invoke(prompt, tools=tool_list)

                    # =========================
                    # TOOL CALL
                    # =========================
                    if hasattr(response, "tool_calls") and response.tool_calls:

                        for call in response.tool_calls:

                            name = call.get("name") or call.get("function", {}).get("name")
                            args = call.get("args") or call.get("function", {}).get("arguments", {})

                            try:
                                print(f"\n⚙️ Tool requested: {name}")

                                # 🔒 ASK PERMISSION FIRST
                                allowed = ask_permission(name, args)

                                if not allowed:
                                    print("❌ Permission denied by user")
                                    memory.append(f"User denied tool: {name}")
                                    continue

                                # ✅ EXECUTE TOOL
                                result = await session.call_tool(name, args)

                                print("\n📄 Tool Result:")
                                tool_output = ""

                                for item in result.content:
                                    if hasattr(item, "text"):
                                        print(item.text)
                                        tool_output += item.text

                                # 🔁 STORE RESULT IN MEMORY
                                memory.append(f"Tool {name} result: {tool_output}")

                            except Exception as e:
                                print("\n❌ Tool failed")
                                memory.append(f"Error: {str(e)}")

                    else:
                        # =========================
                        # FINAL RESPONSE (USES MEMORY NOW ✅)
                        # =========================
                        print("\n🤖 Final Answer:\n")

                        final_prompt = f"""
You are an AI assistant.

Conversation memory:
{memory}

User request:
{user_input}

Give final helpful answer.
"""

                        stream_llm(llm, final_prompt)
                        break

                print("\n" + "=" * 60 + "\n")


# =========================
# ENTRY
# =========================
if __name__ == "__main__":
    asyncio.run(run())