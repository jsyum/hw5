"""Data types shared by the agent team."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Literal, get_args

from pydantic import BaseModel, Field
from pydantic_ai.usage import UsageLimits

AgentName = Literal["boss", "inventory", "accounting", "facilities", "customer_service"]
AGENT_NAMES: tuple[AgentName, ...] = get_args(AgentName)


class DelegationLimits(BaseModel):
    """Guards against delegation loops and runaway token use.

    The usage limits apply to the WHOLE run: every delegated sub-run shares
    one usage counter with the run that started it.
    """

    max_depth: int = Field(3, description="Longest allowed chain of delegations below the first agent.")
    max_delegations: int = Field(8, description="Total delegations allowed in one run, across all agents.")
    allow_reentry: bool = Field(
        False,
        description="If False, an agent may not delegate to an agent already in its current chain (stops A->B->A ping-pong).",
    )
    request_limit: int = Field(40, description="Total model requests allowed in one run.")
    tool_calls_limit: int = Field(60, description="Total tool calls (MCP tools + delegations) allowed in one run.")
    total_tokens_limit: int = Field(150_000, description="Total tokens allowed in one run.")

    def usage_limits(self) -> UsageLimits:
        return UsageLimits(
            request_limit=self.request_limit,
            tool_calls_limit=self.tool_calls_limit,
            total_tokens_limit=self.total_tokens_limit,
        )


class DelegationRecord(BaseModel):
    """One delegation attempt, accepted or refused."""

    from_agent: AgentName
    to_agent: AgentName
    task: str
    depth: int
    status: Literal["completed", "refused", "failed"]
    reason: str | None = None
    output: str | None = None


@dataclass
class TeamState:
    """Mutable state shared by every agent in one run."""

    delegations: list[DelegationRecord] = field(default_factory=list)

    @property
    def delegation_count(self) -> int:
        return sum(1 for d in self.delegations if d.status != "refused")


@dataclass
class TeamDeps:
    """Dependencies passed to each agent run. A child copy is made per delegation."""

    agent: AgentName
    limits: DelegationLimits = field(default_factory=DelegationLimits)
    state: TeamState = field(default_factory=TeamState)
    chain: tuple[AgentName, ...] = ()
    ticket_id: int | None = None
    run_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])

    @property
    def depth(self) -> int:
        return len(self.chain) - 1

    def child(self, to_agent: AgentName) -> "TeamDeps":
        return TeamDeps(
            agent=to_agent,
            limits=self.limits,
            state=self.state,
            chain=self.chain + (to_agent,),
            ticket_id=self.ticket_id,
            run_id=self.run_id,
        )


class UsageSummary(BaseModel):
    requests: int
    input_tokens: int
    output_tokens: int
    total_tokens: int
    tool_calls: int


class AgentRunResult(BaseModel):
    """What a top-level team run returns."""

    run_id: str
    agent: AgentName
    task: str
    ticket_id: int | None
    output: str
    stopped_by_limit: str | None = None
    delegations: list[DelegationRecord]
    usage: UsageSummary
