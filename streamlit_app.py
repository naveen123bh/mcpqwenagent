import streamlit as st
import os
from groq import Groq

# =========================
# PAGE
# =========================

st.set_page_config(
    page_title="MCP Phone Agent",
    page_icon="📱",
    layout="centered"
)

st.title("📱 MCP Phone Agent")

# =========================
# GROQ
# =========================

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    st.error("GROQ_API_KEY is not configured.")
    st.stop()

client = Groq(api_key=GROQ_API_KEY)

MODEL = os.getenv(
    "GROQ_MODEL",
    "openai/gpt-oss-20b"
)

# =========================
# CHAT MEMORY
# =========================

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# =========================
# CHAT
# =========================

user_input = st.chat_input(
    "Phone ko kya karna hai?"
)

if user_input:

    st.session_state.messages.append({
        "role": "user",
        "content": user_input
    })

    with st.chat_message("user"):
        st.write(user_input)

    # ---------------------
    # Temporary test
    # ---------------------

    with st.chat_message("assistant"):

        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": """
You are an Android MCP agent.

Understand the user's command.
For now, DO NOT execute anything.

Simply explain what action would be required
to perform the command on an Android phone.

Be concise.
"""
                },
                *st.session_state.messages
            ],
            temperature=0
        )

        answer = response.choices[0].message.content

        st.write(answer)

        st.session_state.messages.append({
            "role": "assistant",
            "content": answer
        })