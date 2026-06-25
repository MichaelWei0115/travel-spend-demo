# Legacy Modules

This directory contains modules that are **no longer used by current business logic**.
They are retained for historical reference and regression protection only.

**Do not import or extend these modules.**

| File | Reason | Superseded By |
|------|--------|---------------|
| `action_map.py` | Old 5-state model action map; contains `need_supplement`, `sync_failed`, `sync_status` values that belong to the deprecated dual-status model. Zero import references in current code. | 4-state model in `reimbursement_data.py` |
| `ui_components.py` | Old chat UI component library; references `phone_shell.py`. Zero import references in current business code (only referenced by `tests/acceptance_test_ticket1_7.py`). | `phone_ui.py` |
