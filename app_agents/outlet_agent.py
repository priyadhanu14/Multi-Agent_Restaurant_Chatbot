"""
Outlet Agent - Handles outlet browsing, searching, and filtering.
"""
from agents import Agent
from db.queries import get_outlets_by_city_or_zip, is_outlet_open

outlet_agent = Agent(
    name="OutletAgent",
    instructions=(
        "Help guests explore the restaurant outlets. Answer questions about outlets, "
        "operating hours, and details. Use the provided tools to look up information "
        "rather than guessing. If they mention a location, help them find outlets first. "
    ),
    tools=[
        get_outlets_by_city_or_zip,
        is_outlet_open,
    ],
)
