"""Matcher Service - Receipt-to-transaction matching logic."""

import json
from typing import Optional
from .guardrails import detect_injection


def match_receipt_to_transaction(receipt: dict, transaction: dict, policies: dict) -> dict:
    """Match a receipt to a transaction and return confidence assessment."""

    # Step 1: Check for injection in receipt content
    raw_text = receipt.get("raw_text", "") + " " + receipt.get("merchant", "")
    injection_check = detect_injection(raw_text)

    if injection_check["injection_detected"]:
        return {
            "action": "flag_suspicious",
            "message": "Receipt content contains suspicious instructions. Flagged for security review. "
                       "The receipt text is being treated as data only and no embedded instructions were executed.",
            "confidence": 0.10,
            "details": {
                "injection_detected": True,
                "risk_level": injection_check["risk_level"],
                "receipt_id": receipt.get("id"),
                "note": "Receipt content treated as DATA, not instructions",
            },
        }

    # Step 2: Calculate match metrics
    amount_diff = abs(receipt["amount"] - transaction["amount"])
    amount_pct = (amount_diff / transaction["amount"] * 100) if transaction["amount"] > 0 else 100

    # Merchant similarity (simple containment check)
    r_merchant = receipt.get("merchant", "").lower()
    t_merchant = transaction.get("merchant", "").lower()
    if t_merchant in r_merchant or r_merchant in t_merchant:
        merchant_sim = 0.95
    elif any(w in r_merchant for w in t_merchant.split()):
        merchant_sim = 0.70
    else:
        merchant_sim = 0.30

    # Category match
    cat_match = receipt.get("category") == transaction.get("category")

    # Get thresholds from policy
    matching_policy = policies.get("matching", {})
    amount_tolerance = matching_policy.get("amount_tolerance_pct", 15)
    high_threshold = matching_policy.get("high_confidence_threshold", 0.85)
    low_threshold = matching_policy.get("low_confidence_threshold", 0.60)

    # Step 3: Compute composite confidence
    amount_score = max(0, 1 - (amount_pct / amount_tolerance))
    confidence = (0.40 * amount_score + 0.35 * merchant_sim + 0.25 * (1.0 if cat_match else 0.3))

    # Cap at 0.95 (overconfidence calibration)
    confidence = min(confidence, 0.95)

    # Step 4: Determine action
    if confidence >= high_threshold:
        action = "auto_match"
        message = (f"High confidence match: {receipt['merchant']} receipt "
                   f"(${receipt['amount']}) matches {transaction['merchant']} "
                   f"transaction (${transaction['amount']}).")
        possible_reasons = []
    elif confidence >= low_threshold:
        action = "request_review"
        possible_reasons = _identify_discrepancy_reasons(receipt, transaction)
        message = (f"Low confidence match ({confidence:.0%}). "
                   f"Amount difference: ${amount_diff:.2f} ({amount_pct:.1f}%). "
                   f"Possible reasons: {', '.join(possible_reasons)}. "
                   f"Recommended: manual review or request updated receipt.")
    else:
        action = "request_review"
        possible_reasons = _identify_discrepancy_reasons(receipt, transaction)
        message = (f"Very low confidence ({confidence:.0%}). Significant discrepancies found. "
                   f"This may not be a valid match.")

    return {
        "action": action,
        "message": message,
        "confidence": round(confidence, 3),
        "details": {
            "amount_diff": round(amount_diff, 2),
            "amount_diff_pct": round(amount_pct, 1),
            "merchant_similarity": merchant_sim,
            "category_match": cat_match,
            "possible_reasons": possible_reasons if confidence < high_threshold else [],
            "injection_detected": False,
            "calibration_note": "Confidence capped at 0.95 per overconfidence calibration policy",
        },
    }


def _identify_discrepancy_reasons(receipt: dict, transaction: dict) -> list[str]:
    """Identify possible reasons for amount discrepancy."""
    reasons = []
    diff = transaction["amount"] - receipt["amount"]

    if diff > 0:
        if transaction.get("category") == "dining":
            reasons.append("Possible tip not reflected on receipt")
            reasons.append("Tax may be calculated differently")
        reasons.append("Additional charges or fees may apply")
    elif diff < 0:
        reasons.append("Partial refund or discount applied after receipt")
        reasons.append("Currency conversion difference")

    if receipt.get("merchant", "").lower() != transaction.get("merchant", "").lower():
        reasons.append("Merchant name variation between receipt and card statement")

    return reasons if reasons else ["Unknown discrepancy"]
