"""AI Client Service - Handles LLM calls with fallback to templates."""

import json
import os
import time
from typing import Optional
from .guardrails import validate_json_output, get_fallback_response
from .observability import tracker
from .memory import working_memory


def get_api_key() -> Optional[str]:
    """Check for OpenAI API key."""
    return os.environ.get("OPENAI_API_KEY")


def has_api_key() -> bool:
    return get_api_key() is not None and len(get_api_key()) > 0


def call_ai(prompt: str, event_type: str, context: dict,
            prompt_version: str = "v1",
            context_mode: str = "compact",
            prefix_mode: str = "stable") -> dict:
    """
    Call AI model or use template fallback.
    
    Args:
        prompt: The formatted prompt text
        event_type: Type of event being processed
        context: Context data for fallback generation
        prompt_version: v1 or v2
        context_mode: compact or verbose
        prefix_mode: stable_prefix or unstable_prefix
    
    Returns:
        AI response dict with action, message, confidence, details
    """
    tracker.start_timer()
    working_memory.add_note(f"AI call: event={event_type}, version={prompt_version}, context={context_mode}")

    # Estimate tokens for the prompt
    token_count = tracker.estimate_tokens(prompt)

    if has_api_key():
        # Real API call would go here
        # For now, fall through to template responses
        working_memory.add_note("API key found but using template mode for demo stability")

    # Use template-based responses (always works without API key)
    response = _generate_template_response(event_type, context, prompt_version)

    # Validate the response
    raw_json = json.dumps(response)
    is_valid, parsed, error = validate_json_output(raw_json)

    latency = tracker.stop_timer()

    if is_valid:
        tracker.record(
            event_type=event_type,
            tokens=token_count,
            latency_ms=latency,
            confidence=response.get("confidence"),
            notes=f"Template response, version={prompt_version}",
        )
        working_memory.add_note(f"Response generated: confidence={response.get('confidence')}")
        return response
    else:
        # Fallback
        working_memory.add_note(f"Validation failed: {error}. Using fallback.")
        fallback = get_fallback_response(event_type, context)
        tracker.record(
            event_type=event_type,
            tokens=token_count,
            latency_ms=latency,
            fallback=True,
            confidence=fallback.get("confidence"),
            notes=f"Fallback used: {error}",
        )
        return fallback


def call_ai_with_forced_error(prompt: str, event_type: str, context: dict) -> dict:
    """Force a malformed response to test JSON validation and fallback."""
    tracker.start_timer()
    working_memory.add_note("Forced malformed JSON test")

    token_count = tracker.estimate_tokens(prompt)

    # Simulate malformed response
    malformed = '{"action": "test", "message": incomplete json...'
    is_valid, parsed, error = validate_json_output(malformed)

    latency = tracker.stop_timer()

    # Should always fail validation
    fallback = get_fallback_response(event_type, context)
    fallback["details"]["forced_error"] = True
    fallback["details"]["original_error"] = error

    tracker.record(
        event_type=event_type,
        tokens=token_count,
        latency_ms=latency,
        fallback=True,
        confidence=fallback.get("confidence"),
        notes="Forced JSON validation failure",
    )
    working_memory.add_note(f"Fallback triggered as expected: {error}")
    return fallback


def _generate_template_response(event_type: str, context: dict, version: str = "v1") -> dict:
    """Generate template-based responses for demo mode."""

    if event_type == "payment.auth.success":
        txn = context.get("transaction", {})
        deadline = 72 if txn.get("category") == "hotel" else 48
        return {
            "action": "generate_ticket_reminder",
            "message": (f"Payment of ${txn.get('amount', 0):.2f} to {txn.get('merchant', 'merchant')} approved. "
                       f"Please upload your receipt within {deadline} hours to complete expense reconciliation."),
            "confidence": 0.95,
            "details": {
                "merchant": txn.get("merchant"),
                "amount": txn.get("amount"),
                "deadline_hours": deadline,
                "reminder_created": True,
                "traveler": txn.get("traveler", "unknown"),
            },
        }

    elif event_type == "payment.auth.failed":
        txn = context.get("transaction", {})
        policy = context.get("policy", {})
        limit = policy.get("single_transaction_limit", "unknown")
        return {
            "action": "explain_failure",
            "message": (f"Payment of ${txn.get('amount', 0):.2f} to {txn.get('merchant', 'merchant')} was declined. "
                       f"Reason: The amount exceeds the {txn.get('category', 'category')} single transaction limit of ${limit}. "
                       f"Suggestions: (1) Split the payment into multiple transactions under ${limit} each, "
                       f"or (2) Request a temporary limit increase from your finance team."),
            "confidence": 0.95,
            "details": {
                "policy_violated": "single_transaction_limit",
                "limit": limit,
                "attempted": txn.get("amount"),
                "overage": txn.get("amount", 0) - limit if isinstance(limit, (int, float)) else None,
                "suggestions": [
                    f"Split into transactions under ${limit}",
                    "Request temporary limit increase",
                    "Use alternative payment method",
                ],
            },
        }

    elif event_type == "receipt.uploaded":
        receipt = context.get("receipt", {})
        return {
            "action": "receipt_parsed",
            "message": f"Receipt from {receipt.get('merchant', 'merchant')} processed. Fields extracted successfully.",
            "confidence": receipt.get("ocr_confidence", 0.8),
            "details": {
                "fields_extracted": receipt.get("fields_extracted", {}),
                "ocr_confidence": receipt.get("ocr_confidence"),
            },
        }

    elif event_type == "receipt.matched":
        # This comes from the matcher service
        return context.get("match_result", {
            "action": "request_review",
            "message": "Match result not available",
            "confidence": 0.5,
            "details": {},
        })

    elif event_type == "reconciliation.failed":
        return {
            "action": "escalate",
            "message": "Reconciliation failed. The receipt could not be matched to any approved transaction. Escalating to finance team.",
            "confidence": 0.85,
            "details": {
                "reason": "no_matching_transaction",
                "next_steps": ["Manual review required", "Contact traveler for clarification"],
            },
        }

    # Default
    return {
        "action": "unknown",
        "message": f"Event type '{event_type}' not recognized.",
        "confidence": 0.3,
        "details": {},
    }


def estimate_cache_friendliness(prefix_mode: str, prompt: str) -> dict:
    """Estimate how cache-friendly a prompt is based on prefix stability."""
    lines = prompt.strip().split("\n")
    total_chars = len(prompt)

    if prefix_mode == "stable":
        # Find stable prefix markers
        stable_start = prompt.find("[STABLE_PREFIX_START]")
        stable_end = prompt.find("[STABLE_PREFIX_END]")
        if stable_start >= 0 and stable_end > stable_start:
            stable_len = stable_end - stable_start
            cache_ratio = stable_len / total_chars
        else:
            # First 30% is assumed stable
            cache_ratio = 0.30
    else:
        # Unstable prefix - minimal caching
        cache_ratio = 0.05

    return {
        "prefix_mode": prefix_mode,
        "total_chars": total_chars,
        "estimated_cacheable_chars": int(total_chars * cache_ratio),
        "cache_hit_ratio_estimate": round(cache_ratio, 2),
        "cost_saving_estimate": f"{cache_ratio * 50:.0f}% on repeated calls",
    }
