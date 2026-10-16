"""Registry of the five agents and the entry points for a team run."""

from __future__ import annotations

from typing import Any

from pydantic_ai import Agent
from pydantic_ai.exceptions import UsageLimitExceeded
from pydantic_ai.usage import RunUsage

from mcp_server import audit

from .agents.accounting import accounting_agent
from .agents.boss import boss_agent
from .agents.customer_service import customer_service_agent
from .agents.facilities import facilities_agent
from .agents.inventory import inventory_agent
from .mcp_client import MCP_TOOLSET, call_operator_tool
from .models import (
    AGENT_NAMES,
    AgentName,
    AgentRunResult,
    DelegationLimits,
    TeamDeps,
    UsageSummary,
)
from .runner import _usage, run_audited

AGENTS: dict[AgentName, Agent[TeamDeps, str]] = {
    "boss": boss_agent,
    "inventory": inventory_agent,
    "accounting": accounting_agent,
    "facilities": facilities_agent,
    "customer_service": customer_service_agent,
}
assert set(AGENTS) == set(AGENT_NAMES)


def get_agent(name: AgentName) -> Agent[TeamDeps, str]:
    return AGENTS[name]


async def reset_database() -> Any:
    """Restore the working database from the original, via the MCP server. Call before each full ticket run."""
    return await call_operator_tool("reset_working_database")


async def run_agent(
    task: str,
    agent: AgentName = "boss",
    ticket_id: int | None = None,
    limits: DelegationLimits | None = None,
    run_id: str | None = None,
) -> AgentRunResult:
    """Run one agent (Boss by default) on a task; it may delegate to any other agent. Never resets the database."""
    limits = limits or DelegationLimits()
    deps = TeamDeps(agent=agent, limits=limits, chain=(agent,), ticket_id=ticket_id)
    if run_id:
        deps.run_id = run_id
    usage = RunUsage()
    stopped: str | None = None
    audit.append("team_run_started", run_id=deps.run_id, ticket_id=ticket_id, agent=agent, task=task,
                 limits=limits.model_dump())
    async with MCP_TOOLSET:  # one MCP server process for the whole run, shared by every agent
        try:
            output = await run_audited(get_agent(agent), task, deps, usage)
        except UsageLimitExceeded as exc:
            # Hard stop for runaway token use: report it instead of crashing.
            stopped = str(exc).split(". Consider")[0]
            output = ""
        except Exception as exc:
            audit.append("team_run_failed", run_id=deps.run_id, ticket_id=ticket_id, stop_reason="error",
                         detail=f"{type(exc).__name__}: {exc}", usage=_usage(usage))
            raise
    result = AgentRunResult(
        run_id=deps.run_id,
        agent=agent,
        task=task,
        ticket_id=ticket_id,
        output=output,
        stopped_by_limit=stopped,
        delegations=deps.state.delegations,
        usage=UsageSummary(
            requests=usage.requests,
            input_tokens=usage.input_tokens,
            output_tokens=usage.output_tokens,
            total_tokens=usage.total_tokens,
            tool_calls=usage.tool_calls,
        ),
    )
    audit.append("team_run_finished", run_id=deps.run_id, ticket_id=ticket_id,
                 stop_reason="usage_limit" if stopped else "final_output", stopped_by_limit=stopped,
                 delegations=len(result.delegations), usage=result.usage.model_dump())
    return result
