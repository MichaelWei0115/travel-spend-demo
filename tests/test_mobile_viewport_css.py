"""
Mobile Viewport CSS Regression Tests
=====================================
Ensure mobile @media rules use correct chat-app layout patterns:
- Outer shell (phone_shell) uses svh-based viewport sizing + flex layout
- Inner content areas use flex:1 + overflow-y:auto for scrollability
- Bottom bars use flex-shrink:0 + sticky positioning
- No 100vh (use 100svh instead for mobile address bar safety)
- No overflow:hidden on inner scrollable content areas
"""

import re
import unittest

TARGET_FILES = ["phone_shell.py", "phone_ui.py"]

# Outer shell containers: allowed to have overflow:hidden + max-height:svh
SHELL_CONTAINERS = [".st-key-phone_shell"]

# Inner content containers: must NOT have overflow:hidden
CONTENT_CONTAINERS = [".st-key-phone_app", ".phone-app-v2", ".phone-body", ".phone-body.has-bottom-cta"]

# Containers that must be scrollable
SCROLLABLE_CONTAINERS = [".st-key-chat_body_area", ".phone-body", ".phone-body.has-bottom-cta"]


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


class TestMobileViewportCSS(unittest.TestCase):

    def _read_file(self, filename: str) -> str:
        import os
        filepath = os.path.join(os.path.dirname(__file__), "..", filename)
        with open(filepath) as f:
            return f.read()

    def test_no_100vh_on_main_containers(self):
        """No main container should use height:100vh in mobile CSS (use 100svh instead)."""
        dangerous = re.compile(r"height\s*:\s*100vh")
        for fname in TARGET_FILES:
            content = self._read_file(fname)
            blocks = _extract_mobile_blocks(content)
            for block in blocks:
                for container in SHELL_CONTAINERS + CONTENT_CONTAINERS:
                    escaped = re.escape(container).replace(r"\-", "-")
                    container_pattern = re.compile(escaped + r"\s*\{([^}]*)\}")
                    for rule_match in container_pattern.finditer(block):
                        rule_body = rule_match.group(1)
                        self.assertIsNone(
                            dangerous.search(rule_body),
                            f"{fname}: {container} uses height:100vh in mobile CSS (use 100svh)"
                        )

    def test_shell_uses_svh_viewport(self):
        """Outer shell should use 100svh-based viewport sizing with flex layout."""
        for fname in TARGET_FILES:
            content = self._read_file(fname)
            blocks = _extract_mobile_blocks(content)
            found_svh = False
            for block in blocks:
                shell_pattern = re.compile(r"\.st-key-phone_shell\s*\{([^}]*)\}")
                for m in shell_pattern.finditer(block):
                    body = m.group(1)
                    if "100svh" in body and "display:flex" in body:
                        found_svh = True
            self.assertTrue(
                found_svh,
                f"{fname}: .st-key-phone_shell should use 100svh + display:flex in mobile CSS"
            )

    def test_inner_content_containers_no_overflow_hidden(self):
        """Inner content containers must NOT use overflow:hidden without flex layout.

        overflow:hidden is acceptable on flex column containers (display:flex + overflow:hidden)
        because they act as bounded flex parents where children handle their own scrolling.
        overflow:hidden is dangerous only when used without any flex structure.
        """
        for fname in TARGET_FILES:
            content = self._read_file(fname)
            blocks = _extract_mobile_blocks(content)
            for block in blocks:
                for container in CONTENT_CONTAINERS:
                    escaped = re.escape(container).replace(r"\-", "-")
                    container_pattern = re.compile(escaped + r"\s*\{([^}]*)\}")
                    for rule_match in container_pattern.finditer(block):
                        rule_body = rule_match.group(1)
                        has_overflow_hidden = "overflow:hidden" in rule_body
                        has_flex = "display:flex" in rule_body or "flex:1" in rule_body
                        if has_overflow_hidden and not has_flex:
                            self.fail(
                                f"{fname}: {container} uses overflow:hidden without flex layout in mobile CSS"
                            )

    def test_scrollable_containers_have_overflow_auto(self):
        """Content areas that should scroll must have overflow-y:auto."""
        for fname in ["phone_shell.py"]:
            content = self._read_file(fname)
            blocks = _extract_mobile_blocks(content)
            found = False
            for block in blocks:
                chat_pattern = re.compile(r"\.st-key-chat_body_area\s*\{([^}]*)\}")
                for m in chat_pattern.finditer(block):
                    body = m.group(1)
                    if "overflow-y:auto" in body:
                        found = True
            self.assertTrue(
                found,
                f"{fname}: .st-key-chat_body_area should have overflow-y:auto in mobile CSS"
            )

    def test_bottom_bar_sticky(self):
        """Chat bottom bar should be sticky at bottom."""
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
                f"{fname}: .st-key-chat_bottom_bar should have position:sticky + bottom:0 in mobile CSS"
            )


if __name__ == "__main__":
    unittest.main()
