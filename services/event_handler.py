"""Event Handler Service - Routes events to appropriate processing pipelines."""

import json
from typing import Optional
from .ai_client import call_ai, call_ai_with_forced_error
from .matcher import match_receipt_to_transaction
from .receipt_parser import parse_receipt
from .guardrails import check_override_attempt, detect_injection
from .tools import tool_executor
from .memory import working_memory
from .observability import tracker


def load_data():
    """Load all mock data."""
    with open("data/transactions.json") as f:
        transactions = json.load(f)
    with open("data/receipts_mock.json") as f:
        receipts = json.load(f)
    with open("data/policies.json") as f:
        policies = json.load(f)
    return transactions, receipts, policies


def get_transaction(txn_id: str) -> Optional[dict]:
    transactions, _, _ = load_data()
    for t in transactions:
        if t["id"] == txn_id:
            return t
    return None


def get_receipt(receipt_id: str) -> Optional[dict]:
    _, receipts, _ = load_data()
    for r in receipts:
        if r["id"] == receipt_id:
            return r
    return None


def handle_event(event_type: str, payload: dict,
                 prompt_version: str = "v1",
                 context_mode: str = "compact",
                 prefix_mode: str = "stable",
                 simulate_tool_error: bool = False,
                 force_malformed_json: bool = False) -> dict:
    """
    Main event handling entry point.
    Routes events to appropriate handlers and returns AI response.
    """
    _, _, policies = load_data()

    # Start working memory
    task_id = f"{event_type}_{payload.get('transaction_id', payload.get('receipt_id', 'unknown'))}"
    working_memory.start_task(task_id)
    working_memory.add_note(f"Event received: {event_type}")
    working_memory.add_note(f"Config: version={prompt_version}, context={context_mode}, prefix={prefix_mode}")

    # Set tool error simulation
    tool_executor.simulate_error = simulate_tool_error

    try:
        if event_type == "payment.auth.success":
            result = _handle_payment_success(payload, policies, prompt_version, context_mode, prefix_mode, force_malformed_json)
        elif event_type == "payment.auth.failed":
            result = _handle_payment_failed(payload, policies, prompt_version, context_mode, prefix_mode)
        elif event_type == "receipt.uploaded":
            result = _handle_receipt_uploaded(payload, policies, prompt_version, context_mode, prefix_mode)
        elif event_type == "receipt.matched":
            result = _handle_receipt_matched(payload, policies, prompt_version, context_mode, prefix_mode)
        elif event_type == "reconciliation.failed":
            result = _handle_reconciliation_failed(payload, policies)
        elif event_type == "user_override_attempt":
            result = _handle_override_attempt(payload)
        else:
            result = {
                "action": "unknown_event",
                "message": f"Unknown event type: {event_type}",
                "confidence": 0.0,
                "details": {},
            }

        # Attach working notes and tool log
        result["_working_notes"] = working_memory.get_formatted()
        result["_tool_calls"] = tool_executor.get_call_log()

        # Clear working memory
        memory_summary = working_memory.clear()
        result["_memory_summary"] = memory_summary

        return result

    finally:
        tool_executor.simulate_error = False
        tool_executor.clear_log()


def _handle_payment_success(payload, policies, version, context_mode, prefix_mode, force_malformed):
    txn = get_transaction(payload.get("transaction_id", ""))
    if not txn:
        return {"action": "error", "message": "Transaction not found", "confidence": 0, "details": {}}

    working_memory.add_note(f"Transaction found: {txn['merchant']} ${txn['amount']}")

    # Tool call: create reminder
    policy = policies.get(txn["category"], {})
    deadline = policy.get("receipt_deadline_hours", 72)

    tool_result = tool_executor.execute("create_ticket_reminder", {
        "transaction_id": txn["id"],
        "deadline_hours": deadline,
    })
    working_memory.add_note(f"Tool call: create_ticket_reminder -> {tool_result.get('error', 'success')}")

    # Build prompt
    prompt = _load_prompt("failure_explanation", version, {
        "merchant": txn["merchant"],
        "amount": txn["amount"],
        "currency": txn["currency"],
        "category": txn["category"],
    })

    context = {"transaction": txn, "policy": policy, "tool_result": tool_result}

    if force_malformed:
        return call_ai_with_forced_error(prompt, "payment.auth.success", context)

    return call_ai(prompt, "payment.auth.success", context, version, context_mode, prefix_mode)


def _handle_payment_failed(payload, policies, version, context_mode, prefix_mode):
    txn = get_transaction(payload.get("transaction_id", ""))
    if not txn:
        return {"action": "error", "message": "Transaction not found", "confidence": 0, "details": {}}

    working_memory.add_note(f"Failed transaction: {txn['merchant']} ${txn['amount']}")

    # Tool call: lookup policy
    policy_result = tool_executor.execute("lookup_policy", {"category": txn["category"]})
    policy = policy_result.get("result", {}) if not policy_result.get("error") else policies.get(txn["category"], {})
    working_memory.add_note(f"Policy lookup: limit=${policy.get('single_transaction_limit', '?')}")

    prompt = _load_prompt("failure_explanation", version, {
        "merchant": txn["merchant"],
        "amount": txn["amount"],
        "currency": txn["currency"],
        "category": txn["category"],
        "decline_reason": txn.get("decline_reason", "unknown"),
        "policy_limit": policy.get("single_transaction_limit", "unknown"),
        "policy_scope": "single transaction",
    })

    context = {"transaction": txn, "policy": policy}
    return call_ai(prompt, "payment.auth.failed", context, version, context_mode, prefix_mode)


def _handle_receipt_uploaded(payload, policies, version, context_mode, prefix_mode):
    receipt = get_receipt(payload.get("receipt_id", ""))
    if not receipt:
        return {"action": "error", "message": "Receipt not found", "confidence": 0, "details": {}}

    working_memory.add_note(f"Receipt uploaded: {receipt['merchant']} ${receipt['amount']}")

    # Tool call: lookup receipt (this will fail if simulate_tool_error is enabled)
    tool_result = tool_executor.execute("lookup_receipt", {"receipt_id": receipt["id"]})
    if tool_result.get("error"):
        working_memory.add_note(f"Tool error: {tool_result.get('message')}")
        tracker.record(
            event_type="receipt.uploaded",
            tokens=tracker.estimate_tokens(str(receipt)),
            fallback=True,
            confidence=0.40,
            notes="Tool error during receipt processing",
        )
        return {
            "action": "graceful_degradation",
            "message": "Receipt processing tool temporarily unavailable. Please retry later. Your receipt has been queued for processing.",
            "confidence": 0.40,
            "details": {
                "tool_error": True,
                "receipt_id": receipt["id"],
                "suggestion": "retry",
            },
        }

    # Parse receipt (includes injection check)
    parsed = parse_receipt(receipt)
    working_memory.add_note(f"Parse result: status={parsed['status']}, confidence={parsed.get('confidence', parsed.get('ocr_confidence'))}")

    if parsed["status"] == "flagged":
        tracker.record(
            event_type="receipt.uploaded",
            tokens=tracker.estimate_tokens(str(receipt)),
            confidence=0.10,
            notes="Injection detected in receipt",
        )
        return {
            "action": "flag_suspicious",
            "message": parsed["message"],
            "confidence": 0.10,
            "details": {
                "injection_detected": True,
                "security": parsed["security"],
                "receipt_id": receipt["id"],
            },
        }

    context = {"receipt": receipt, "parsed": parsed}
    prompt = _load_prompt("receipt_match", version, {
        "receipt_merchant": receipt["merchant"],
        "receipt_amount": receipt["amount"],
        "receipt_currency": receipt["currency"],
        "receipt_date": receipt.get("date", ""),
        "receipt_category": receipt.get("category", ""),
    })

    return call_ai(prompt, "receipt.uploaded", context, version, context_mode, prefix_mode)


def _handle_receipt_matched(payload, policies, version, context_mode, prefix_mode):
    txn = get_transaction(payload.get("transaction_id", ""))
    receipt = get_receipt(payload.get("receipt_id", ""))

    if not txn or not receipt:
        return {"action": "error", "message": "Transaction or receipt not found", "confidence": 0, "details": {}}

    working_memory.add_note(f"Matching: receipt {receipt['id']} <-> transaction {txn['id']}")

    # Run matching
    match_result = match_receipt_to_transaction(receipt, txn, policies)
    working_memory.add_note(f"Match result: action={match_result['action']}, confidence={match_result['confidence']}")

    # Track confidence for observability
    tracker.record(
        event_type="receipt.matched",
        tokens=tracker.estimate_tokens(str(match_result)),
        confidence=match_result["confidence"],
        human_confirm=match_result["action"] == "request_review",
        notes=f"Match {receipt['id']}<->{txn['id']}",
    )

    return match_result


def _handle_reconciliation_failed(payload, policies):
    working_memory.add_note("Reconciliation failed event")
    return {
        "action": "escalate",
        "message": "Automatic reconciliation failed. Escalating to finance team for manual review.",
        "confidence": 0.85,
        "details": {
            "reason": payload.get("reason", "unknown"),
            "next_steps": ["Manual review required", "Contact traveler for clarification"],
        },
    }


def _handle_override_attempt(payload):
    """Handle user trying to verbally override locked facts."""
    claim = payload.get("claim", "")
    locked_field = payload.get("locked_field", "")
    locked_value = payload.get("locked_value")

    working_memory.add_note(f"Override attempt: claim='{claim}', locked={locked_field}={locked_value}")

    result = check_override_attempt(claim, {locked_field: locked_value})

    if result["override_attempted"]:
        working_memory.add_note("Override REJECTED - locked field cannot be modified by user claim")
        tracker.record(
            event_type="user_override_attempt",
            tokens=tracker.estimate_tokens(claim),
            confidence=0.99,
            notes="Override rejected",
        )
        return result["response"]
    else:
        return {
            "action": "no_conflict",
            "message": "No locked field conflict detected.",
            "confidence": 0.90,
            "details": {},
        }


def _load_prompt(prompt_type: str, version: str, variables: dict) -> str:
    """Load and format a prompt template."""
    filename = f"prompts/{prompt_type}_{version}.txt"
    try:
        with open(filename) as f:
            template = f.read()
        # Simple variable substitution
        for key, value in variables.items():
            template = template.replace(f"{{{key}}}", str(value))
        return template
    except FileNotFoundError:
        return f"[Prompt template not found: {filename}]"
