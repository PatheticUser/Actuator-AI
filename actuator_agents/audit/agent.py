"""
Audit Agent — Actuator AI

QA, hallucination detection, policy compliance.
audit_logs and escalations from PostgreSQL.
"""

import sys
import os
import asyncio
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from agents import Agent, Runner, ModelSettings, function_tool

from shared.models.ollama_provider import get_model
from shared.mcp_config import get_mcp_postgres
from shared.guardrails.safety import detect_jailbreak
from shared.tools.db_tools import get_audit_logs, get_escalations


# --- Tools ---

@function_tool
def check_hallucination(agent_response: str, tool_outputs: str) -> str:
    """Compare agent response against tool outputs to detect hallucinations.

    Args:
        agent_response: The response text from an agent.
        tool_outputs: Raw tool output that the agent based its response on.
    """
    import re
    response_numbers = set(re.findall(r'\b\d+[,.]?\d*\b', agent_response))
    tool_numbers = set(re.findall(r'\b\d+[,.]?\d*\b', tool_outputs))

    unverified_numbers = response_numbers - tool_numbers
    hallucination_risk = "LOW"
    findings = []

    if unverified_numbers:
        hallucination_risk = "MEDIUM"
        findings.append(
            f"⚠ Unverified numbers in response: {', '.join(list(unverified_numbers)[:5])}"
        )

    confidence_markers = ["always", "never", "guaranteed", "100%", "certainly", "definitely"]
    found_markers = [m for m in confidence_markers if m in agent_response.lower()]
    if found_markers:
        hallucination_risk = "HIGH" if hallucination_risk == "MEDIUM" else "MEDIUM"
        findings.append(f"⚠ Overconfident language: {', '.join(found_markers)}")

    if not findings:
        findings.append("✅ No hallucination indicators detected")

    return (
        f"Hallucination Check:\n"
        f"  Risk Level: {hallucination_risk}\n"
        f"  Findings:\n    " + "\n    ".join(findings)
    )


@function_tool
def check_policy_compliance(agent_response: str, agent_name: str) -> str:
    """Check if response follows company policies.

    Args:
        agent_response: The response text to check.
        agent_name: Name of the agent that generated the response.
    """
    import re
    violations = []
    response_lower = agent_response.lower()

    if re.search(r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b', agent_response):
        violations.append("🚨 CRITICAL: Full credit card number exposed")
    if re.search(r'\b\d{3}-\d{2}-\d{4}\b', agent_response):
        violations.append("🚨 CRITICAL: SSN pattern detected")

    promise_words = ["guarantee", "promise", "100% uptime", "free upgrade"]
    found = [w for w in promise_words if w in response_lower]
    if found:
        violations.append(f"⚠ Unauthorized promises: {', '.join(found)}")

    competitors = ["zendesk", "intercom", "freshdesk", "salesforce service cloud"]
    found_comp = [c for c in competitors if c in response_lower]
    if found_comp:
        violations.append(f"⚠ Competitor mentioned: {', '.join(found_comp)}")

    if "refund" in response_lower and "approved" not in response_lower:
        if "processed" in response_lower or "issued" in response_lower:
            violations.append("⚠ Refund without approval workflow")

    compliant = len(violations) == 0
    return (
        f"Policy Compliance ({agent_name}):\n"
        f"  Status: {'✅ COMPLIANT' if compliant else '❌ VIOLATIONS FOUND'}\n"
        f"  Issues: {len(violations)}\n"
        + ("\n    ".join([""] + violations) if violations else "")
    )


@function_tool
def audit_conversation(conversation_id: str) -> str:
    """Pull full audit trail for a conversation from database.

    Args:
        conversation_id: Conversation UUID.
    """
    from shared.tools.db_tools import _query

    # Get conversation
    convs = _query(
        "SELECT * FROM conversations WHERE id = %s", (conversation_id,)
    )
    if not convs or "error" in convs[0]:
        return f"Conversation not found: {conversation_id}"

    c = convs[0]
    # Get audit entries
    audits = _query(
        "SELECT agent_name, action, hallucination_risk, policy_compliant, quality_score, latency_ms, tokens_used "
        "FROM audit_logs WHERE conversation_id = %s ORDER BY created_at",
        (conversation_id,),
    )

    # Get messages count
    msgs = _query(
        "SELECT count(*) as cnt FROM messages WHERE conversation_id = %s",
        (conversation_id,),
    )

    audit_lines = []
    for a in audits:
        audit_lines.append(
            f"    {a['agent_name']} | {a['action']} | H-risk: {a['hallucination_risk']} | "
            f"Compliant: {'✅' if a['policy_compliant'] else '❌'} | Quality: {a['quality_score']}/100 | "
            f"{a['latency_ms']}ms | {a['tokens_used']} tokens"
        )

    msg_count = msgs[0]["cnt"] if msgs and "error" not in msgs[0] else "?"
    duration = ""
    if c.get("ended_at") and c.get("started_at"):
        delta = c["ended_at"] - c["started_at"]
        duration = f"\n  Duration: {delta}"

    return (
        f"Audit Trail — {conversation_id}:\n"
        f"  Status: {c['status']} | Last agent: {c['last_agent']}\n"
        f"  Customer: {c.get('customer_email', 'N/A')}\n"
        f"  Started: {c['started_at']} | Ended: {c.get('ended_at', 'Active')}"
        f"{duration}\n"
        f"  Messages: {msg_count}\n"
        f"  Summary: {c.get('summary', 'N/A')}\n"
        f"  Audit entries ({len(audits)}):\n"
        + ("\n".join(audit_lines) if audit_lines else "    No audit entries")
    )


@function_tool
def score_response_accuracy(agent_response: str, expected_outcome: str) -> str:
    """Score response accuracy against expected outcome.

    Args:
        agent_response: Agent's actual response.
        expected_outcome: What the response should have contained.
    """
    response_words = set(agent_response.lower().split())
    expected_words = set(expected_outcome.lower().split())
    overlap = response_words & expected_words
    coverage = len(overlap) / max(len(expected_words), 1) * 100

    if coverage > 70:
        grade = "A — Highly accurate"
    elif coverage > 50:
        grade = "B — Mostly accurate"
    elif coverage > 30:
        grade = "C — Partially accurate"
    else:
        grade = "D — Needs review"

    return (
        f"Accuracy Score:\n"
        f"  Grade: {grade}\n"
        f"  Coverage: {coverage:.1f}%\n"
        f"  Terms matched: {len(overlap)} / {len(expected_words)}"
    )


@function_tool
def generate_qa_report(agent_name: str = "") -> str:
    """Generate QA report from audit_logs database. Optionally filter by agent.

    Args:
        agent_name: Filter by agent (empty for all agents).
    """
    from shared.tools.db_tools import _query

    if agent_name:
        rows = _query(
            "SELECT agent_name, count(*) as cnt, "
            "avg(quality_score) as avg_quality, avg(latency_ms) as avg_latency, "
            "sum(tokens_used) as total_tokens, "
            "count(CASE WHEN hallucination_risk = 'high' THEN 1 END) as high_risk, "
            "count(CASE WHEN policy_compliant = false THEN 1 END) as violations "
            "FROM audit_logs WHERE agent_name ILIKE %s GROUP BY agent_name",
            (f"%{agent_name}%",),
        )
    else:
        rows = _query(
            "SELECT agent_name, count(*) as cnt, "
            "avg(quality_score) as avg_quality, avg(latency_ms) as avg_latency, "
            "sum(tokens_used) as total_tokens, "
            "count(CASE WHEN hallucination_risk = 'high' THEN 1 END) as high_risk, "
            "count(CASE WHEN policy_compliant = false THEN 1 END) as violations "
            "FROM audit_logs GROUP BY agent_name ORDER BY avg_quality DESC"
        )

    if not rows or "error" in rows[0]:
        return "No audit data available."

    total = sum(r["cnt"] for r in rows)
    overall_quality = sum(r["avg_quality"] * r["cnt"] for r in rows if r["avg_quality"]) / max(total, 1)

    lines = [f"QA Report (from audit_logs — {total} entries):"]
    lines.append(f"  Overall avg quality: {overall_quality:.0f}/100\n")

    for r in rows:
        lines.append(
            f"  {r['agent_name']}:\n"
            f"    Audited: {r['cnt']} | Quality: {r['avg_quality']:.0f}/100 | "
            f"Avg latency: {r['avg_latency']:.0f}ms\n"
            f"    Tokens: {r['total_tokens']:,} | High-risk: {r['high_risk']} | "
            f"Violations: {r['violations']}"
        )

    return "\n".join(lines)


# --- Dynamic Instructions ---
def build_instructions(ctx, agent):
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    return f"""You are the Audit Agent for Actuator AI. Current time: {now}

CAPABILITIES:
- Hallucination detection (compare response vs tool output)
- Policy compliance checking (PII, promises, competitors, refunds)
- Conversation audit trail from database
- Response accuracy scoring
- QA report generation from audit_logs database
- Audit log and escalation retrieval from database

PROTOCOL:
1. For hallucination: compare against actual tool outputs
2. For compliance: check all categories (PII, promises, competitors, refunds)
3. For audit trails: pull from DB, show agent chain and metrics
4. For reports: aggregate from audit_logs table, highlight issues

AUDIT RULES:
- CRITICAL violations (PII) must be flagged immediately
- HIGH hallucination risk requires human review
- Document violations with specific evidence
- QA scores should be fair — consider complexity
- Never modify audited content
- You now have access to 'query' tool via MCP for direct PostgreSQL table reads/joins. Ensure schemas are verified."""


# --- Agent ---
agent = Agent(
    name="Audit Agent",
    instructions=build_instructions,
    model=get_model(),
    model_settings=ModelSettings(temperature=0.1, max_tokens=1200),
    tools=[
        check_hallucination,
        check_policy_compliance,
        audit_conversation,
        score_response_accuracy,
        generate_qa_report,
        get_audit_logs,
        get_escalations,
    ],
    mcp_servers=[get_mcp_postgres()],
    input_guardrails=[detect_jailbreak],
    handoff_description="Audit: QA review, hallucination detection, policy compliance, accuracy scoring, conversation audits",
)


async def main():
    queries = [
        "Generate a QA report for all agents",
    ]
    for query in queries:
        print(f"\n{'='*60}\nQuery: {query}")
        result = await Runner.run(agent, query)
        print(f"Response:\n{result.final_output}")


if __name__ == "__main__":
    asyncio.run(main())
