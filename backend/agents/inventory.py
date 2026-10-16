"""Inventory agent. Checks stock by SKU and size, identifies shortages, and identifies suitable restocking vendors.

System prompt: backend/prompts/inventory.md
"""

from .base import build_agent

inventory_agent = build_agent("inventory")
