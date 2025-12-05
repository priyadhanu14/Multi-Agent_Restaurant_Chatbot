"""
Run with: streamlit run app.py
Requirements:
pip install streamlit python-dotenv openai-agents "langsmith[openai-agents]"
"""

import asyncio
import uuid
import os

import streamlit as st

try:
    from dotenv import load_dotenv
    load_dotenv()  # loads OPENAI_API_KEY, DB_*, LANGSMITH_* from .env
except ImportError:
    # python-dotenv not installed, using environment variables directly
    pass

from agents import Runner, SQLiteSession, set_trace_processors

try:
    from langsmith.wrappers import OpenAIAgentsTracingProcessor
    LANGSMITH_AVAILABLE = True
except ImportError:
    LANGSMITH_AVAILABLE = False

from app_agents.router_agent import router_agent

# ---------------------------------------------------------------------
# Boot
# ---------------------------------------------------------------------

# Optional: attach LangSmith tracing (comment out to disable)
if LANGSMITH_AVAILABLE:
    try:
        set_trace_processors([OpenAIAgentsTracingProcessor()])
    except Exception:
        pass  # LangSmith not configured

# Add strict fallback if no tool applies
RULE = (
    "\n\nCRITICAL RULE: Only if the user's request is clearly NOT about restaurant "
    "outlets, opening hours, menu items, placing orders, or checking order status "
    "(for example, questions about personal life, movies, programming help, etc.), "
    "then reply EXACTLY with: "
    "'I can only help with restaurant menu, orders, and order status. "
    "How can I assist you with that?' "
    "In all other cases, call the appropriate tools."
)

if RULE not in router_agent.instructions:
    router_agent.instructions += RULE

# ---------------------------------------------------------------------
# Streamlit UI
# ---------------------------------------------------------------------
st.set_page_config(
    page_title="Restaurant Chatbot",
    page_icon="🍽️",
    layout="centered"
)
st.title("🍽️ Restaurant Multi-Agent Chatbot")
st.caption("Ask about outlets, menu, place orders, or check order status—our specialists will help you.")

# Create (or reuse) a persistent session id for conversation memory
if "session_id" not in st.session_state:
    st.session_state.session_id = f"web-{uuid.uuid4().hex[:8]}"

# Persist chat transcript for on-screen history
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                "### 👋 Welcome to your Food Ordering Assistant\n\n"
                "I can help you with:\n"
                "- 🏪 **Outlets** – find restaurants in a city \n"
                "- 📖 **Menus** – browse items, or filter by cuisine, veg/spicy, or price\n"
                "- 🛒 **Orders** – place a new order for pickup or delivery\n"
                "- 🔔 **Order status** – check the status of an existing order\n\n"
                "**Try asking me:**\n"
                "- \"Show me the outlets in Seattle\"\n"
                "- \"What vegetarian options do you have at Downtown Diner?\"\n"
                "- \"I want to order 2 Chicken Tikka Masala for delivery\"\n"
                "- \"What is the status of order #number ?\"\n\n"
                "What would you like to do today?"
            ),
        }
    ]


# Render chat history
chat_container = st.container()
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input anchored at the bottom
prompt = st.chat_input("How can we help today?")

if prompt:
    prompt = prompt.strip()
    if not prompt:
        st.warning("Please enter a question.")
    else:
        # Display user message immediately
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        session = SQLiteSession(st.session_state.session_id, "conversations.db")

        async def _run():
            return await Runner.run(router_agent, prompt, session=session)

        # Stream assistant response in chat-style block
        with st.chat_message("assistant"):
            placeholder = st.empty()
            placeholder.markdown("_Checking with our specialists..._")
            try:
                result = asyncio.run(_run())
                assistant_reply = result.final_output or "I'm sorry, I couldn't process that request."
            except Exception as e:
                assistant_reply = f"I encountered an error: {str(e)}. Please try again."
            placeholder.markdown(assistant_reply)

        st.session_state.messages.append({"role": "assistant", "content": assistant_reply})
