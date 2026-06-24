"""
Ticket 25+: Mobile Viewport CSS Regression Tests
=================================================
Ensure mobile @media rules never reintroduce the 100vh+overflow:hidden
combo that caused white-screen on real phone browsers.

Checks:
1. No height:100vh or max-height:100vh on main containers inside @media(max-width:768px)
2. Mobile main containers use min-height:100svh (or 100dvh)
3. Mobile main containers have max-height:none
4. Mobile main containers use overflow:visible (shell/app) or overflow-y:auto (body)
"""

import re
import unittest

# Files that contain mobile CSS we care about
TARGET_FILES = ["phone_shell.py", "phone_ui.py"]

# Containers that must not have fixed-height/overflow cropping on mobile
MAIN_CONTAINERS = [
    "st-key-phone_shell",
    "st-key-phone_app",
    "phone-app-v2",
    "phone-body",
]

# Patterns that are dangerous on mobile main containers
DANGEROUS_HEIGHT = re.compile(r"height\s*:\s*100vh")
DANGEROUS_MAX_HEIGHT = re.compile(r"max-height\s*:\s*100vh")
DANGEROUS_OVERFLOW = re.compile(r"overflow\s*:\s*hidden")


def _extract_mobile_blocks(content: str) -> list[str]:
    """Extract text inside @media(max-width:768px) { ... } blocks."""
    # Handle nested braces by counting depth
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

    def test_mobile_css_no_100vh_on_main_containers(self):
        """Main containers inside @media(max-width:768px) must not use height:100vh."""
        for fname in TARGET_FILES:
            content = self._read_file(fname)
            blocks = _extract_mobile_blocks(content)
            for block in blocks:
                for container in MAIN_CONTAINERS:
                    # Find rules for this container within the block
                    # Match patterns like .container{...} or .container {...}
                    container_pattern = re.compile(
                        re.escape(container).replace(r"\-", r"-")
                        + r"\s*\{([^}]*)\}"
                    )
                    for rule_match in container_pattern.finditer(block):
                        rule_body = rule_match.group(1)
                        self.assertIsNone(
                            DANGEROUS_HEIGHT.search(rule_body),
                            f"{fname}: {container} uses height:100vh in mobile CSS"
                        )
                        self.assertIsNone(
                            DANGEROUS_MAX_HEIGHT.search(rule_body),
                            f"{fname}: {container} uses max-height:100vh in mobile CSS"
                        )

    def test_mobile_css_no_overflow_hidden_on_main_containers(self):
        """Main containers inside @media(max-width:768px) must not use overflow:hidden."""
        for fname in TARGET_FILES:
            content = self._read_file(fname)
            blocks = _extract_mobile_blocks(content)
            for block in blocks:
                for container in MAIN_CONTAINERS:
                    container_pattern = re.compile(
                        re.escape(container).replace(r"\-", r"-")
                        + r"\s*\{([^}]*)\}"
                    )
                    for rule_match in container_pattern.finditer(block):
                        rule_body = rule_match.group(1)
                        self.assertIsNone(
                            DANGEROUS_OVERFLOW.search(rule_body),
                            f"{fname}: {container} uses overflow:hidden in mobile CSS"
                        )

    def test_mobile_css_uses_dynamic_viewport(self):
        """Mobile shell/app containers should use svh/dvh, not vh."""
        for fname in TARGET_FILES:
            content = self._read_file(fname)
            blocks = _extract_mobile_blocks(content)
            for block in blocks:
                # Check that .st-key-phone_shell uses svh or dvh
                shell_pattern = re.compile(
                    r"\.st-key-phone_shell\s*\{([^}]*)\}"
                )
                for rule_match in shell_pattern.finditer(block):
                    rule_body = rule_match.group(1)
                    self.assertTrue(
                        "svh" in rule_body or "dvh" in rule_body,
                        f"{fname}: .st-key-phone_shell should use svh/dvh in mobile CSS"
                    )

    def test_mobile_css_max_height_none_on_main_containers(self):
        """Mobile main containers should have max-height:none."""
        for fname in TARGET_FILES:
            content = self._read_file(fname)
            blocks = _extract_mobile_blocks(content)
            for block in blocks:
                # Check phone_shell at minimum
                shell_pattern = re.compile(
                    r"\.st-key-phone_shell\s*\{([^}]*)\}"
                )
                for rule_match in shell_pattern.finditer(block):
                    rule_body = rule_match.group(1)
                    self.assertIn(
                        "max-height:none",
                        rule_body,
                        f"{fname}: .st-key-phone_shell should have max-height:none in mobile CSS"
                    )

    def test_mobile_css_shell_overflow_visible(self):
        """Mobile phone_shell and phone_app should use overflow:visible."""
        for fname in TARGET_FILES:
            content = self._read_file(fname)
            blocks = _extract_mobile_blocks(content)
            for block in blocks:
                shell_pattern = re.compile(
                    r"\.st-key-phone_shell\s*\{([^}]*)\}"
                )
                for rule_match in shell_pattern.finditer(block):
                    rule_body = rule_match.group(1)
                    self.assertIn(
                        "overflow:visible",
                        rule_body,
                        f"{fname}: .st-key-phone_shell should have overflow:visible in mobile CSS"
                    )


if __name__ == "__main__":
    unittest.main()
