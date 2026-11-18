"""Case-specific assertions, separate from prose quality heuristics."""

import json
import re


def command_contract_issues(response, *, action, title):
    """Require a recognized action and exact task title, not just structured text."""
    if not isinstance(response, str) or not response.strip():
        return ["Empty command response"]
    try:
        data = json.loads(response)
    except (ValueError, TypeError):
        fields = dict(re.findall(r"^([A-Z_]+):\s*(.*)$", response, re.M))
        actual_action = fields.get("ACTION", "").casefold()
        actual_title = fields.get("TITLE", "")
    else:
        if not isinstance(data, dict):
            return ["Command response is not an object"]
        actual_action = str(data.get("action", "")).casefold()
        details = data.get("details") or {}
        actual_title = details.get("title", "") if isinstance(details, dict) else ""
    issues = []
    if actual_action != action:
        issues.append(f"Expected action {action}; got {actual_action or 'missing'}")
    if str(actual_title).strip().casefold() != title.casefold():
        issues.append(f"Expected exact task title: {title}")
    return issues


def review_status(turns, test_type, *, has_response=True):
    if test_type in ("mode_detection", "postprocess", "cache_contract"):
        return "not_applicable"
    if not turns and not has_response:
        return "not_applicable"
    if any(turn.get("source") == "unknown" for turn in turns):
        return "insufficient_evidence"
    return "pending" if turns else "insufficient_evidence"


def audit_case_input(case, messages):
    """Check expected inputs and instructions in assembled messages, before inference.

    The caller supplies assembled or post-fit messages and records that scope.
    This does not detect arbitrary semantic instruction conflicts.
    Explicit prerequisites prevent blaming a model for a missing app instruction.
    """
    users = [m["content"] for m in messages if m["role"] == "user"]
    current = users[-1] if users else ""
    system = "\n".join(m["content"] for m in messages if m["role"] == "system")
    context_issues = []
    if case["request"] not in current:
        context_issues.append("Current request missing from the final user message")
    if "context" in case and json.dumps(case["context"]) not in current:
        context_issues.append("Expected reference context missing from the user message")
    for turn in case.get("history", []):
        if turn not in messages:
            context_issues.append("Expected history turn or its role was not preserved")
    if "result" in case and json.dumps(case["result"], ensure_ascii=False, default=str) not in current:
        context_issues.append("Expected execution result missing from the user message")
    instruction_issues = [
        f"Required instruction missing: {text}"
        for text in case.get("required_instructions", []) if text.casefold() not in system.casefold()
    ]
    instruction_issues += [
        f"Conflicting instruction present: {text}"
        for text in case.get("conflicting_instructions", []) if text.casefold() in system.casefold()
    ]
    return {"context_issues": context_issues, "instruction_issues": instruction_issues,
            "scope": "supplied messages; caller determines assembly/fitting stage"}


def diagnose_case_failure(case, *, audit, raw, issues, raw_issues, failure=None):
    """Attribute observed failures conservatively; semantic judgments need review."""
    if audit["context_issues"]:
        return {"origin": "application_context", "evidence": audit["context_issues"]}
    if audit["instruction_issues"]:
        return {"origin": "application_prompt", "evidence": audit["instruction_issues"]}
    if failure:
        return {"origin": "transport_or_configuration", "evidence": [failure]}
    if not issues and not raw_issues:
        return {"origin": "none_observed", "evidence": []}
    if case.get("kind") == "planner":
        # These are explicit supported no-action forms. A rejected one is an app
        # contract/parser problem, not evidence of malformed model generation.
        if case.get("intent") == "answer_only" and re.fullmatch(
            r"\s*(?:INTENT:\s*answer_only|ACTION:\s*unknown)\s*", raw, re.IGNORECASE
        ):
            return {"origin": "application_parser", "evidence": issues}
    if issues and not raw_issues and case.get("kind") != "planner":
        return {"origin": "application_postprocessing", "evidence": issues}
    return {"origin": "model_output", "evidence": raw_issues or issues,
            "review_required": True}
