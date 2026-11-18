"""Lossless evidence artifacts and honest separation of contract/review outcomes."""

import json
import re
from pathlib import Path

from tests.ai.evaluation_evidence import source_summary


def code_block(text, language=""):
    text = str(text)
    longest = max((len(s) for s in re.findall(r"`+", text)), default=0)
    fence = "`" * max(3, longest + 1)
    return f"{fence}{language}\n{text}\n{fence}\n"


def evidence_markdown(result):
    parts = [
        f"- **Semantic review**: {result.get('review_status', 'insufficient_evidence')}\n"
    ]
    for index, turn in enumerate(result.get("turns", []), 1):
        parts.append(f"\n#### Turn {index} — observed source: {turn['source']}\n\n")
        parts.append("**Full prompt**\n\n" + code_block(turn["prompt"]))
        parts.append("\n**Full final response**\n\n" + code_block(turn["response"]))
        parts.append(
            "\n**Source events / raw output**\n\n"
            + code_block(
                json.dumps(turn.get("events", []), ensure_ascii=False, indent=2), "json"
            )
        )
        if turn.get("error"):
            parts.append(f"\nGeneration error: {turn['error']}\n")
    parts.append(
        "\n**Full context evidence**\n\n"
        + code_block(
            json.dumps(result.get("context_info", {}), ensure_ascii=False, indent=2),
            "json",
        )
    )
    return "".join(parts)


def evidence_summary(results):
    return {
        "contract_results": {
            status: sum(r["status"] == status for r in results)
            for status in ("PASS", "PARTIAL", "FAIL")
        },
        "semantic_review": {
            status: sum(r.get("review_status") == status for r in results)
            for status in ("pending", "insufficient_evidence", "not_applicable")
        },
        "turns_by_source_and_contract_status": source_summary(results),
    }


def write_json_report(path, results, *, model):
    report = {
        "schema_version": 1,
        "model": model,
        "scope": "Automatic contracts are not semantic quality approval. Source labels are observed per turn; unknown is not model success.",
        "summary": evidence_summary(results),
        "results": results,
    }
    Path(path).write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return report
