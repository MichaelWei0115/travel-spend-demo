"""
Mobile Tab Panel Visibility Regression Tests
=============================================
Ensure mobile @media rules never hide tab-panels via nth-child+display:none,
which caused the "flash then grey screen" bug on real phones.

Checks:
1. No tab-panel:nth-child(...){display:none} in mobile CSS
2. Mobile tab-panels are explicitly visible (display:block; visibility:visible)
3. Mobile tab-list can still be hidden
4. Mobile side panel can still be hidden
5. Viewport fixes from previous round are intact
"""

import re
import unittest

TARGET_FILES = ["phone_shell.py", "phone_ui.py"]


def _extract_mobile_blocks(content: str) -> list[str]:
    """Extract text inside @media(max-width:768px) { ... } blocks."""
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


class TestMobileTabVisibility(unittest.TestCase):

    def _read_file(self, filename: str) -> str:
        import os
        filepath = os.path.join(os.path.dirname(__file__), "..", filename)
        with open(filepath) as f:
            return f.read()

    def test_no_tab_panel_nth_child_display_none(self):
        """Mobile CSS must NOT contain tab-panel:nth-child(...){display:none}."""
        dangerous = re.compile(
            r"\[data-baseweb=.tab-panel.\].*nth-child.*display\s*:\s*none",
            re.IGNORECASE,
        )
        for fname in TARGET_FILES:
            content = self._read_file(fname)
            blocks = _extract_mobile_blocks(content)
            for block in blocks:
                self.assertIsNone(
                    dangerous.search(block),
                    f"{fname}: mobile CSS contains tab-panel nth-child display:none"
                )

    def test_mobile_tab_panels_explicitly_visible(self):
        """Mobile CSS must make tab-panels explicitly visible."""
        for fname in TARGET_FILES:
            content = self._read_file(fname)
            blocks = _extract_mobile_blocks(content)
            found = False
            for block in blocks:
                panel_pattern = re.compile(
                    r'\.stTabs\s+\[data-baseweb="tab-panel"\]\s*\{([^}]*)\}'
                )
                for m in panel_pattern.finditer(block):
                    body = m.group(1)
                    if "display:block" in body.replace(" ", "") and "visibility:visible" in body.replace(" ", ""):
                        found = True
            self.assertTrue(
                found,
                f"{fname}: mobile CSS must include tab-panel display:block+visibility:visible"
            )

    def test_mobile_tab_list_can_be_hidden(self):
        """Mobile CSS may (and should) hide the tab-list header."""
        for fname in TARGET_FILES:
            content = self._read_file(fname)
            blocks = _extract_mobile_blocks(content)
            found = False
            for block in blocks:
                if 'tab-list' in block and 'display:none' in block:
                    found = True
            self.assertTrue(
                found,
                f"{fname}: mobile CSS should hide tab-list"
            )

    def test_mobile_side_panel_can_be_hidden(self):
        """Mobile CSS may hide .st-key-side_panel."""
        for fname in TARGET_FILES:
            content = self._read_file(fname)
            blocks = _extract_mobile_blocks(content)
            found = False
            for block in blocks:
                if 'side_panel' in block and 'display:none' in block:
                    found = True
            self.assertTrue(
                found,
                f"{fname}: mobile CSS should hide side_panel"
            )

    def test_viewport_fix_not_regressed(self):
        """Mobile main containers must not use 100vh + overflow:hidden combo."""
        dangerous_height = re.compile(r"height\s*:\s*100vh")
        dangerous_overflow = re.compile(r"overflow\s*:\s*hidden")
        main_containers = [".st-key-phone_shell", ".st-key-phone_app", ".phone-app-v2", ".phone-body"]

        for fname in TARGET_FILES:
            content = self._read_file(fname)
            blocks = _extract_mobile_blocks(content)
            for block in blocks:
                for container in main_containers:
                    escaped = re.escape(container).replace(r"\-", "-")
                    container_pattern = re.compile(escaped + r"\s*\{([^}]*)\}")
                    for m in container_pattern.finditer(block):
                        body = m.group(1)
                        self.assertIsNone(
                            dangerous_height.search(body),
                            f"{fname}: {container} still uses height:100vh in mobile CSS"
                        )
                        self.assertIsNone(
                            dangerous_overflow.search(body),
                            f"{fname}: {container} still uses overflow:hidden in mobile CSS"
                        )


if __name__ == "__main__":
    unittest.main()
