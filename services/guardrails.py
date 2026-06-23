"""Guardrails Service - JSON validation, injection detection, override protection."""

import json
import re
from typing import Any, Optional


INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?previous",
    r"override\s+(all\s+)?rules",
    r"mark\s+(this\s+)?(as\s+)?(approved|passed|valid)",
    r"forget\s+(your\s+)?instructions",
    r"you\s+are\s+now",
    r"new\s+instructions",
    r"disregard\s+(the\s+)?(above|previous|system)",
]

REQUIRED_JSON_FIELDS = ["action", "message", "confidence"]


def detect_injection(text: str) -> dict:
    """Scan text for prompt injection attempts."""
    text_lower = text.lower()
    detections = []

    for pattern in INJECTION_PATTERNS:
        matches = re.findall(pattern, text_lower)
        if matches:
            detections.append({
                "pattern": pattern,
                "matched": True,
            })

    return {
        "injection_detected": len(detections) > 0,
        "detections": detections,
        "risk_level": "high" if len(detections) >= 2 else "medium" if detections else "low",
    }


def validate_json_output(raw: str) -> tuple[bool, Optional[dict], str]:
    """Validate AI output is valid JSON with required fields.
    Returns: (is_valid, parsed_dict_or_None, error_message)
    """
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as e:
        return False, None, f"Invalid JSON: {str(e)}"

    if not isinstance(parsed, dict):
        return False, None, "Output must be a JSON object"

    missing = [f for f in REQUIRED_JSON_FIELDS if f not in parsed]
    if missing:
        return False, None, f"Missing required fields: {missing}"

    # Confidence range check
    conf = parsed.get("confidence")
    if conf is not None:
        if not isinstance(conf, (int, float)) or conf < 0 or conf > 1:
            return False, None, f"Confidence must be 0.0-1.0, got: {conf}"

    return True, parsed, ""


def get_fallback_response(event_type: str, context: dict) -> dict:
    """Generate a safe fallback response when AI output is invalid."""
    fallbacks = {
        "payment.auth.success": {
            "action": "generate_ticket_reminder",
            "message": f"Payment approved for {context.get('merchant', 'unknown')}. Please upload your receipt within the policy deadline.",
            "confidence": 0.80,
            "details": {"fallback_used": True, "reason": "AI output validation failed"},
        },
        "payment.auth.failed": {
            "action": "explain_failure",
            "message": f"Payment for {context.get('merchant', 'unknown')} was declined. Please check with your finance team for policy limits.",
            "confidence": 0.70,
            "details": {"fallback_used": True, "reason": "AI output validation failed"},
        },
        "receipt.uploaded": {
            "action": "acknowledge_receipt",
            "message": "Receipt received. Processing is temporarily unavailable. Please try again shortly.",
            "confidence": 0.60,
            "details": {"fallback_used": True, "reason": "AI output validation failed"},
        },
        "receipt.matched": {
            "action": "request_review",
            "message": "Unable to automatically match this receipt. Please review manually.",
            "confidence": 0.50,
            "details": {"fallback_used": True, "reason": "AI output validation failed"},
        },
    }
    return fallbacks.get(event_type, {
        "action": "error",
        "message": "Unable to process this request. Please contact support.",
        "confidence": 0.0,
        "details": {"fallback_used": True, "reason": "Unknown event type"},
    })


def check_override_attempt(claim: str, locked_fields: dict) -> dict:
    """Check if user is trying to override locked system facts."""
    # Extract potential amount claims
    amount_patterns = re.findall(r'(\d+(?:\.\d+)?)\s*(USD|CNY|EUR|GBP)', claim, re.IGNORECASE)

    override_detected = False
    conflicts = []

    for amount_str, currency in amount_patterns:
        claimed_amount = float(amount_str)
        if "amount" in locked_fields:
            locked_amount = locked_fields["amount"]
            if abs(claimed_amount - locked_amount) > 0.01:
                override_detected = True
                conflicts.append({
                    "field": "amount",
                    "claimed": claimed_amount,
                    "system_record": locked_amount,
                })

    return {
        "override_attempted": override_detected,
        "conflicts": conflicts,
        "response": {
            "action": "reject_override",
            "message": f"Cannot modify locked field(s). System record shows the verified amount. "
                       f"If you believe this is incorrect, please submit a dispute through the finance portal.",
            "confidence": 0.99,
            "details": {"locked_fields": locked_fields, "conflicts": conflicts},
        } if override_detected else None,
    }
