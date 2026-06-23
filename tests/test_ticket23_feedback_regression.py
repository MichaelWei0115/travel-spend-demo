"""
Ticket 23: Unified Toast, Loading, Modal, Empty State & Mobile UX
=================================================================
Tests that the feedback system works correctly and integrates with
existing components without breaking them.
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
_session["toast_message"] = ""
_session["loading_action"] = None
_mock_st.session_state = _session

# Must set streamlit BEFORE importing feedback
sys.modules["streamlit"] = _mock_st
sys.modules.setdefault("streamlit.components", MagicMock())
sys.modules.setdefault("streamlit.components.v1", MagicMock())

import feedback
# Ensure feedback module uses our mock st
feedback.st = _mock_st

from feedback import (
    FEEDBACK_CSS,
    inject_feedback_styles,
    render_empty_state,
    simulate_async,
    render_confirm,
    show_success_toast,
    show_error_toast,
    show_info_toast,
    with_loading,
)


def _ensure_session():
    """Ensure _mock_st.session_state is our shared _session."""
    _mock_st.session_state = _session
    feedback.st = _mock_st


class TestFeedbackCSS(unittest.TestCase):
    """Verify the CSS content is well-formed and covers requirements."""

    def test_css_not_empty(self):
        self.assertGreater(len(FEEDBACK_CSS), 100)

    def test_contains_44px_mobile_button(self):
        self.assertIn("44px", FEEDBACK_CSS)
        self.assertIn("min-height", FEEDBACK_CSS)

    def test_contains_safe_area(self):
        self.assertIn("safe-area-inset-bottom", FEEDBACK_CSS)

    def test_contains_button_active_state(self):
        self.assertIn(":active", FEEDBACK_CSS)
        self.assertIn("scale(0.97)", FEEDBACK_CSS)

    def test_contains_disabled_state(self):
        self.assertIn(":disabled", FEEDBACK_CSS)
        self.assertIn("not-allowed", FEEDBACK_CSS)

    def test_contains_toast_positioning(self):
        self.assertIn("stToast", FEEDBACK_CSS)
        self.assertIn("bottom", FEEDBACK_CSS)

    def test_contains_empty_state_class(self):
        self.assertIn("empty-state", FEEDBACK_CSS)

    def test_contains_confirm_box(self):
        self.assertIn("confirm-box", FEEDBACK_CSS)

    def test_contains_filter_scroll(self):
        self.assertIn("filter-scroll-container", FEEDBACK_CSS)
        self.assertIn("overflow-x: auto", FEEDBACK_CSS)

    def test_inject_feedback_styles_callable(self):
        inject_feedback_styles()
        _mock_st.html.assert_called()

    def test_44px_inside_mobile_media_query(self):
        idx = FEEDBACK_CSS.find("@media (max-width: 519px)")
        self.assertGreater(idx, 0)
        media_section = FEEDBACK_CSS[idx:]
        self.assertIn("44px", media_section)

    def test_button_transition_for_click_feedback(self):
        self.assertIn("transition", FEEDBACK_CSS)
        self.assertIn("transform", FEEDBACK_CSS)


class TestEmptyState(unittest.TestCase):

    def test_renders_with_defaults(self):
        _ensure_session()
        render_empty_state()
        call_args = _mock_st.markdown.call_args
        html = call_args[0][0]
        self.assertIn("empty-state", html)
        self.assertIn("\U0001f4ed", html)

    def test_renders_with_custom_params(self):
        _ensure_session()
        render_empty_state("\U0001f50d", "No records found")
        call_args = _mock_st.markdown.call_args
        html = call_args[0][0]
        self.assertIn("\U0001f50d", html)
        self.assertIn("No records found", html)


class TestToastHelpers(unittest.TestCase):

    def setUp(self):
        _ensure_session()
        _session["toast_message"] = ""

    def test_success_toast(self):
        show_success_toast("Done!")
        self.assertIn("\u2705", _mock_st.session_state.toast_message)
        self.assertIn("Done!", _mock_st.session_state.toast_message)

    def test_error_toast(self):
        show_error_toast("Failed!")
        self.assertIn("\u274c", _mock_st.session_state.toast_message)
        self.assertIn("Failed!", _mock_st.session_state.toast_message)

    def test_info_toast(self):
        show_info_toast("FYI")
        self.assertIn("\u2139\ufe0f", _mock_st.session_state.toast_message)
        self.assertIn("FYI", _mock_st.session_state.toast_message)

    def test_toast_does_not_accumulate(self):
        show_success_toast("First")
        show_error_toast("Second")
        self.assertIn("Second", _mock_st.session_state.toast_message)
        self.assertNotIn("First", _mock_st.session_state.toast_message)

    def test_toast_prefixes_are_distinct(self):
        show_success_toast("msg")
        success_msg = _mock_st.session_state.toast_message
        show_error_toast("msg")
        error_msg = _mock_st.session_state.toast_message
        show_info_toast("msg")
        info_msg = _mock_st.session_state.toast_message
        self.assertNotEqual(success_msg, error_msg)
        self.assertNotEqual(error_msg, info_msg)


class TestLoadingSimulation(unittest.TestCase):

    def test_simulate_async_callable(self):
        _ensure_session()
        simulate_async("Loading...", 0.01)

    def test_with_loading_returns_spinner(self):
        _ensure_session()
        ctx = with_loading("Processing...")
        self.assertIsNotNone(ctx)


class TestConfirmDialog(unittest.TestCase):

    def test_renders_without_error(self):
        _ensure_session()
        mock_col1 = MagicMock()
        mock_col2 = MagicMock()
        mock_col1.__enter__ = MagicMock(return_value=mock_col1)
        mock_col1.__exit__ = MagicMock(return_value=False)
        mock_col2.__enter__ = MagicMock(return_value=mock_col2)
        mock_col2.__exit__ = MagicMock(return_value=False)
        _mock_st.columns.return_value = [mock_col1, mock_col2]
        _mock_st.button.return_value = False

        result = render_confirm(
            "Are you sure?",
            confirm_key="test_confirm",
            cancel_key="test_cancel",
        )
        self.assertEqual(result, "")

    def test_confirm_message_rendered(self):
        _ensure_session()
        mock_col1 = MagicMock()
        mock_col2 = MagicMock()
        mock_col1.__enter__ = MagicMock(return_value=mock_col1)
        mock_col1.__exit__ = MagicMock(return_value=False)
        mock_col2.__enter__ = MagicMock(return_value=mock_col2)
        mock_col2.__exit__ = MagicMock(return_value=False)
        _mock_st.columns.return_value = [mock_col1, mock_col2]
        _mock_st.button.return_value = False

        render_confirm("Delete this?", "c_key", "x_key")
        found = False
        for call in _mock_st.markdown.call_args_list:
            if "Delete this?" in str(call):
                found = True
                break
        self.assertTrue(found)


class TestCSSDoesNotBreakExistingStyles(unittest.TestCase):

    def test_no_global_font_size_override(self):
        parts = FEEDBACK_CSS.split("@media")
        base_css = parts[0]
        if ".stButton > button {" in base_css:
            btn_block = base_css.split(".stButton > button {")[1].split("}")[0]
            self.assertNotIn("font-size", btn_block)


class TestModuleImports(unittest.TestCase):

    def test_feedback_module_importable(self):
        self.assertTrue(hasattr(feedback, 'inject_feedback_styles'))
        self.assertTrue(hasattr(feedback, 'render_empty_state'))
        self.assertTrue(hasattr(feedback, 'simulate_async'))
        self.assertTrue(hasattr(feedback, 'render_confirm'))
        self.assertTrue(hasattr(feedback, 'show_success_toast'))
        self.assertTrue(hasattr(feedback, 'show_error_toast'))
        self.assertTrue(hasattr(feedback, 'show_info_toast'))

    def test_demo_actions_importable(self):
        import demo_actions
        self.assertTrue(hasattr(demo_actions, 'handle_demo_action'))
        self.assertTrue(hasattr(demo_actions, 'render_toast'))

    def test_h5_pages_importable(self):
        import h5_pages
        self.assertTrue(hasattr(h5_pages, 'render_h5_page'))


class TestExistingRegressionStillPasses(unittest.TestCase):

    def setUp(self):
        _ensure_session()
        import demo_state as _ds
        ss = _MockSessionState()
        ss["messages"] = []
        ss["demo_step"] = 0
        ss["current_task_state"] = "idle"
        ss["active_modal"] = None
        _mock_st.session_state = ss
        _ds.st.session_state = ss
        self.ss = ss

    def test_flow_buttons_still_work(self):
        from demo_state import (
            run_step_push_pending_receipt, run_step_upload_receipt,
            run_step_parse_receipt, run_step_auto_fill, run_step_sync_success,
            reset_demo,
        )
        run_step_push_pending_receipt()
        self.assertEqual(self.ss["demo_step"], 1)
        run_step_upload_receipt()
        self.assertEqual(self.ss["demo_step"], 2)
        run_step_parse_receipt()
        self.assertEqual(self.ss["demo_step"], 3)
        run_step_auto_fill()
        self.assertEqual(self.ss["demo_step"], 4)
        run_step_sync_success()
        self.assertEqual(self.ss["demo_step"], 5)
        reset_demo()
        self.assertEqual(self.ss["demo_step"], 0)
        self.assertEqual(self.ss["messages"], [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
