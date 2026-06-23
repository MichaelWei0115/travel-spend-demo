"""Evaluator Service - Runs eval cases and reports pass/fail."""

import json
from typing import Optional
from .event_handler import handle_event


def load_eval_cases() -> list[dict]:
    with open("data/eval_cases.json") as f:
        return json.load(f)


def run_single_eval(case: dict) -> dict:
    """Run a single eval case and check expectations."""
    case_id = case["id"]
    event_type = case["event"]
    payload = case["input"]

    # Special flags
    force_malformed = payload.pop("force_malformed_json", False)
    simulate_tool_error = payload.pop("simulate_tool_error", False)

    # Run the event
    result = handle_event(
        event_type=event_type,
        payload=payload,
        prompt_version="v2",
        context_mode="compact",
        prefix_mode="stable",
        simulate_tool_error=simulate_tool_error,
        force_malformed_json=force_malformed,
    )

    # Check expectations
    checks = []

    # Check expected action
    if "expected_action" in case:
        action_match = result.get("action") == case["expected_action"]
        checks.append({
            "check": "action",
            "expected": case["expected_action"],
            "actual": result.get("action"),
            "passed": action_match,
        })

    # Check expected fields exist
    if "expected_fields" in case:
        details = result.get("details", {})
        for field in case["expected_fields"]:
            field_exists = field in details or field in result
            checks.append({
                "check": f"field:{field}",
                "expected": "exists",
                "actual": "found" if field_exists else "missing",
                "passed": field_exists,
            })

    # Check expected text contains
    if "expected_contains" in case:
        message = result.get("message", "").lower()
        details_str = json.dumps(result.get("details", {})).lower()
        full_text = message + " " + details_str
        for keyword in case["expected_contains"]:
            found = keyword.lower() in full_text
            checks.append({
                "check": f"contains:{keyword}",
                "expected": f"'{keyword}' in response",
                "actual": "found" if found else "not found",
                "passed": found,
            })

    # Check minimum confidence
    if "expected_confidence_min" in case:
        conf = result.get("confidence", 0)
        passed = conf >= case["expected_confidence_min"]
        checks.append({
            "check": "confidence_min",
            "expected": f">= {case['expected_confidence_min']}",
            "actual": conf,
            "passed": passed,
        })

    # Check guardrail
    if "expected_guardrail" in case:
        details = result.get("details", {})
        guardrail_triggered = details.get("injection_detected", False)
        checks.append({
            "check": f"guardrail:{case['expected_guardrail']}",
            "expected": "triggered",
            "actual": "triggered" if guardrail_triggered else "not triggered",
            "passed": guardrail_triggered,
        })

    all_passed = all(c["passed"] for c in checks)

    return {
        "case_id": case_id,
        "name": case.get("name", ""),
        "category": case.get("category", ""),
        "passed": all_passed,
        "checks": checks,
        "response_preview": result.get("message", "")[:200],
    }


def run_all_evals() -> dict:
    """Run all eval cases and return summary."""
    cases = load_eval_cases()
    results = []

    for case in cases:
        result = run_single_eval(case)
        results.append(result)

    passed = sum(1 for r in results if r["passed"])
    failed = sum(1 for r in results if not r["passed"])

    return {
        "total": len(results),
        "passed": passed,
        "failed": failed,
        "pass_rate": round(passed / len(results) * 100, 1) if results else 0,
        "results": results,
        "by_category": _group_by_category(results),
    }


def _group_by_category(results: list[dict]) -> dict:
    categories = {}
    for r in results:
        cat = r.get("category", "other")
        if cat not in categories:
            categories[cat] = {"passed": 0, "failed": 0, "total": 0}
        categories[cat]["total"] += 1
        if r["passed"]:
            categories[cat]["passed"] += 1
        else:
            categories[cat]["failed"] += 1
    return categories
