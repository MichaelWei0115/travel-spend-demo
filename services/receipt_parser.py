"""Receipt Parser Service - Simulates OCR field extraction."""

import json
from typing import Optional
from .guardrails import detect_injection


def parse_receipt(receipt_data: dict) -> dict:
    """Parse a receipt and extract structured fields.
    In production this would call an OCR service; here we use mock data.
    """
    # Security: check for injection before processing
    raw_text = receipt_data.get("raw_text", "")
    injection_result = detect_injection(raw_text)

    if injection_result["injection_detected"]:
        return {
            "status": "flagged",
            "action": "flag_suspicious",
            "message": "Receipt contains suspicious content patterns. Treating as data only.",
            "fields": receipt_data.get("fields_extracted", {}),
            "security": injection_result,
            "confidence": 0.10,
        }

    # Normal parsing (using pre-extracted mock fields)
    fields = receipt_data.get("fields_extracted", {})
    ocr_confidence = receipt_data.get("ocr_confidence", 0.0)

    return {
        "status": "parsed",
        "action": "receipt_parsed",
        "message": f"Receipt from {receipt_data.get('merchant', 'unknown')} parsed successfully.",
        "fields": fields,
        "amount": receipt_data.get("amount"),
        "currency": receipt_data.get("currency"),
        "merchant": receipt_data.get("merchant"),
        "category": receipt_data.get("category"),
        "date": receipt_data.get("date"),
        "ocr_confidence": ocr_confidence,
        "security": injection_result,
    }


def extract_fields_summary(parsed: dict) -> list[dict]:
    """Create a summary of extracted fields for display."""
    fields = parsed.get("fields", {})
    summary = []
    for key, value in fields.items():
        summary.append({
            "field": key.replace("_", " ").title(),
            "value": str(value),
            "source": "OCR extraction",
        })
    return summary
