"""Audited agent loop. Every top-level and delegated run goes through run_audited().

Each loop step is appended to output/audit_trail.json: run start, every model
response (text and tool calls), every tool result, delegations, the final
output, and why the run stopped.
"""

from __future__ import annotations

from typing import Any

from pydantic_ai import Agent
from pydantic_ai.exceptions import UsageLimitExceeded
from pydantic_ai.messages import RetryPromptPart, TextPart, ToolCallPart, ToolReturnPart
from pydantic_ai.usage import RunUsage

from mcp_server import audit

from .models import TeamDeps


def _base(deps: TeamDeps) -> dict[str, Any]:
    return {"run_id": deps.run_id, "ticket_id": deps.ticket_id, "agent": deps.agent,
            "chain": list(deps.chain), "depth": deps.depth}


def _usage(u: RunUsage) -> dict[str, int]:
    return {"requests": u.requests, "input_tokens": u.input_tokens, "output_tokens": u.output_tokens,
            "total_tokens": u.total_tokens, "tool_calls": u.tool_calls}


async def run_audited(agent: Agent[TeamDeps, str], task: str, deps: TeamDeps, usage: RunUsage) -> str:
    base = _base(deps)
    audit.append("agent_run_started", **base, task=task)
    step = 0
    try:
        async with agent.iter(task, deps=deps, usage=usage, usage_limits=deps.limits.usage_limits()) as run:
            async for node in run:
                if Agent.is_call_tools_node(node):
                    step += 1
                    resp = node.model_response
                    audit.append(
                        "model_response", **base, step=step,
                        text="".join(p.content for p in resp.parts if isinstance(p, TextPart)) or None,
                        tool_calls=[{"tool": p.tool_name, "args": p.args, "call_id": p.tool_call_id}
                                    for p in resp.parts if isinstance(p, ToolCallPart)],
                        model=resp.model_name, finish_reason=getattr(resp, "finish_reason", None),
                        usage_so_far=_usage(usage),
                    )
                elif Agent.is_model_request_node(node):
                    for part in node.request.parts:
                        if isinstance(part, ToolReturnPart):
                            audit.append("tool_result", **base, step=step, tool=part.tool_name,
                                         call_id=part.tool_call_id, result=part.model_response_str())
                        elif isinstance(part, RetryPromptPart):
                            audit.append("tool_retry", **base, step=step, tool=part.tool_name,
                                         call_id=part.tool_call_id, error=part.model_response())
            output = str(run.result.output)
    except UsageLimitExceeded as exc:
        audit.append("agent_run_stopped", **base, step=step, stop_reason="usage_limit", detail=str(exc),
                     usage=_usage(usage))
        raise
    except Exception as exc:
        audit.append("agent_run_failed", **base, step=step, stop_reason="error",
                     detail=f"{type(exc).__name__}: {exc}", usage=_usage(usage))
        raise
    audit.append("agent_run_finished", **base, steps=step, stop_reason="final_output", output=output,
                 usage=_usage(usage))
    return output
