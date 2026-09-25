import streamlit as st
import asyncio
import json
import os
import sys

from langchain_groq import ChatGroq
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


# ============================================================
# STREAMLIT
# ============================================================

st.set_page_config(
    page_title="MCP Agent",
    page_icon="🤖"
)

st.title("🤖 MCP Agent")

# ============================================================
# CONFIG
# ============================================================

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    st.error("GROQ_API_KEY is missing.")
    st.stop()

MODEL_NAME = os.getenv(
    "GROQ_MODEL",
    "openai/gpt-oss-20b"
)

# ============================================================
# GROQ
# ============================================================

llm = ChatGroq(
    model=MODEL_NAME,
    temperature=0,
    api_key=GROQ_API_KEY,
)


# ============================================================
# MCP SERVER
# ============================================================

async def run_mcp_agent(user_message):

    server_params = StdioServerParameters(
        command=sys.executable,
        args=["mcp_server.py"],
        env=os.environ.copy()
    )

    async with stdio_client(server_params) as (read, write):

        async with ClientSession(read, write) as session:

            await session.initialize()

            # --------------------------------------------
            # Get MCP tools
            # --------------------------------------------

            tools_result = await session.list_tools()

            tools = tools_result.tools

            tool_descriptions = []

            for tool in tools:
                tool_descriptions.append({
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": tool.inputSchema
                })

            # --------------------------------------------
            # Tell Groq about tools
            # --------------------------------------------

            system_prompt = """
You are an MCP agent.

You have access to tools provided by an MCP server.

Decide whether a tool is required.

If the user asks something that can be answered
without a tool, answer directly.

If a tool is required, return ONLY this JSON:

{
  "action": "tool",
  "tool": "TOOL_NAME",
  "arguments": {}
}

If no tool is required, return ONLY:

{
  "action": "answer",
  "answer": "..."
}

Available tools:

""" + json.dumps(tool_descriptions, indent=2)

            response = await llm.ainvoke([
                ("system", system_prompt),
                ("human", user_message)
            ])

            raw = response.content

            # --------------------------------------------
            # Parse Groq response
            # --------------------------------------------

            try:
                decision = json.loads(raw)
            except Exception:

                return {
                    "type": "answer",
                    "content": raw
                }

            # --------------------------------------------
            # Direct answer
            # --------------------------------------------

            if decision.get("action") == "answer":

                return {
                    "type": "answer",
                    "content": decision.get(
                        "answer",
                        "No answer."
                    )
                }

            # --------------------------------------------
            # Tool execution
            # --------------------------------------------

            if decision.get("action") == "tool":

                tool_name = decision.get("tool")
                arguments = decision.get(
                    "arguments",
                    {}
                )

                result = await session.call_tool(
                    tool_name,
                    arguments=arguments
                )

                output = []

                for item in result.content:

                    if hasattr(item, "text"):
                        output.append(item.text)
                    else:
                        output.append(str(item))

                return {
                    "type": "tool",
                    "tool": tool_name,
                    "content": "\n".join(output)
                }

            return {
                "type": "answer",
                "content": raw
            }


# ============================================================
# CHAT
# ============================================================

if "messages" not in st.session_state:
    st.session_state.messages = []


for message in st.session_state.messages:

    with st.chat_message(message["role"]):
        st.write(message["content"])


user_input = st.chat_input(
    "Ask your MCP agent..."
)


if user_input:

    st.session_state.messages.append({
        "role": "user",
        "content": user_input
    })

    with st.chat_message("user"):
        st.write(user_input)

    with st.chat_message("assistant"):

        try:

            result = asyncio.run(
                run_mcp_agent(user_input)
            )

            if result["type"] == "tool":

                st.caption(
                    f"🔧 Tool: {result['tool']}"
                )

                st.write(result["content"])

                answer = result["content"]

            else:

                answer = result["content"]

                st.write(answer)

            st.session_state.messages.append({
                "role": "assistant",
                "content": answer
            })

        except Exception as e:

            st.error(
                f"Agent error: {type(e).__name__}: {e}"
            )