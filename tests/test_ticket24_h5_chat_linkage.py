"""
Ticket 24: H5 与聊天页结果联动
===============================
Tests that H5 operations (supplement, retry, confirm sync)
correctly append result messages to the chat and navigate
based on the current 4-status model:
  pending_receipt / pending_submit / submitted / error

Previous version used the old 5-status model (ai_check_result + sync_status).
Those tests have been replaced with 4-status model tests.
"""

import sys
import os
import unittest
from unittest.mock import MagicMock

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Minimal Streamlit mock
class _MockSessionState(dict):
    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(key)
    def __setattr__(self, key, value):
        self[key] = value
    def __delattr__(self, key):
        try:
            del self[key]
        except KeyError:
            raise AttributeError(key)

_mock_st = MagicMock()
_session = _MockSessionState()
_mock_st.session_state = _session

sys.modules["streamlit"] = _mock_st
sys.modules.setdefault("streamlit.components", MagicMock())
sys.modules.setdefault("streamlit.components.v1", MagicMock())

from reimbursement_data import (
    get_default_records,
    STATUS_PENDING_RECEIPT, STATUS_PENDING_SUBMIT, STATUS_SUBMITTED, STATUS_ERROR,
)
import demo_actions
import demo_state

# Wire mock session state into modules
demo_actions.st = _mock_st
demo_state.st = _mock_st


def _fresh_state():
    """Reset session state to a clean initial condition."""
    _session.clear()
    _session["messages"] = []
    _session["demo_step"] = 0
    _session["current_task_state"] = "idle"
    _session["active_modal"] = None
    _session["current_phone_page"] = "chat"
    _session["previous_phone_page"] = "chat"
    _session["reimbursement_records"] = get_default_records()
    _session["record_filter"] = "all"
    _session["selected_record_id"] = None
    _session["supplement_form"] = {
        "invoice_uploaded": False,
        "invoice_name": "",
        "receipt_uploaded": False,
        "receipt_name": "",
        "note": "",
        "expense_type": "",
    }
    _session["toast_message"] = ""
    _session["loading_action"] = None
    _session["h5_completed_actions"] = {}
    _mock_st.session_state = _session
    demo_actions.st = _mock_st
    demo_state.st = _mock_st


def _find_record_by_status(records, status):
    """Find the first record with the given status."""
    for r in records:
        if r.get("status") == status:
            return r
    raise AssertionError(f"No record found with status={status}")


# =============================================================================
# Tests: 4-status model H5-Chat linkage
# =============================================================================

class TestUploadReceiptLinkage(unittest.TestCase):
    """After uploading receipt (pending_receipt -> pending_submit), chat gets a message."""

    def setUp(self):
        _fresh_state()
        self.rec = _find_record_by_status(
            _session["reimbursement_records"], STATUS_PENDING_RECEIPT)
        _session["selected_record_id"] = self.rec["id"]

    def test_message_appended_to_chat(self):
        demo_actions.handle_demo_action("upload_receipt")
        msgs = _session["messages"]
        self.assertEqual(len(msgs), 1)
        self.assertIn(self.rec["merchant_name"], msgs[0]["content"])

    def test_status_changes_to_pending_submit(self):
        demo_actions.handle_demo_action("upload_receipt")
        rec = demo_actions.get_record(self.rec["id"])
        self.assertEqual(rec["status"], STATUS_PENDING_SUBMIT)

    def test_no_duplicate_on_repeat(self):
        demo_actions.handle_demo_action("upload_receipt")
        demo_actions.handle_demo_action("upload_receipt")
        msgs = _session["messages"]
        self.assertEqual(len(msgs), 1, "Should not duplicate message on repeat action")


class TestConfirmSubmitLinkage(unittest.TestCase):
    """After confirming submit (pending_submit -> submitted), chat gets a message."""

    def setUp(self):
        _fresh_state()
        self.rec = _find_record_by_status(
            _session["reimbursement_records"], STATUS_PENDING_SUBMIT)
        _session["selected_record_id"] = self.rec["id"]

    def test_message_appended_to_chat(self):
        demo_actions.handle_demo_action("confirm_submit")
        msgs = _session["messages"]
        self.assertEqual(len(msgs), 1)
        self.assertIn(self.rec["merchant_name"], msgs[0]["content"])

    def test_status_changes_to_submitted(self):
        demo_actions.handle_demo_action("confirm_submit")
        rec = demo_actions.get_record(self.rec["id"])
        self.assertEqual(rec["status"], STATUS_SUBMITTED)

    def test_no_duplicate_on_repeat(self):
        demo_actions.handle_demo_action("confirm_submit")
        demo_actions.handle_demo_action("confirm_submit")
        msgs = _session["messages"]
        self.assertEqual(len(msgs), 1, "Should not duplicate message on repeat action")


class TestConfirmSingleSyncLinkage(unittest.TestCase):
    """After confirm-single-sync from H5 detail, chat gets a message."""

    def setUp(self):
        _fresh_state()
        self.rec = _find_record_by_status(
            _session["reimbursement_records"], STATUS_PENDING_SUBMIT)
        _session["selected_record_id"] = self.rec["id"]

    def test_message_appended_to_chat(self):
        demo_actions.handle_demo_action(
            "confirm_single_sync", {"record_id": self.rec["id"]})
        msgs = _session["messages"]
        self.assertEqual(len(msgs), 1)
        self.assertIn("报销系统", msgs[0]["content"])

    def test_navigates_to_detail(self):
        _session["current_phone_page"] = "reimbursement_list"
        demo_actions.handle_demo_action(
            "confirm_single_sync", {"record_id": self.rec["id"]})
        self.assertEqual(_session["current_phone_page"], "reimbursement_detail")

    def test_no_duplicate_on_repeat(self):
        demo_actions.handle_demo_action(
            "confirm_single_sync", {"record_id": self.rec["id"]})
        demo_actions.handle_demo_action(
            "confirm_single_sync", {"record_id": self.rec["id"]})
        msgs = _session["messages"]
        self.assertEqual(len(msgs), 1, "Should not duplicate message on repeat action")


class TestRetryProcessLinkage(unittest.TestCase):
    """After retry process (error -> pending_submit), chat gets a message."""

    def setUp(self):
        _fresh_state()
        self.rec = _find_record_by_status(
            _session["reimbursement_records"], STATUS_ERROR)
        _session["selected_record_id"] = self.rec["id"]

    def test_message_appended_to_chat(self):
        demo_actions.handle_demo_action(
            "retry_process", {"record_id": self.rec["id"]})
        msgs = _session["messages"]
        self.assertEqual(len(msgs), 1)
        self.assertIn(self.rec["merchant_name"], msgs[0]["content"])

    def test_status_changes_to_pending_submit(self):
        demo_actions.handle_demo_action(
            "retry_process", {"record_id": self.rec["id"]})
        rec = demo_actions.get_record(self.rec["id"])
        self.assertEqual(rec["status"], STATUS_PENDING_SUBMIT)

    def test_no_duplicate_on_repeat(self):
        demo_actions.handle_demo_action(
            "retry_process", {"record_id": self.rec["id"]})
        demo_actions.handle_demo_action(
            "retry_process", {"record_id": self.rec["id"]})
        msgs = _session["messages"]
        self.assertEqual(len(msgs), 1)


class TestSubmitSupplementLinkage(unittest.TestCase):
    """After submitting supplement material, chat gets a result message."""

    def setUp(self):
        _fresh_state()
        self.rec = _find_record_by_status(
            _session["reimbursement_records"], STATUS_PENDING_RECEIPT)
        _session["selected_record_id"] = self.rec["id"]
        _session["supplement_form"] = {
            "invoice_uploaded": True,
            "invoice_name": "test_invoice.pdf",
            "receipt_uploaded": False,
            "receipt_name": "",
            "note": "",
            "expense_type": "差旅住宿",
        }

    def test_message_appended_to_chat(self):
        demo_actions.handle_demo_action("submit_supplement")
        msgs = _session["messages"]
        self.assertEqual(len(msgs), 1)
        self.assertIn(self.rec["merchant_name"], msgs[0]["content"])

    def test_status_changes_to_pending_submit(self):
        demo_actions.handle_demo_action("submit_supplement")
        rec = demo_actions.get_record(self.rec["id"])
        self.assertEqual(rec["status"], STATUS_PENDING_SUBMIT)

    def test_navigates_to_detail(self):
        _session["current_phone_page"] = "supplement_material"
        demo_actions.handle_demo_action("submit_supplement")
        self.assertEqual(_session["current_phone_page"], "reimbursement_detail")

    def test_no_duplicate_on_repeat(self):
        demo_actions.handle_demo_action("submit_supplement")
        demo_actions.handle_demo_action("submit_supplement")
        msgs = _session["messages"]
        self.assertEqual(len(msgs), 1, "Should not duplicate message on repeat action")


class TestResetClearsLinkageState(unittest.TestCase):
    """reset_demo should clear H5 linkage tracking."""

    def setUp(self):
        _fresh_state()
        self.rec = _find_record_by_status(
            _session["reimbursement_records"], STATUS_PENDING_SUBMIT)

    def test_reset_clears_h5_completed_actions(self):
        _session["h5_completed_actions"] = {"confirm_submit:record_001": True}
        demo_state.reset_demo()
        self.assertEqual(_session.get("h5_completed_actions", {}), {})

    def test_action_works_again_after_reset(self):
        _session["selected_record_id"] = self.rec["id"]
        demo_actions.handle_demo_action("confirm_submit")
        self.assertEqual(len(_session["messages"]), 1)
        # Reset
        demo_state.reset_demo()
        _session["reimbursement_records"] = get_default_records()
        _session["h5_completed_actions"] = {}
        # Should be able to fire again
        _session["selected_record_id"] = self.rec["id"]
        demo_actions.handle_demo_action("confirm_submit")
        self.assertEqual(len(_session["messages"]), 1)


class TestH5CompletedActionsIsDict(unittest.TestCase):
    """h5_completed_actions should be a dict, not a set."""

    def test_initial_type_is_dict(self):
        _fresh_state()
        self.assertIsInstance(_session["h5_completed_actions"], dict)

    def test_compat_migration_from_set(self):
        _fresh_state()
        # Simulate old set data
        _session["h5_completed_actions"] = {"key1", "key2"}
        # Re-init should migrate
        demo_actions.init_full_state()
        self.assertIsInstance(demo_actions.st.session_state["h5_completed_actions"], dict)
        self.assertTrue(demo_actions.st.session_state["h5_completed_actions"].get("key1"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
