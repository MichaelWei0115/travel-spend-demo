"""Tools Service - Registered tool definitions and execution."""

import json
import time
import random
from typing import Any, Optional


# Tool registry - defines what tools the AI can call
TOOL_REGISTRY = {
    "lookup_policy": {
        "description": "Look up company expense policy for a given category",
        "parameters": {"category": "str"},
        "returns": "Policy rules for the category",
    },
    "lookup_transaction": {
        "description": "Retrieve transaction details by ID",
        "parameters": {"transaction_id": "str"},
        "returns": "Transaction record",
    },
    "lookup_receipt": {
        "description": "Retrieve receipt details by ID",
        "parameters": {"receipt_id": "str"},
        "returns": "Receipt record with OCR fields",
    },
    "calculate_match_score": {
        "description": "Calculate confidence score between receipt and transaction",
        "parameters": {"receipt_id": "str", "transaction_id": "str"},
        "returns": "Match confidence and breakdown",
    },
    "create_ticket_reminder": {
        "description": "Create a ticket reminder for missing receipt",
        "parameters": {"transaction_id": "str", "deadline_hours": "int"},
        "returns": "Reminder record",
    },
    "flag_for_review": {
        "description": "Flag an item for human review",
        "parameters": {"item_id": "str", "reason": "str"},
        "returns": "Review request record",
    },
}


class ToolExecutor:
    """Executes registered tools with logging and error simulation."""

    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.call_log: list[dict] = []
        self.simulate_error: bool = False

    def execute(self, tool_name: str, params: dict) -> dict:
        """Execute a tool call. Returns result or error."""
        call_record = {
            "tool": tool_name,
            "params": params,
            "timestamp": time.time(),
        }

        # Check if tool is registered
        if tool_name not in TOOL_REGISTRY:
            call_record["status"] = "error"
            call_record["error"] = f"Tool '{tool_name}' is not registered"
            self.call_log.append(call_record)
            return {"error": True, "message": f"Tool '{tool_name}' is not registered. Available tools: {list(TOOL_REGISTRY.keys())}"}

        # Simulate errors if enabled
        if self.simulate_error:
            call_record["status"] = "error"
            call_record["error"] = "Simulated tool error"
            self.call_log.append(call_record)
            return {"error": True, "message": "Tool temporarily unavailable. Please retry later."}

        # Execute the tool
        try:
            result = self._dispatch(tool_name, params)
            call_record["status"] = "success"
            call_record["result_preview"] = str(result)[:200]
            self.call_log.append(call_record)
            return {"error": False, "result": result}
        except Exception as e:
            call_record["status"] = "error"
            call_record["error"] = str(e)
            self.call_log.append(call_record)
            return {"error": True, "message": str(e)}

    def _dispatch(self, tool_name: str, params: dict) -> Any:
        """Route tool calls to implementations."""
        if tool_name == "lookup_policy":
            return self._lookup_policy(params.get("category", ""))
        elif tool_name == "lookup_transaction":
            return self._lookup_transaction(params.get("transaction_id", ""))
        elif tool_name == "lookup_receipt":
            return self._lookup_receipt(params.get("receipt_id", ""))
        elif tool_name == "calculate_match_score":
            return self._calculate_match(params.get("receipt_id", ""), params.get("transaction_id", ""))
        elif tool_name == "create_ticket_reminder":
            return self._create_reminder(params.get("transaction_id", ""), params.get("deadline_hours", 72))
        elif tool_name == "flag_for_review":
            return self._flag_review(params.get("item_id", ""), params.get("reason", ""))
        return {"error": "Unknown dispatch"}

    def _lookup_policy(self, category: str) -> dict:
        with open(f"{self.data_dir}/policies.json") as f:
            policies = json.load(f)
        return policies.get(category, {"error": f"No policy found for '{category}'"})

    def _lookup_transaction(self, txn_id: str) -> dict:
        with open(f"{self.data_dir}/transactions.json") as f:
            transactions = json.load(f)
        for txn in transactions:
            if txn["id"] == txn_id:
                return txn
        return {"error": f"Transaction '{txn_id}' not found"}

    def _lookup_receipt(self, receipt_id: str) -> dict:
        with open(f"{self.data_dir}/receipts_mock.json") as f:
            receipts = json.load(f)
        for r in receipts:
            if r["id"] == receipt_id:
                return r
        return {"error": f"Receipt '{receipt_id}' not found"}

    def _calculate_match(self, receipt_id: str, txn_id: str) -> dict:
        receipt = self._lookup_receipt(receipt_id)
        txn = self._lookup_transaction(txn_id)
        if "error" in receipt or "error" in txn:
            return {"error": "Cannot find receipt or transaction"}

        amount_diff = abs(receipt["amount"] - txn["amount"])
        amount_pct = amount_diff / txn["amount"] * 100 if txn["amount"] > 0 else 100

        # Simple merchant similarity
        r_merchant = receipt["merchant"].lower()
        t_merchant = txn["merchant"].lower()
        merchant_sim = 1.0 if t_merchant in r_merchant or r_merchant in t_merchant else 0.5

        # Category match
        cat_match = 1.0 if receipt["category"] == txn["category"] else 0.3

        # Composite score
        score = (0.4 * (1 - min(amount_pct / 20, 1.0)) +
                 0.35 * merchant_sim +
                 0.25 * cat_match)

        return {
            "confidence": round(score, 3),
            "amount_diff": amount_diff,
            "amount_diff_pct": round(amount_pct, 1),
            "merchant_similarity": merchant_sim,
            "category_match": cat_match,
        }

    def _create_reminder(self, txn_id: str, deadline_hours: int) -> dict:
        return {
            "reminder_id": f"rem_{txn_id}",
            "transaction_id": txn_id,
            "deadline_hours": deadline_hours,
            "status": "created",
            "message": f"Receipt reminder created. Please upload within {deadline_hours} hours.",
        }

    def _flag_review(self, item_id: str, reason: str) -> dict:
        return {
            "review_id": f"rev_{item_id}",
            "item_id": item_id,
            "reason": reason,
            "status": "pending_review",
            "assigned_to": "finance_team",
        }

    def get_call_log(self) -> list[dict]:
        return self.call_log.copy()

    def clear_log(self):
        self.call_log = []


# Singleton
tool_executor = ToolExecutor()
