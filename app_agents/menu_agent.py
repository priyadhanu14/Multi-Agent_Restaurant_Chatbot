"""
Menu Agent - Handles menu browsing, searching, and filtering.
"""
from agents import Agent

from db.queries import (
    get_outlet_menu,
    filter_menu,
    is_outlet_open,
)   

menu_agent = Agent(
    name="MenuAgent",
    instructions=(
        "Help guests explore the restaurant menu. Answer questions about menu items, "
        "availability, pricing, and details. Use the provided tools to look up information "
        "rather than guessing. If they mention a location, help them find outlets first. "
        "If they ask about menu items, show them the menu for the selected outlet."
    ),
    tools=[
        get_outlet_menu,
        filter_menu,
        is_outlet_open,
    ],
)
