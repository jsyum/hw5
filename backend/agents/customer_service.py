"""Customer Service agent. Drafts customer messages (drafts only; nothing is sent).

System prompt: backend/prompts/customer_service.md
"""

from .base import build_agent

customer_service_agent = build_agent("customer_service")
