# Visual / Manual Tests

Tests in this directory require a **real browser environment** (Playwright)
and are **not part of the default pytest suite**.

They must be run manually:

```bash
# Requires: pip install playwright && playwright install
pytest tests/visual/ -v
```

| File | Description |
|------|-------------|
| `visual_assert_chat_page.py` | Visual regression: chat page layout bounding box checks |
| `visual_contract_chat_buttons.py` | Visual regression: chat button contract checks |

These tests validate pixel-level rendering and are intended for manual
regression checks before releases, not for CI.
