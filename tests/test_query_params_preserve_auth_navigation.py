"""
Query Params Auth Preservation Tests
======================================
Ensure all navigation routes preserve demo_authed=1.
"""

import unittest
import re


class TestAuthPreservationInForms(unittest.TestCase):
    """Verify that HTML GET forms in phone_ui.py include demo_authed hidden field."""

    def _read_file(self, filename: str) -> str:
        import os
        filepath = os.path.join(os.path.dirname(__file__), "..", filename)
        with open(filepath) as f:
            return f.read()

    def test_phone_action_form_preserves_auth(self):
        """phone_action_form() already preserves auth via AUTH_QUERY_KEY hidden field."""
        content = self._read_file("phone_ui.py")
        # phone_action_form should reference AUTH_QUERY_KEY
        self.assertIn("AUTH_QUERY_KEY", content)
        # It should generate hidden input with demo_authed
        self.assertIn('name="{AUTH_QUERY_KEY}"', content)

    def test_record_card_form_preserves_auth(self):
        """record-card-form must include _auth_hidden for demo_authed preservation."""
        content = self._read_file("phone_ui.py")
        # The record-card-form should use _auth_hidden
        self.assertIn("_auth_hidden", content)
        # _auth_hidden must be defined with AUTH_QUERY_KEY
        self.assertIn('_auth_hidden = f\'<input type="hidden" name="{AUTH_QUERY_KEY}" value="1">\'', content)

    def test_all_form_methods_preserve_auth(self):
        """All forms with method="get" must have a mechanism to preserve demo_authed."""
        content = self._read_file("phone_ui.py")
        # Count forms with method="get"
        form_count = len(re.findall(r'<form[^>]*method="get"', content))
        self.assertGreater(form_count, 0, "Should have at least one GET form")
        
        # phone_action_form uses AUTH_QUERY_KEY (covers most forms)
        self.assertIn("phone_action_form", content)
        # record-card-form uses _auth_hidden
        self.assertIn("record-card-form", content)
        self.assertIn("{_auth_hidden}", content)

    def test_no_direct_query_params_clear(self):
        """Business files should not directly clear query params."""
        for fname in ["phone_ui.py", "demo_actions.py", "h5_pages.py"]:
            try:
                content = self._read_file(fname)
            except FileNotFoundError:
                continue
            # Should not have st.query_params.clear() in business files
            # (only query_params.py is allowed to do this internally)
            self.assertNotIn("st.query_params.clear()", content,
                f"{fname} should not call st.query_params.clear() directly")


class TestSetQueryParamsPreservingAuth(unittest.TestCase):
    """Verify set_query_params_preserving_auth is used for navigation."""

    def _read_file(self, filename: str) -> str:
        import os
        filepath = os.path.join(os.path.dirname(__file__), "..", filename)
        with open(filepath) as f:
            return f.read()

    def test_phone_ui_uses_preserving_auth(self):
        """phone_ui.py should import and use set_query_params_preserving_auth."""
        content = self._read_file("phone_ui.py")
        self.assertIn("set_query_params_preserving_auth", content)

    def test_demo_actions_uses_preserving_auth(self):
        """demo_actions.py should import and use set_query_params_preserving_auth."""
        content = self._read_file("demo_actions.py")
        self.assertIn("set_query_params_preserving_auth", content)


if __name__ == "__main__":
    unittest.main()
