"""Prompt Rendering Regression Tests
====================================
Verify that all v1/v2 prompt templates render without residual
``{placeholder}`` tokens when given a complete variable context.

These tests guard against the class of bug where a prompt template
references a variable that the event handler does not inject, which
would result in ``{txn_merchant}`` etc. appearing in the prompt text
sent to the AI.
"""

import re
import unittest

from services.event_handler import _load_prompt


# ── Shared variable context ──────────────────────────────────────
# A superset of all variables needed by any v1 or v2 template.
# Extra variables are harmless — _load_prompt only substitutes
# keys that actually appear in the template.

FULL_RECEIPT_MATCH_CONTEXT = {
    # Receipt-side variables
    "receipt_merchant": "Tokyo Grand Hotel",
    "receipt_amount": "820.00",
    "receipt_currency": "USD",
    "receipt_date": "2024-03-15",
    "receipt_category": "hotel",
    "receipt_json": '{"merchant": "Tokyo Grand Hotel", "amount": 820.00}',
    # Transaction-side variables
    "txn_merchant": "Tokyo Hotel",
    "txn_amount": "820.00",
    "txn_currency": "USD",
    "txn_date": "2024-03-15",
    "txn_category": "hotel",
    "transaction_json": '{"merchant": "Tokyo Hotel", "amount": 820.00}',
    # Policy tolerance variables
    "amount_tolerance_pct": "15",
    "date_tolerance_days": "2",
    "low_confidence_threshold": "0.60",
    # Verbose-context variables
    "policy_json": '{"matching": {"amount_tolerance_pct": 15}}',
}

FULL_FAILURE_EXPLANATION_CONTEXT = {
    # Transaction variables
    "merchant": "Tokyo Hotel",
    "amount": "1500.00",
    "currency": "USD",
    "category": "hotel",
    "decline_reason": "exceeds_single_transaction_limit",
    # Policy variables
    "policy_limit": "1000",
    "policy_scope": "single transaction",
    "policy_json": '{"hotel": {"single_transaction_limit": 1000}}',
    # Verbose-context variables
    "transaction_json": '{"merchant": "Tokyo Hotel", "amount": 1500.00}',
    "history_json": "{}",
}


class TestPromptRenderNoPlaceholders(unittest.TestCase):
    """Assert that rendered prompts contain zero residual {var} tokens."""

    PLACEHOLDER_RE = re.compile(r"\{([a-zA-Z_][a-zA-Z0-9_]*)\}")

    def _assert_no_residuals(self, prompt_type: str, version: str, context: dict):
        rendered = _load_prompt(prompt_type, version, context)
        leftovers = self.PLACEHOLDER_RE.findall(rendered)
        self.assertEqual(
            leftovers, [],
            f"{prompt_type}_{version} has unsubstituted placeholders: {leftovers}",
        )

    # ── receipt_match ────────────────────────────────────────────

    def test_receipt_match_v1_no_residuals(self):
        self._assert_no_residuals("receipt_match", "v1", FULL_RECEIPT_MATCH_CONTEXT)

    def test_receipt_match_v2_no_residuals(self):
        self._assert_no_residuals("receipt_match", "v2", FULL_RECEIPT_MATCH_CONTEXT)

    # ── failure_explanation ──────────────────────────────────────

    def test_failure_explanation_v1_no_residuals(self):
        self._assert_no_residuals(
            "failure_explanation", "v1", FULL_FAILURE_EXPLANATION_CONTEXT
        )

    def test_failure_explanation_v2_no_residuals(self):
        self._assert_no_residuals(
            "failure_explanation", "v2", FULL_FAILURE_EXPLANATION_CONTEXT
        )


class TestPromptRenderSanityChecks(unittest.TestCase):
    """Edge-case / sanity tests for the prompt rendering pipeline."""

    PLACEHOLDER_RE = re.compile(r"\{([a-zA-Z_][a-zA-Z0-9_]*)\}")

    def test_missing_variable_produces_residual(self):
        """When a required variable is omitted, a residual placeholder remains.

        This test validates that the residual detection logic itself works
        by intentionally withholding a variable and confirming detection.
        """
        # Remove receipt_merchant from the context
        incomplete = dict(FULL_RECEIPT_MATCH_CONTEXT)
        del incomplete["receipt_merchant"]
        rendered = _load_prompt("receipt_match", "v1", incomplete)
        leftovers = self.PLACEHOLDER_RE.findall(rendered)
        self.assertIn(
            "receipt_merchant", leftovers,
            "Expected receipt_merchant to remain unsubstituted when omitted from context",
        )

    def test_nonexistent_prompt_returns_fallback(self):
        """Loading a non-existent prompt template returns a fallback string."""
        result = _load_prompt("nonexistent_prompt", "v1", {})
        self.assertIn("Prompt template not found", result)

    def test_superset_context_is_harmless(self):
        """Passing extra variables not referenced by the template is safe."""
        extra = dict(FULL_RECEIPT_MATCH_CONTEXT)
        extra["unused_var"] = "hello"
        rendered = _load_prompt("receipt_match", "v1", extra)
        leftovers = self.PLACEHOLDER_RE.findall(rendered)
        self.assertEqual(
            leftovers, [],
            "Extra variables should not cause any issues in rendered output",
        )

    def test_receipt_uploaded_pending_match_context(self):
        """receipt.uploaded events use (pending match) for txn-side vars.

        Verify that even with placeholder-like values, the rendered prompt
        has no residual {var} tokens.
        """
        pending_match_context = dict(FULL_RECEIPT_MATCH_CONTEXT)
        pending_match_context["txn_merchant"] = "(pending match)"
        pending_match_context["txn_amount"] = "(pending match)"
        pending_match_context["txn_currency"] = "(pending match)"
        pending_match_context["txn_date"] = "(pending match)"
        pending_match_context["txn_category"] = "(pending match)"
        pending_match_context["transaction_json"] = "(pending match)"

        self._assert_no_residuals("receipt_match", "v1", pending_match_context)
        self._assert_no_residuals("receipt_match", "v2", pending_match_context)

    def _assert_no_residuals(self, prompt_type, version, context):
        rendered = _load_prompt(prompt_type, version, context)
        leftovers = self.PLACEHOLDER_RE.findall(rendered)
        self.assertEqual(
            leftovers, [],
            f"{prompt_type}_{version} has unsubstituted placeholders: {leftovers}",
        )
