"""Boss agent. Reviews each ticket, assigns work to the responsible agents, and makes the final decisions.

System prompt: backend/prompts/boss.md
"""

from .base import build_agent

boss_agent = build_agent("boss")
