"""
Run with: streamlit run app.py
Requirements:
pip install streamlit python-dotenv openai-agents "langsmith[openai-agents]"
"""

import asyncio
import uuid
import os
import time
from collections import deque
from app_agents.menu_agent import menu_agent
from app_agents.ordering_agent import ordering_agent
from app_agents.status_agent import status_agent
from app_agents.outlet_agent import outlet_agent
from models import ConversationContext
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
from db.connection import get_connection

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
# Helper Functions
# ---------------------------------------------------------------------

@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_all_outlets():
    """Fetch all active outlets from the database."""
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, name, city, state
            FROM outlets
            WHERE is_active = TRUE
            ORDER BY city, name
        """)
        outlets = cur.fetchall()
        cur.close()
        conn.close()
        return outlets
    except Exception as e:
        st.error(f"Error fetching outlets: {str(e)}")
        return []

@st.cache_data(ttl=300)  # Cache for 5 minutes per outlet
def get_outlet_menu_cached(outlet_id: int):
    """Fetch menu for a specific outlet with caching."""
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        # Verify outlet exists
        cur.execute("SELECT name FROM outlets WHERE id = %s AND is_active = TRUE", (outlet_id,))
        outlet_row = cur.fetchone()
        if not outlet_row:
            cur.close()
            conn.close()
            return None
        
        outlet_name = outlet_row[0]
        
        query = """
            SELECT 
                mi.id,
                mi.name,
                mi.description,
                mi.category,
                mi.base_price,
                mi.is_veg,
                mi.is_spicy,
                oma.is_available,
                oma.available_from_time,
                oma.available_to_time
            FROM menu_items mi
            INNER JOIN outlet_menu_availability oma ON oma.menu_item_id = mi.id
            WHERE oma.outlet_id = %s
              AND mi.is_active = TRUE
            ORDER BY mi.category, mi.name
        """
        
        cur.execute(query, (outlet_id,))
        rows = cur.fetchall()
        cur.close()
        conn.close()
        
        return {
            "outlet_name": outlet_name,
            "outlet_id": outlet_id,
            "items": rows
        }
    except Exception as e:
        return None

# ---------------------------------------------------------------------
# Rate Limiting
# ---------------------------------------------------------------------

def init_rate_limiter():
    """Initialize rate limiter in session state if not present."""
    if "rate_limiter_calls" not in st.session_state:
        st.session_state.rate_limiter_calls = deque()
    if "rate_limiter_max_calls" not in st.session_state:
        st.session_state.rate_limiter_max_calls = 100  # 100 calls per minute
    if "rate_limiter_window" not in st.session_state:
        st.session_state.rate_limiter_window = 60  # 60 seconds

def enforce_rate_limit():
    """
    Enforce rate limiting: max 100 LLM calls per minute.
    If limit is reached, sleep until a slot becomes available.
    """
    init_rate_limiter()
    
    now = time.time()
    window_start = now - st.session_state.rate_limiter_window
    
    # Remove calls outside the time window
    while (st.session_state.rate_limiter_calls and 
           st.session_state.rate_limiter_calls[0] < window_start):
        st.session_state.rate_limiter_calls.popleft()
    
    # Check if we're at the limit
    current_calls = len(st.session_state.rate_limiter_calls)
    
    if current_calls >= st.session_state.rate_limiter_max_calls:
        # Calculate how long to wait until the oldest call expires
        oldest_call_time = st.session_state.rate_limiter_calls[0]
        wait_time = (oldest_call_time + st.session_state.rate_limiter_window) - now + 0.1
        
        if wait_time > 0:
            # Show a message to user (optional, can be removed for production)
            with st.spinner(f"Rate limit reached. Waiting {wait_time:.1f}s..."):
                time.sleep(wait_time)
            
            # Clean up expired calls again after waiting
            now = time.time()
            window_start = now - st.session_state.rate_limiter_window
            while (st.session_state.rate_limiter_calls and 
                   st.session_state.rate_limiter_calls[0] < window_start):
                st.session_state.rate_limiter_calls.popleft()
    
    # Record this call
    st.session_state.rate_limiter_calls.append(time.time())

# ---------------------------------------------------------------------
# Streamlit UI
# ---------------------------------------------------------------------
st.set_page_config(
    page_title="Restaurant Chatbot",
    page_icon="🍽️",
    layout="wide"
)

# Sidebar for outlet selection and session controls
with st.sidebar:
    st.header("⚙️ Controls")
    
    # Session Controls
    st.subheader("📋 Session")
    st.text(f"Session ID: {st.session_state.get('session_id', 'N/A')[:12]}...")
    
    if st.button("🔄 New Session", use_container_width=True):
        st.session_state.session_id = f"web-{uuid.uuid4().hex[:8]}"
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
        st.rerun()
    
    if st.button("🗑️ Clear Chat", use_container_width=True):
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
        st.rerun()
    
    st.divider()
    
    # Outlet Selection
    st.subheader("🏪 Select Outlet")
    outlets = get_all_outlets()
    
    if outlets:
        outlet_options = {f"#{outlet[0]} - {outlet[1]} ({outlet[2]}, {outlet[3]})": outlet[0] 
                         for outlet in outlets}
        
        selected_outlet_label = st.selectbox(
            "Choose an outlet:",
            options=["None"] + list(outlet_options.keys()),
            key="outlet_selector",
            help="Select an outlet to view its menu or place orders"
        )
        
        if selected_outlet_label != "None":
            selected_outlet_id = outlet_options[selected_outlet_label]
            st.session_state.selected_outlet_id = selected_outlet_id
            st.info(f"Selected: Outlet #{selected_outlet_id}")
            
            # Quick action buttons
            if st.button("📖 View Menu", use_container_width=True):
                prompt = f"Show me the menu for outlet #{selected_outlet_id}"
                st.session_state.quick_action = prompt
                st.rerun()
        else:
            st.session_state.selected_outlet_id = None
    else:
        st.warning("No outlets available")
    
    st.divider()
    
    # Rate Limit Status
    init_rate_limiter()
    now = time.time()
    window_start = now - st.session_state.rate_limiter_window
    
    # Clean up old calls for display
    recent_calls = [t for t in st.session_state.rate_limiter_calls if t >= window_start]
    current_calls = len(recent_calls)
    max_calls = st.session_state.rate_limiter_max_calls
    
    st.subheader("⚡ Rate Limit")
    usage_pct = (current_calls / max_calls) * 100 if max_calls > 0 else 0
    st.progress(usage_pct / 100)
    st.caption(f"{current_calls}/{max_calls} calls in last minute")
    
    if usage_pct >= 90:
        st.warning("⚠️ Approaching rate limit")
    elif usage_pct >= 100:
        st.error("🚫 Rate limit reached")
    
    st.divider()
    st.caption("💡 Tip: Select an outlet to quickly access its menu")

# Main chat area
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

# Handle quick actions from sidebar or chat input
prompt = None
if "quick_action" in st.session_state:
    prompt = st.session_state.quick_action
    del st.session_state.quick_action
else:
    prompt = st.chat_input("How can we help today?")

AGENT_MAP = {
    "menu_agent": menu_agent,
    "ordering_agent": ordering_agent,
    "status_agent": status_agent,
    "outlet_agent": outlet_agent,
}

async def handle_user_message(conversation_id: str, user_message: str, session):
    ctx = ConversationContext(
        conversation_id=conversation_id,
        raw_user_message=user_message,
    )

    # 1) Run router once
    router_result = await Runner.run(router_agent, user_message, session=session)

    # Expect the router to return structured fields in final_output (you can adjust this)
    meta = getattr(router_result, "metadata", {}) or {}
    ctx.intent = meta.get("intent")
    ctx.outlet_id = meta.get("outlet_id")
    ctx.candidate_menu_item_ids = meta.get("candidate_menu_item_ids", [])
    ctx.order_id = meta.get("order_id")
    target = meta.get("target_agent")  # "menu_agent", "ordering_agent", "status_agent", "outlet_agent", or "clarify"

    # 2) Clarify / no-op
    if target in (None, "clarify"):
        return router_result.final_output or (
            "Can you clarify whether you want to browse the menu, place an order, or track an order?"
        )

    # 3) One handoff to specialist
    specialist = AGENT_MAP.get(target)
    if specialist is None:
        return "Sorry, something went wrong while routing your request. Please try again."

    specialist_result = await Runner.run(
        specialist,
        user_message,
        session=session,
        # If your Runner/agents support extra kwargs, pass context here; if not,
        # you’ll instead embed ctx into the prompt in the specialist agents.
    )

    return specialist_result.final_output or "Done."


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

        # Enforce rate limiting before making LLM call
        enforce_rate_limit()

        async def _run():
            return await handle_user_message(
                st.session_state.session_id,
                prompt,
                session=session,
            )

        # Stream assistant response in chat-style block
        with st.chat_message("assistant"):
            placeholder = st.empty()
            placeholder.markdown("_Checking with our specialists..._")
            try:
                result = asyncio.run(_run())
            except Exception as e:
                result = f"I encountered an error: {str(e)}. Please try again."
            placeholder.markdown(result)

        st.session_state.messages.append({"role": "assistant", "content": result})
