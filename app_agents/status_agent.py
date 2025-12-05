"""
Status Agent - Handles order status queries.
"""
from agents import Agent

from db.queries import get_order_status

status_agent = Agent(
    name="StatusAgent",
    instructions=(
        "Help customers check their order status. Use get_order_status to retrieve detailed "
        "information about orders. If the customer doesn't provide an order ID, ask them for it. "
        "Always use the tools to get accurate order information rather than guessing."
    ),
    tools=[get_order_status],
)
