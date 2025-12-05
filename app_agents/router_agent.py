"""
Router Agent - Routes messages to appropriate specialized agents.
"""
from agents import Agent

from db import is_outlet_open

from .menu_agent import menu_agent
from .ordering_agent import ordering_agent
from .status_agent import status_agent
from .outlet_agent import outlet_agent
from db.queries import is_outlet_open

router_agent = Agent(
    name="RestaurantRouterAgent",
    instructions=(
        "You are a routing agent for a restaurant chatbot. "
        "Decide if the visitor needs outlet browsing, menu browsing, order placement, or order status checking. "
        "Then hand off to the best-fit specialist agent: "
        "- outlet_agent: For browsing outlets, searching by city or zip code "
        "- menu_agent: For browsing menu, searching items, filtering by preferences "
        "- ordering_agent: For placing orders, managing cart, checkout "
        "- status_agent: For checking order status, tracking orders"
        "- restaurant_agent: For updating the order status."
    ),
    
    tools=[is_outlet_open],
    handoffs=[outlet_agent, menu_agent, ordering_agent, status_agent],
)
router_agent.instructions += (
    "\n\nIf the user asks whether a specific outlet is open now or at a given time, "
    "you MUST call the `is_outlet_open` tool with the correct outlet_id. "
    "Do NOT use the fallback domain message in that case."
)
