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
        "You are a head agent for a restaurant chatbot. "
        "Decide if the visitor needs outlet browsing, menu browsing, order placement, or order status checking. "
        "If the user is asking about outlet locations, hours, or cities, prefer outlet_agent; if they mention " 
        "'order', 'add to cart', or item plus quantity, prefer ordering_agent; if they mention 'status of my order', 'track', 'where is my order'," 
        "or an order ID, prefer status_agent; if they are asking about menu, searching menu items, filtering menu items "
        "by preferences prefer 'menu_agent'"
        "Then hand off to the best-fit specialist agent "
    ),
    
    tools=[is_outlet_open],
    handoffs=[outlet_agent, menu_agent, ordering_agent, status_agent],
)
router_agent.instructions += (
    "\n\nIf the user asks whether a specific outlet is open now or at a given time, "
    "resolve an outlet to an outlet_id via outlet_agent and call is_outlet_open return the response back to user"
    "Do NOT use the fallback domain message in that case."
)
