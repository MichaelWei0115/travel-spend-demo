"""
Ticket 21: Streamlit Native Flow Button Regression Protection
=============================================================
Regression test for all 18 flow-panel buttons in app.py.

Buttons tested:
  1. push_pending_receipt
  2. upload_receipt
  3. parse_receipt
  4. auto_fill
  5. sync_success
  6. amount_mismatch
  7. payment_failed
  8. full_main_flow
  9. reset_demo
  10. confirm_sync
  11. view_detail
  12. update_detail
  13. confirm_diff
  14. reupload
  15. apply_limit_increase
  16. view_travel_rules
  17. close_detail_panel
  18. close_rules_panel

Acceptance criteria:
- All 18 buttons invoke without error
- State transitions are correct
- Detail/rules panels open and close
- Flow panel state stays consistent
"""

import sys
import os
import unittest
from unittest.mock import MagicMock

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# Minimal Streamlit session_state mock
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


def _fresh_session_state():
    ss = _MockSessionState()
    ss["messages"] = []
    ss["demo_step"] = 0
    ss["current_task_state"] = "idle"
    ss["active_modal"] = None
    ss["current_page"] = "chat"
    ss["previous_page"] = "chat"
    ss["reimbursement_records"] = []
    ss["record_filter"] = "all"
    ss["selected_record_id"] = None
    ss["supplement_form"] = {}
    ss["toast_message"] = ""
    ss["loading_action"] = None
    ss["event_log"] = []
    ss["ai_responses"] = []
    ss["lab_config"] = {}
    ss["chat_messages"] = []
    return ss


# Patch streamlit before importing demo modules
_mock_st = MagicMock()
_session = _fresh_session_state()
_mock_st.session_state = _session

sys.modules.setdefault("streamlit", _mock_st)
sys.modules.setdefault("streamlit.components", MagicMock())
sys.modules.setdefault("streamlit.components.v1", MagicMock())

import importlib

if "demo_state" in sys.modules:
    importlib.reload(sys.modules["demo_state"])
else:
    import demo_state

from demo_state import (
    append_message, reset_demo,
    run_step_push_pending_receipt, run_step_upload_receipt,
    run_step_parse_receipt, run_step_auto_fill, run_step_sync_success,
    run_flow_amount_mismatch, run_flow_payment_failed, run_full_main_flow,
    handle_confirm_sync, handle_view_detail, handle_update_detail, close_modal,
    handle_confirm_diff, handle_reupload, handle_apply_limit_increase,
    handle_view_travel_rules,
)


def _reset():
    ss = _fresh_session_state()
    _mock_st.session_state = ss
    import demo_state as _ds
    _ds.st.session_state = ss
    return ss


class TestMainFlowButtons(unittest.TestCase):

    def setUp(self):
        self.ss = _reset()

    def test_01_push_pending_receipt(self):
        run_step_push_pending_receipt()
        self.assertEqual(self.ss["demo_step"], 1)
        self.assertEqual(self.ss["current_task_state"], "pending_receipt")
        self.assertEqual(len(self.ss["messages"]), 2)
        self.assertEqual(self.ss["messages"][0]["type"], "time_chip")
        self.assertEqual(self.ss["messages"][1]["type"], "card")
        self.assertIn("fields", self.ss["messages"][1])
        self.assertIn("actions", self.ss["messages"][1])

    def test_02_upload_receipt(self):
        run_step_upload_receipt()
        self.assertEqual(self.ss["demo_step"], 2)
        self.assertEqual(self.ss["current_task_state"], "receipt_uploaded")
        self.assertEqual(len(self.ss["messages"]), 2)
        self.assertEqual(self.ss["messages"][0]["type"], "receipt_upload")
        self.assertEqual(self.ss["messages"][1]["type"], "text")

    def test_03_parse_receipt(self):
        run_step_parse_receipt()
        self.assertEqual(self.ss["demo_step"], 3)
        self.assertEqual(self.ss["current_task_state"], "parsing")
        self.assertEqual(len(self.ss["messages"]), 1)
        self.assertEqual(self.ss["messages"][0]["type"], "card")
        self.assertIn("hint", self.ss["messages"][0])

    def test_04_auto_fill(self):
        run_step_auto_fill()
        self.assertEqual(self.ss["demo_step"], 4)
        self.assertEqual(self.ss["current_task_state"], "auto_filled")
        self.assertEqual(len(self.ss["messages"]), 1)
        card = self.ss["messages"][0]
        self.assertEqual(card["type"], "card")
        self.assertIn("\u786e\u8ba4\u5e76\u540c\u6b65", card["actions"])
        self.assertIn("\u67e5\u770b/\u7f16\u8f91\u8be6\u60c5", card["actions"])

    def test_05_sync_success(self):
        run_step_sync_success()
        self.assertEqual(self.ss["demo_step"], 5)
        self.assertEqual(self.ss["current_task_state"], "synced")
        self.assertEqual(len(self.ss["messages"]), 1)
        card = self.ss["messages"][0]
        self.assertEqual(card["status"], "\u5df2\u540c\u6b65")


class TestExceptionFlowButtons(unittest.TestCase):

    def setUp(self):
        self.ss = _reset()

    def test_06_amount_mismatch(self):
        run_flow_amount_mismatch()
        self.assertEqual(self.ss["current_task_state"], "amount_mismatch")
        self.assertEqual(len(self.ss["messages"]), 2)
        card = self.ss["messages"][1]
        self.assertEqual(card["type"], "card")
        self.assertEqual(card["status"], "\u9700\u8981\u786e\u8ba4")
        self.assertIn("\u786e\u8ba4\u5dee\u5f02\u5408\u7406", card["actions"])
        self.assertIn("\u91cd\u65b0\u4e0a\u4f20", card["actions"])

    def test_07_payment_failed(self):
        run_flow_payment_failed()
        self.assertEqual(self.ss["current_task_state"], "payment_failed")
        self.assertEqual(len(self.ss["messages"]), 2)
        card = self.ss["messages"][1]
        self.assertEqual(card["type"], "card")
        self.assertEqual(card["status"], "\u652f\u4ed8\u5931\u8d25")
        self.assertIn("\u7533\u8bf7\u4e34\u65f6\u8c03\u989d", card["actions"])
        self.assertIn("\u67e5\u770b\u5dee\u65c5\u89c4\u5219", card["actions"])


class TestAuxiliaryButtons(unittest.TestCase):

    def setUp(self):
        self.ss = _reset()

    def test_08_full_main_flow(self):
        run_full_main_flow()
        self.assertEqual(self.ss["demo_step"], 5)
        self.assertEqual(self.ss["current_task_state"], "synced")
        self.assertGreaterEqual(len(self.ss["messages"]), 7)
        types = [m["type"] for m in self.ss["messages"]]
        self.assertIn("time_chip", types)
        self.assertIn("receipt_upload", types)
        self.assertIn("text", types)
        self.assertIn("card", types)

    def test_09_reset_demo(self):
        run_full_main_flow()
        self.assertGreater(len(self.ss["messages"]), 0)
        self.assertNotEqual(self.ss["demo_step"], 0)
        reset_demo()
        self.assertEqual(self.ss["messages"], [])
        self.assertEqual(self.ss["demo_step"], 0)
        self.assertEqual(self.ss["current_task_state"], "idle")
        self.assertIsNone(self.ss["active_modal"])


class TestCardButtonResponses(unittest.TestCase):

    def setUp(self):
        self.ss = _reset()

    def test_10_confirm_sync(self):
        handle_confirm_sync()
        self.assertEqual(self.ss["demo_step"], 5)
        self.assertEqual(self.ss["current_task_state"], "synced")
        self.assertEqual(len(self.ss["messages"]), 1)
        self.assertEqual(self.ss["messages"][0]["status"], "\u5df2\u540c\u6b65")

    def test_11_view_detail(self):
        handle_view_detail()
        self.assertEqual(self.ss["active_modal"], "expense_detail")

    def test_12_update_detail(self):
        handle_update_detail()
        self.assertEqual(len(self.ss["messages"]), 1)
        self.assertEqual(self.ss["messages"][0]["type"], "text")
        self.assertIn("Demo", self.ss["messages"][0]["content"])

    def test_13_confirm_diff(self):
        handle_confirm_diff()
        self.assertEqual(len(self.ss["messages"]), 1)
        self.assertIn("\u786e\u8ba4", self.ss["messages"][0]["content"])

    def test_14_reupload(self):
        handle_reupload()
        self.assertEqual(len(self.ss["messages"]), 1)
        self.assertIn("\u91cd\u65b0\u4e0a\u4f20", self.ss["messages"][0]["content"])

    def test_15_apply_limit_increase(self):
        handle_apply_limit_increase()
        self.assertEqual(len(self.ss["messages"]), 1)
        self.assertIn("\u8c03\u989d", self.ss["messages"][0]["content"])

    def test_16_view_travel_rules(self):
        handle_view_travel_rules()
        self.assertEqual(self.ss["active_modal"], "travel_rules")


class TestPanelOpenClose(unittest.TestCase):

    def setUp(self):
        self.ss = _reset()

    def test_17_close_detail_panel(self):
        handle_view_detail()
        self.assertEqual(self.ss["active_modal"], "expense_detail")
        close_modal()
        self.assertIsNone(self.ss["active_modal"])

    def test_18_close_rules_panel(self):
        handle_view_travel_rules()
        self.assertEqual(self.ss["active_modal"], "travel_rules")
        close_modal()
        self.assertIsNone(self.ss["active_modal"])


class TestFlowPanelStateConsistency(unittest.TestCase):

    def setUp(self):
        self.ss = _reset()

    def test_19_sequential_main_flow(self):
        steps = [
            (run_step_push_pending_receipt, 1, "pending_receipt"),
            (run_step_upload_receipt, 2, "receipt_uploaded"),
            (run_step_parse_receipt, 3, "parsing"),
            (run_step_auto_fill, 4, "auto_filled"),
            (run_step_sync_success, 5, "synced"),
        ]
        for fn, expected_step, expected_state in steps:
            fn()
            self.assertEqual(self.ss["demo_step"], expected_step,
                             f"After {fn.__name__}: demo_step should be {expected_step}")
            self.assertEqual(self.ss["current_task_state"], expected_state,
                             f"After {fn.__name__}: state should be {expected_state}")

    def test_20_reset_clears_exception_flow(self):
        run_flow_amount_mismatch()
        self.assertEqual(self.ss["current_task_state"], "amount_mismatch")
        reset_demo()
        self.assertEqual(self.ss["current_task_state"], "idle")
        self.assertEqual(self.ss["messages"], [])

    def test_21_modal_does_not_affect_flow_state(self):
        run_step_push_pending_receipt()
        msg_count = len(self.ss["messages"])
        step = self.ss["demo_step"]

        handle_view_detail()
        self.assertEqual(len(self.ss["messages"]), msg_count)
        self.assertEqual(self.ss["demo_step"], step)

        close_modal()
        self.assertEqual(len(self.ss["messages"]), msg_count)
        self.assertEqual(self.ss["demo_step"], step)

        handle_view_travel_rules()
        self.assertEqual(len(self.ss["messages"]), msg_count)
        self.assertEqual(self.ss["demo_step"], step)

        close_modal()
        self.assertEqual(len(self.ss["messages"]), msg_count)
        self.assertEqual(self.ss["demo_step"], step)

    def test_22_messages_only_append(self):
        run_step_push_pending_receipt()
        first_batch = list(self.ss["messages"])
        count_after_step1 = len(first_batch)

        run_step_upload_receipt()
        self.assertGreater(len(self.ss["messages"]), count_after_step1)
        for i, msg in enumerate(first_batch):
            self.assertEqual(self.ss["messages"][i], msg)


if __name__ == "__main__":
    unittest.main(verbosity=2)
