import asyncio
import json

from langchain_ollama import ChatOllama

from mcp.client.stdio import stdio_client, StdioServerParameters
from mcp import ClientSession


# ============================================================
# CONFIG
# ============================================================

MODEL_NAME = "qwen3:1.7b"

# Maximum number of tool rounds for one user request.
# Keep this LOW because your LLM is relatively slow.
MAX_TOOL_ROUNDS = 2

# Keep only recent conversation memory.
# This prevents the prompt from becoming huge.
MAX_MEMORY_ITEMS = 6


# ============================================================
# LLM
# ============================================================

llm = ChatOllama(
    model=MODEL_NAME,
    temperature=0
)


# ============================================================
# SIMPLE BOUNDED MEMORY
# ============================================================

memory = []


def add_memory(text):
    """
    Store only a small amount of recent memory.

    Why?
    Large memory = larger prompt = slower Qwen.
    """

    memory.append(text)

    if len(memory) > MAX_MEMORY_ITEMS:
        del memory[:-MAX_MEMORY_ITEMS]


# ============================================================
# STREAM FINAL RESPONSE
# ============================================================

def stream_llm(llm, prompt):

    for chunk in llm.stream(prompt):

        if hasattr(chunk, "content") and chunk.content:
            print(chunk.content, end="", flush=True)

    print()


# ============================================================
# MCP TOOL FORMAT
# ============================================================

def convert_mcp_tools(mcp_tools):

    return [
        {
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description or "",
                "parameters": tool.inputSchema
            }
        }
        for tool in mcp_tools
    ]


# ============================================================
# EXTRACT TOOL CALL
# ============================================================

def extract_tool_calls(response):

    calls = getattr(response, "tool_calls", None)

    if calls:
        return calls

    return []


# ============================================================
# EXTRACT TOOL NAME + ARGUMENTS
# ============================================================

def extract_call_data(call):

    # LangChain style
    name = call.get("name")

    args = call.get("args")

    # Some versions may return nested function format.
    if not name:

        function_data = call.get("function", {})

        name = function_data.get("name")

        args = function_data.get("arguments", {})

    # Sometimes arguments can be JSON string.
    if isinstance(args, str):

        try:
            args = json.loads(args)

        except json.JSONDecodeError:

            args = {}

    if args is None:
        args = {}

    return name, args


# ============================================================
# EXTRACT MCP RESULT
# ============================================================

def extract_tool_output(result):

    output_parts = []

    for item in result.content:

        if hasattr(item, "text") and item.text:

            output_parts.append(item.text)

    return "\n".join(output_parts)


# ============================================================
# BUILD SMALL MEMORY
# ============================================================

def get_memory_text():

    if not memory:
        return "No previous context."

    return "\n".join(memory)


# ============================================================
# BUILD AGENT PROMPT
# ============================================================

def build_agent_prompt(user_input):

    return f"""
You are a small local AI agent.

IMPORTANT RULES:

1. Use tools only when they are actually needed.
2. Do NOT perform heavy calculations yourself.
3. Let Python tools do heavy work.
4. Do NOT explain your internal reasoning.
5. If a tool result is available, use it.
6. If the task is already complete, give the final answer.
7. Keep your response concise.

Recent context:
{get_memory_text()}

Current user request:
{user_input}
"""


# ============================================================
# MAIN AGENT
# ============================================================

async def run():

    print("\n🔥 FAST MCP LOCAL AGENT STARTED")
    print(f"🤖 Model: {MODEL_NAME}")
    print("💡 LLM handles decisions, Python handles heavy work.\n")

    # ========================================================
    # MCP SERVER
    # ========================================================

    server = StdioServerParameters(
        command="python",
        args=["mcp_server.py"]
    )

    async with stdio_client(server) as (read, write):

        async with ClientSession(read, write) as session:

            # =================================================
            # INITIALIZE MCP
            # =================================================

            await session.initialize()

            # =================================================
            # GET TOOLS ONLY ONCE
            # =================================================

            mcp_response = await session.list_tools()

            tool_list = convert_mcp_tools(
                mcp_response.tools
            )

            print(
                f"🛠️ MCP tools loaded: {len(tool_list)}"
            )

            # =================================================
            # USER LOOP
            # =================================================

            while True:

                try:

                    user_input = input("\nYOU: ").strip()

                except (KeyboardInterrupt, EOFError):

                    print("\n\n👋 Exiting...")
                    break

                # =================================================
                # EXIT
                # =================================================

                if user_input.lower() in {
                    "exit",
                    "quit"
                }:

                    print("\n👋 Goodbye!")
                    break

                if not user_input:
                    continue

                # =================================================
                # STORE USER REQUEST
                # =================================================

                add_memory(
                    f"User: {user_input}"
                )

                # =================================================
                # AGENT LOOP
                # =================================================

                tool_round = 0

                while tool_round < MAX_TOOL_ROUNDS:

                    prompt = build_agent_prompt(
                        user_input
                    )

                    print(
                        "\n🧠 Deciding...",
                        end="",
                        flush=True
                    )

                    # =================================================
                    # LLM DECISION
                    # =================================================

                    response = llm.invoke(
                        prompt,
                        tools=tool_list
                    )

                    tool_calls = extract_tool_calls(
                        response
                    )

                    # =================================================
                    # NO TOOL REQUIRED
                    # =================================================

                    if not tool_calls:

                        print(
                            "\n\n🤖 Answer:\n"
                        )

                        # We already have the answer from invoke().
                        # Stream only a final response when necessary.
                        #
                        # To avoid another LLM call, directly print
                        # the response generated above.

                        if hasattr(
                            response,
                            "content"
                        ):

                            print(
                                response.content
                            )

                        else:

                            print(
                                str(response)
                            )

                        break

                    # =================================================
                    # TOOL REQUIRED
                    # =================================================

                    tool_round += 1

                    print(
                        f"\n\n⚙️ Tool round "
                        f"{tool_round}/{MAX_TOOL_ROUNDS}"
                    )

                    tool_results = []

                    # =================================================
                    # EXECUTE TOOL CALLS
                    # =================================================

                    for call in tool_calls:

                        name, args = extract_call_data(
                            call
                        )

                        if not name:

                            print(
                                "❌ Invalid tool call."
                            )

                            continue

                        print(
                            f"🔧 Tool: {name}"
                        )

                        try:

                            result = await session.call_tool(
                                name,
                                args
                            )

                            tool_output = extract_tool_output(
                                result
                            )

                            # -----------------------------------------
                            # PRINT RESULT
                            # -----------------------------------------

                            print(
                                "\n📄 Tool result:"
                            )

                            print(
                                tool_output
                            )

                            # -----------------------------------------
                            # Keep result in memory
                            # -----------------------------------------

                            add_memory(
                                f"Tool {name} result: "
                                f"{tool_output}"
                            )

                            tool_results.append(
                                f"""
Tool: {name}

Result:
{tool_output}
"""
                            )

                        except Exception as e:

                            error_message = str(e)

                            print(
                                f"\n❌ Tool failed: "
                                f"{error_message}"
                            )

                            add_memory(
                                f"Tool {name} failed: "
                                f"{error_message}"
                            )

                            tool_results.append(
                                f"""
Tool: {name}

ERROR:
{error_message}
"""
                            )

                    # =================================================
                    # GIVE TOOL RESULT BACK TO LLM
                    # =================================================

                    result_text = "\n".join(
                        tool_results
                    )

                    add_memory(
                        f"Latest tool results:\n"
                        f"{result_text}"
                    )

                    # =================================================
                    # ASK LLM TO FINISH OR CONTINUE
                    # =================================================

                    followup_prompt = f"""
You are a small local AI agent.

The Python/MCP tool has finished its work.

User request:
{user_input}

Tool result:
{result_text}

Recent context:
{get_memory_text()}

Rules:

1. Trust the tool result when it contains the required data.
2. Do not redo the heavy work yourself.
3. If the task is complete, give a concise final answer.
4. If another tool is absolutely necessary, use it.
5. Do not explain your internal reasoning.
"""

                    print(
                        "\n🧠 Processing result..."
                    )

                    final_response = llm.invoke(
                        followup_prompt,
                        tools=tool_list
                    )

                    next_tool_calls = extract_tool_calls(
                        final_response
                    )

                    # =================================================
                    # FINAL ANSWER
                    # =================================================

                    if not next_tool_calls:

                        print(
                            "\n🤖 Final Answer:\n"
                        )

                        if hasattr(
                            final_response,
                            "content"
                        ):

                            print(
                                final_response.content
                            )

                        else:

                            print(
                                str(final_response)
                            )

                        break

                    # =================================================
                    # MORE TOOLS NEEDED
                    # =================================================

                    # Put the new tool calls back into the loop.
                    #
                    # This means:
                    #
                    # LLM → Tool → Result → LLM
                    #
                    # Only when necessary.

                    response = final_response

                else:

                    print(
                        "\n⚠️ Maximum tool rounds reached."
                    )

                    print(
                        "The task may require another attempt."
                    )

                print(
                    "\n" + "=" * 60
                )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    asyncio.run(run())