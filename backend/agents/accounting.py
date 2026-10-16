"""Accounting agent. Monitors funds and invoices, checks margins, and prepares payments or purchase orders that require human approval.

System prompt: backend/prompts/accounting.md
"""

from .base import build_agent

accounting_agent = build_agent("accounting")
