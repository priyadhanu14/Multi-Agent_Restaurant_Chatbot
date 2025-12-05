"""
App Agents package - Simplified structure matching reference.
"""
from app_agents.router_agent import router_agent
from app_agents.menu_agent import menu_agent
from app_agents.ordering_agent import ordering_agent
from app_agents.status_agent import status_agent

__all__ = [
    "router_agent",
    "menu_agent",
    "ordering_agent",
    "status_agent",
]
