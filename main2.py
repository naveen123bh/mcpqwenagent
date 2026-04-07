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
                for step in range(3):  # loop (important!)

                    print(f"\n🔄 Step {step+1} thinking...\n")

                    prompt = f"""
You are an AI agent.

Memory:
{memory}

User request:
{user_input}

Decide next action.
Use tools if needed.
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
                                print(f"\n⚙️ Calling Tool: {name}")

                                result = await session.call_tool(name, args)

                                print("\n📄 Tool Result:")
                                tool_output = ""

                                for item in result.content:
                                    if hasattr(item, "text"):
                                        print(item.text)
                                        tool_output += item.text

                                memory.append(f"Tool {name} result: {tool_output}")

                            except Exception as e:
                                print("\n❌ Tool failed, retrying...")
                                memory.append(f"Error: {str(e)}")

                    else:
                        # =========================
                        # FINAL RESPONSE (STREAM)
                        # =========================
                        print("\n🤖 Final Answer:\n")
                        stream_llm(llm, prompt)
                        break

                print("\n" + "=" * 60 + "\n")


# =========================
# ENTRY
# =========================
if __name__ == "__main__":
    asyncio.run(run())