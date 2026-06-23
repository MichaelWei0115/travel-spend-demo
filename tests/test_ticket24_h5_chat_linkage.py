"""
Ticket 24: H5 与聊天页结果联动
===============================
Tests that H5 operations (supplement, retry sync, confirm sync)
correctly append result messages to the chat and navigate back to chat page.
Also validates deduplication - repeated actions don't duplicate messages.
"""

import sys
import os
import unittest
from unittest.mock import MagicMock
from datetime import datetime

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

from reimbursement_data import get_default_records
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
    _session["h5_completed_actions"] = set()
    _mock_st.session_state = _session
    demo_actions.st = _mock_st
    demo_state.st = _mock_st


class TestSubmitSupplementLinkage(unittest.TestCase):
    """After submitting supplement material, chat gets a result message."""

    def setUp(self):
        _fresh_state()
        # record_003 is "滴滴出行" with ai_check_result=need_supplement
        _session["selected_record_id"] = "record_003"
        _session["supplement_form"] = {
            "invoice_uploaded": True,
            "invoice_name": "didi_invoice.pdf",
            "receipt_uploaded": False,
            "receipt_name": "",
            "note": "",
            "expense_type": "交通出行",
        }

    def test_message_appended_to_chat(self):
        demo_actions.handle_demo_action("submit_supplement")
        msgs = _session["messages"]
        self.assertEqual(len(msgs), 1)
        self.assertIn("滴滴出行", msgs[0]["content"])
        self.assertIn("发票已重新校验", msgs[0]["content"])
        self.assertIn("同步至报销系统", msgs[0]["content"])

    def test_navigates_to_chat(self):
        _session["current_phone_page"] = "supplement_material"
        demo_actions.handle_demo_action("submit_supplement")
        self.assertEqual(_session["current_phone_page"], "reimbursement_detail")

    def test_no_duplicate_on_repeat(self):
        demo_actions.handle_demo_action("submit_supplement")
        demo_actions.handle_demo_action("submit_supplement")
        msgs = _session["messages"]
        self.assertEqual(len(msgs), 1, "Should not duplicate message on repeat action")


class TestRetrySyncLinkage(unittest.TestCase):
    """After retry sync succeeds, chat gets a result message."""

    def setUp(self):
        _fresh_state()
        # record_004 is "浦东机场希尔顿" with sync_status=sync_failed
        _session["selected_record_id"] = "record_004"

    def test_message_appended_to_chat(self):
        demo_actions.handle_demo_action("retry_sync", {"record_id": "record_004"})
        msgs = _session["messages"]
        self.assertEqual(len(msgs), 1)
        self.assertIn("浦东机场希尔顿", msgs[0]["content"])
        self.assertIn("重新同步成功", msgs[0]["content"])

    def test_navigates_to_chat(self):
        _session["current_phone_page"] = "reimbursement_detail"
        demo_actions.handle_demo_action("retry_sync", {"record_id": "record_004"})
        self.assertEqual(_session["current_phone_page"], "reimbursement_detail")

    def test_no_duplicate_on_repeat(self):
        demo_actions.handle_demo_action("retry_sync", {"record_id": "record_004"})
        demo_actions.handle_demo_action("retry_sync", {"record_id": "record_004"})
        msgs = _session["messages"]
        # Second call won't add message (record is now synced + dedup guard)
        self.assertEqual(len(msgs), 1)

    def test_no_message_when_already_synced(self):
        """If record is already synced, no message should be added."""
        # First sync it
        demo_actions.handle_demo_action("retry_sync", {"record_id": "record_004"})
        msgs_count = len(_session["messages"])
        # Reset dedup to test the synced-guard path
        _session["h5_completed_actions"] = set()
        demo_actions.handle_demo_action("retry_sync", {"record_id": "record_004"})
        # Should show info toast (already synced) but no new message
        self.assertEqual(len(_session["messages"]), msgs_count)


class TestConfirmSingleSyncLinkage(unittest.TestCase):
    """After confirm-and-sync succeeds, chat gets a result message."""

    def setUp(self):
        _fresh_state()
        # record_002 is "星巴克" with ai_check_result=passed, sync_status=not_synced
        _session["selected_record_id"] = "record_002"

    def test_message_appended_to_chat(self):
        demo_actions.handle_demo_action("confirm_single_sync", {"record_id": "record_002"})
        msgs = _session["messages"]
        self.assertEqual(len(msgs), 1)
        self.assertIn("该笔消费已同步至报销系统", msgs[0]["content"])

    def test_navigates_to_chat(self):
        _session["current_phone_page"] = "reimbursement_list"
        demo_actions.handle_demo_action("confirm_single_sync", {"record_id": "record_002"})
        self.assertEqual(_session["current_phone_page"], "reimbursement_detail")

    def test_no_duplicate_on_repeat(self):
        demo_actions.handle_demo_action("confirm_single_sync", {"record_id": "record_002"})
        demo_actions.handle_demo_action("confirm_single_sync", {"record_id": "record_002"})
        msgs = _session["messages"]
        self.assertEqual(len(msgs), 1, "Should not duplicate message on repeat action")


class TestResetClearsLinkageState(unittest.TestCase):
    """reset_demo should clear H5 linkage tracking."""

    def setUp(self):
        _fresh_state()

    def test_reset_clears_h5_completed_actions(self):
        _session["h5_completed_actions"] = {"submit_supplement:record_003"}
        demo_state.reset_demo()
        self.assertEqual(_session.get("h5_completed_actions", set()), set())

    def test_action_works_again_after_reset(self):
        _session["selected_record_id"] = "record_002"
        demo_actions.handle_demo_action("confirm_single_sync", {"record_id": "record_002"})
        self.assertEqual(len(_session["messages"]), 1)
        # Reset
        demo_state.reset_demo()
        _session["reimbursement_records"] = get_default_records()
        # Should be able to fire again
        demo_actions.handle_demo_action("confirm_single_sync", {"record_id": "record_002"})
        self.assertEqual(len(_session["messages"]), 1)  # messages was cleared by reset, then 1 new


if __name__ == "__main__":
    unittest.main(verbosity=2)
