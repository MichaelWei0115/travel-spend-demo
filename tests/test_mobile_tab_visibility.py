"""
Mobile Tab Panel Visibility Regression Tests
=============================================
Ensure mobile @media rules:
1. Never hide tab-panels via nth-child+display:none (caused grey screen)
2. Hide AI Lab / eval panels by explicit container key
3. Tab-panels remain generally visible
4. Tab-list and side_panel can be hidden
5. No 100vh on content containers (shell may use 100svh)
6. No overflow:hidden on inner scrollable content areas without flex
"""

import re
import unittest

TARGET_FILES = ["phone_shell.py", "phone_ui.py"]

CONTENT_CONTAINERS = [".st-key-phone_app", ".phone-app-v2", ".phone-body", ".phone-body.has-bottom-cta"]


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

    def test_ai_lab_panel_hidden_on_mobile(self):
        """Mobile CSS should hide AI Lab panel by explicit container key."""
        for fname in TARGET_FILES:
            content = self._read_file(fname)
            blocks = _extract_mobile_blocks(content)
            found = False
            for block in blocks:
                if "desktop_ai_lab_panel" in block and "display:none" in block:
                    found = True
            self.assertTrue(
                found,
                f"{fname}: mobile CSS should hide .st-key-desktop_ai_lab_panel"
            )

    def test_eval_observe_panel_hidden_on_mobile(self):
        """Mobile CSS should hide eval/observe panel by explicit container key."""
        for fname in TARGET_FILES:
            content = self._read_file(fname)
            blocks = _extract_mobile_blocks(content)
            found = False
            for block in blocks:
                if "desktop_eval_observe_panel" in block and "display:none" in block:
                    found = True
            self.assertTrue(
                found,
                f"{fname}: mobile CSS should hide .st-key-desktop_eval_observe_panel"
            )

    def test_mobile_tab_list_can_be_hidden(self):
        """Mobile CSS should hide the tab-list header."""
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
        """Mobile CSS should hide .st-key-side_panel."""
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

    def test_no_100vh_on_content_containers(self):
        """Inner content containers must not use height:100vh (use 100svh)."""
        dangerous = re.compile(r"height\s*:\s*100vh")
        for fname in TARGET_FILES:
            content = self._read_file(fname)
            blocks = _extract_mobile_blocks(content)
            for block in blocks:
                for container in CONTENT_CONTAINERS:
                    escaped = re.escape(container).replace(r"\-", "-")
                    container_pattern = re.compile(escaped + r"\s*\{([^}]*)\}")
                    for m in container_pattern.finditer(block):
                        body = m.group(1)
                        self.assertIsNone(
                            dangerous.search(body),
                            f"{fname}: {container} uses height:100vh (use 100svh)"
                        )

    def test_no_overflow_hidden_on_non_flex_content_containers(self):
        """Inner content containers must not use overflow:hidden without flex layout."""
        for fname in TARGET_FILES:
            content = self._read_file(fname)
            blocks = _extract_mobile_blocks(content)
            for block in blocks:
                for container in CONTENT_CONTAINERS:
                    escaped = re.escape(container).replace(r"\-", "-")
                    container_pattern = re.compile(escaped + r"\s*\{([^}]*)\}")
                    for m in container_pattern.finditer(block):
                        body = m.group(1)
                        if "overflow:hidden" in body and "display:flex" not in body:
                            self.fail(
                                f"{fname}: {container} uses overflow:hidden without display:flex"
                            )


if __name__ == "__main__":
    unittest.main()
