"""Shared agent factory and the delegation tool every agent carries."""

from __future__ import annotations

from pathlib import Path

from pydantic_ai import Agent, RunContext

from mcp_server import audit

from ..config import build_model
from ..mcp_client import toolset_for
from ..models import AGENT_NAMES, AgentName, DelegationRecord, TeamDeps

PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"


def load_prompt(name: AgentName) -> str:
    """Read backend/prompts/<name>.md at run time, so prompt edits apply without a restart."""
    path = PROMPTS_DIR / f"{name}.md"
    return path.read_text(encoding="utf-8").strip() if path.exists() else ""


async def delegate(ctx: RunContext[TeamDeps], to_agent: AgentName, task: str) -> str:
    """Hand a sub-task to another Campus Customs agent and get its answer back.

    Agents: boss, inventory, accounting, facilities, customer_service.
    Give the task as a complete, self-contained instruction, including any
    ticket id, SKU, size, amounts, or dates the other agent will need.
    """
    deps = ctx.deps
    limits = deps.limits

    def refuse(reason: str) -> str:
        deps.state.delegations.append(
            DelegationRecord(from_agent=deps.agent, to_agent=to_agent, task=task,
                             depth=deps.depth + 1, status="refused", reason=reason)
        )
        audit.append("delegation_refused", run_id=deps.run_id, ticket_id=deps.ticket_id, agent=deps.agent,
                     chain=list(deps.chain), to_agent=to_agent, task=task, reason=reason)
        return f"Delegation refused: {reason} Complete the task yourself with what you have."

    if to_agent not in AGENT_NAMES:
        return refuse(f"unknown agent '{to_agent}'.")
    if to_agent == deps.agent:
        return refuse("an agent cannot delegate to itself.")
    if deps.depth + 1 > limits.max_depth:
        return refuse(f"maximum delegation depth ({limits.max_depth}) reached.")
    if deps.state.delegation_count >= limits.max_delegations:
        return refuse(f"maximum delegations per run ({limits.max_delegations}) reached.")
    if not limits.allow_reentry and to_agent in deps.chain:
        chain = " -> ".join(deps.chain)
        return refuse(f"'{to_agent}' is already working on this chain ({chain}); return your answer instead of delegating back.")

    from ..runner import run_audited  # late imports: team imports every agent module
    from ..team import get_agent

    record = DelegationRecord(from_agent=deps.agent, to_agent=to_agent, task=task,
                              depth=deps.depth + 1, status="completed")
    deps.state.delegations.append(record)
    audit.append("delegation_started", run_id=deps.run_id, ticket_id=deps.ticket_id, agent=deps.agent,
                 chain=list(deps.chain), to_agent=to_agent, task=task)
    try:
        # ctx.usage is shared, so the usage limits cover the whole run.
        output = await run_audited(get_agent(to_agent), task, deps.child(to_agent), ctx.usage)
    except Exception as exc:
        record.status = "failed"
        record.reason = f"{type(exc).__name__}: {exc}"
        raise
    record.output = output
    audit.append("delegation_returned", run_id=deps.run_id, ticket_id=deps.ticket_id, agent=deps.agent,
                 to_agent=to_agent, output=output)
    return output


def build_agent(name: AgentName) -> Agent[TeamDeps, str]:
    """Create one team agent: gpt-6-luna via OpenAI, its prompt file, its MCP tools, and the delegate tool."""
    agent: Agent[TeamDeps, str] = Agent(
        build_model(),
        name=name,
        deps_type=TeamDeps,
        output_type=str,
        tools=[delegate],
        toolsets=[toolset_for(name)],
    )

    @agent.instructions
    def _instructions() -> str:
        return load_prompt(name)

    return agent
