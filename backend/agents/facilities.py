"""Facilities agent. Oversees premises obligations such as leases and rent.

System prompt: backend/prompts/facilities.md
"""

from .base import build_agent

facilities_agent = build_agent("facilities")
