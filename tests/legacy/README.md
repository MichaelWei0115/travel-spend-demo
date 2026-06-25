# Legacy Tests

Tests in this directory are based on the **deprecated 5-state / dual-status model**
and are **not collected by the default pytest run**.

They are retained for historical reference only. Do not extend or maintain them.

| File | Status | Reason |
|------|--------|--------|
| `acceptance_test_ticket1_7.py` | Not collected | Based on old 5-state model (ai_check_result + sync_status). References `ui_components.py` and uses `need_supplement`/`sync_failed` filter values that no longer exist in the 4-state model. |

The current authoritative test suite is in `tests/` (parent directory).
