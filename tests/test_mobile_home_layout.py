"""
Mobile Home Layout Regression Tests
====================================
Ensure mobile chat home page has proper chat-app layout:
- Shell uses svh viewport with flex column layout
- Chat body area is scrollable (flex:1 + overflow-y:auto)
- Bottom bar is sticky/pinned to bottom
- Safe-area-inset-bottom padding for notched phones
- PC phone shell (390x867) styles are untouched
"""

import re
import unittest

TARGET_FILES = ["phone_shell.py", "phone_ui.py"]


def _extract_mobile_blocks(content: str) -> list[str]:
    blocks = []
    pattern = re.compile(r"@media\s*\(\s*max-width\s*:\s*768px\s*\)\s*\{")
    for m in pattern.finditer(content):
        start = m.end()
        depth = 1
        i = start
        while i < len(content) and depth > 0:
            if content[i] == "{":
                depth += 1
            elif content[i] == "}":
                depth -= 1
            i += 1
        blocks.append(content[start:i - 1])
    return blocks


class TestMobileHomeLayout(unittest.TestCase):

    def _read_file(self, filename: str) -> str:
        import os
        filepath = os.path.join(os.path.dirname(__file__), "..", filename)
        with open(filepath) as f:
            return f.read()

    def test_phone_shell_uses_flex_layout(self):
        """Mobile phone_shell should use display:flex + flex-direction:column."""
        for fname in TARGET_FILES:
            content = self._read_file(fname)
            blocks = _extract_mobile_blocks(content)
            found = False
            for block in blocks:
                shell_pattern = re.compile(r"\.st-key-phone_shell\s*\{([^}]*)\}")
                for m in shell_pattern.finditer(block):
                    body = m.group(1)
                    if "display:flex" in body and "flex-direction:column" in body:
                        found = True
            self.assertTrue(
                found,
                f"{fname}: .st-key-phone_shell should use display:flex+flex-direction:column in mobile CSS"
            )

    def test_chat_body_area_is_flex_and_scrollable(self):
        """Mobile chat_body_area should use flex:1 + overflow-y:auto."""
        for fname in ["phone_shell.py"]:
            content = self._read_file(fname)
            blocks = _extract_mobile_blocks(content)
            found = False
            for block in blocks:
                body_pattern = re.compile(r"\.st-key-chat_body_area\s*\{([^}]*)\}")
                for m in body_pattern.finditer(block):
                    body = m.group(1)
                    if "flex:1" in body and "overflow-y:auto" in body:
                        found = True
            self.assertTrue(
                found,
                f"{fname}: .st-key-chat_body_area should have flex:1+overflow-y:auto in mobile CSS"
            )

    def test_bottom_bar_is_sticky(self):
        """Mobile chat_bottom_bar should have position:sticky + bottom:0."""
        for fname in ["phone_shell.py"]:
            content = self._read_file(fname)
            blocks = _extract_mobile_blocks(content)
            found = False
            for block in blocks:
                bar_pattern = re.compile(r"\.st-key-chat_bottom_bar\s*\{([^}]*)\}")
                for m in bar_pattern.finditer(block):
                    body = m.group(1)
                    if "position:sticky" in body and "bottom:0" in body:
                        found = True
            self.assertTrue(
                found,
                f"{fname}: .st-key-chat_bottom_bar should have position:sticky+bottom:0 in mobile CSS"
            )

    def test_bottom_bar_has_safe_area_padding(self):
        """Mobile bottom bar should include safe-area-inset-bottom for notched phones."""
        for fname in ["phone_shell.py"]:
            content = self._read_file(fname)
            blocks = _extract_mobile_blocks(content)
            found = False
            for block in blocks:
                bar_pattern = re.compile(r"\.st-key-chat_bottom_bar\s*\{([^}]*)\}")
                for m in bar_pattern.finditer(block):
                    body = m.group(1)
                    if "safe-area-inset-bottom" in body:
                        found = True
            self.assertTrue(
                found,
                f"{fname}: .st-key-chat_bottom_bar should have safe-area-inset-bottom in mobile CSS"
            )

    def test_phone_body_is_flex_and_scrollable(self):
        """Mobile phone-body in phone_ui should use flex:1 + overflow-y:auto."""
        for fname in ["phone_ui.py"]:
            content = self._read_file(fname)
            blocks = _extract_mobile_blocks(content)
            found = False
            for block in blocks:
                # The rule may be a combined selector like .phone-body,.phone-body.has-bottom,...
                if ".phone-body" in block and "flex:1" in block and "overflow-y:auto" in block:
                    found = True
            self.assertTrue(
                found,
                f"{fname}: .phone-body should have flex:1+overflow-y:auto in mobile CSS"
            )

    def test_phone_bottom_sticky_in_phone_ui(self):
        """Mobile phone-bottom should be sticky in phone_ui."""
        for fname in ["phone_ui.py"]:
            content = self._read_file(fname)
            blocks = _extract_mobile_blocks(content)
            found = False
            for block in blocks:
                if "phone-bottom" in block and "position:sticky" in block:
                    found = True
            self.assertTrue(
                found,
                f"{fname}: .phone-bottom should have position:sticky in mobile CSS"
            )

    def test_pc_phone_shell_untouched(self):
        """PC (desktop) phone shell should still use 390x867 fixed dimensions."""
        content = self._read_file("phone_shell.py")
        self.assertIn("--phone-w:390px", content)
        self.assertIn("--phone-h:867px", content)


if __name__ == "__main__":
    unittest.main()
