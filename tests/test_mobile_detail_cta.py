"""
Mobile Detail CTA Visibility Tests
====================================
Ensure detail page bottom CTA buttons are visible on mobile.
"""

import re
import unittest

TARGET_FILES = ["phone_ui.py"]


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


class TestMobileDetailCTA(unittest.TestCase):

    def _read_file(self, filename: str) -> str:
        import os
        filepath = os.path.join(os.path.dirname(__file__), "..", filename)
        with open(filepath) as f:
            return f.read()

    def test_phone_app_v2_is_flex_container(self):
        """Mobile .phone-app-v2 must be a flex column container with svh viewport."""
        for fname in TARGET_FILES:
            content = self._read_file(fname)
            blocks = _extract_mobile_blocks(content)
            found = False
            for block in blocks:
                pattern = re.compile(r"\.phone-app-v2\s*\{([^}]*)\}")
                for m in pattern.finditer(block):
                    body = m.group(1)
                    if "display:flex" in body and "flex-direction:column" in body and "100svh" in body:
                        found = True
            self.assertTrue(found, f"{fname}: .phone-app-v2 must be flex column with 100svh in mobile CSS")

    def test_phone_body_is_flex_grow(self):
        """Mobile .phone-body variants must use flex:1 for scrollable content."""
        for fname in TARGET_FILES:
            content = self._read_file(fname)
            blocks = _extract_mobile_blocks(content)
            found = False
            for block in blocks:
                if ".phone-body" in block and "flex:1" in block:
                    found = True
            self.assertTrue(found, f"{fname}: .phone-body must have flex:1 in mobile CSS")

    def test_phone_body_has_bottom_overrides_desktop_height(self):
        """Mobile .phone-body.has-bottom must override desktop fixed height."""
        for fname in TARGET_FILES:
            content = self._read_file(fname)
            blocks = _extract_mobile_blocks(content)
            found = False
            for block in blocks:
                if ".has-bottom" in block and "height:auto" in block:
                    found = True
            self.assertTrue(found, f"{fname}: .phone-body.has-bottom needs height:auto in mobile CSS")

    def test_bottom_cta_is_visible(self):
        """Mobile CSS must not hide .phone-bottom-cta with display:none."""
        for fname in TARGET_FILES:
            content = self._read_file(fname)
            blocks = _extract_mobile_blocks(content)
            for block in blocks:
                cta_pattern = re.compile(r"\.phone-bottom-cta\s*\{([^}]*)\}")
                for m in cta_pattern.finditer(block):
                    body = m.group(1)
                    self.assertNotIn("display:none", body,
                        f"{fname}: .phone-bottom-cta must not have display:none in mobile CSS")

    def test_bottom_bars_sticky_or_flex_shrink(self):
        """Mobile bottom bars must use flex-shrink:0 to stay visible."""
        for fname in TARGET_FILES:
            content = self._read_file(fname)
            blocks = _extract_mobile_blocks(content)
            found = False
            for block in blocks:
                if "phone-bottom" in block and "flex-shrink:0" in block:
                    found = True
            self.assertTrue(found, f"{fname}: .phone-bottom/-cta must have flex-shrink:0 in mobile CSS")

    def test_bottom_bars_not_fixed_height(self):
        """Mobile bottom bars must not use fixed pixel height (use height:auto)."""
        for fname in TARGET_FILES:
            content = self._read_file(fname)
            blocks = _extract_mobile_blocks(content)
            for block in blocks:
                for selector in [".phone-bottom", ".phone-action-bottom", ".phone-bottom-cta"]:
                    pattern = re.compile(re.escape(selector).replace(r"\-", "-") + r"\s*\{([^}]*)\}")
                    for m in pattern.finditer(block):
                        body = m.group(1)
                        self.assertNotRegex(body, r"height:\d+px",
                            f"{fname}: {selector} should not use fixed pixel height in mobile CSS")
                        self.assertIn("height:auto", body,
                            f"{fname}: {selector} should have height:auto in mobile CSS")


if __name__ == "__main__":
    unittest.main()
