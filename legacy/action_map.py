"""
Legacy: Old 5-state model action map — NOT used by current business logic.
This module is retained for historical reference only.
Current Demo uses the 4-state model (pending_receipt, pending_submit, submitted, error).
Do not import or extend this module.
"""

"""
Demo Action Map
===============
Unified interaction event spec for every clickable element in the Demo.

Every button, tag, card action, and navigation element is mapped to a
DemoAction entry that defines:
  - trigger:      where the click originates
  - feedback:     immediate visual response type
  - target:       navigation / state destination
  - state_change: what session_state keys are mutated
  - toast:        text shown in a transient notification (empty = no toast)
  - loading:      whether to show a spinner before completing
  - fallback:     what happens if mock logic fails
"""


# =============================================================================
# Action Registry
# =============================================================================

DEMO_ACTIONS = {

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------
    "open_reimbursement_records": {
        "label": "\u62a5\u9500\u8bb0\u5f55",
        "trigger": "\u804a\u5929\u9875\u5feb\u6377\u64cd\u4f5c\u533a / \u66f4\u591a\u83dc\u5355",
        "feedback": "page_navigate",
        "target": "reimbursement_list",
        "state_change": {"current_page": "reimbursement_list"},
        "toast": "",
        "loading": False,
        "fallback": "\u7559\u5728\u804a\u5929\u9875\uff0cToast \u63d0\u793a\u201c\u52a0\u8f7d\u5931\u8d25\u201d",
    },
    "go_back": {
        "label": "\u8fd4\u56de",
        "trigger": "\u5404 H5 \u5b50\u9875\u9762\u9876\u680f",
        "feedback": "page_navigate",
        "target": "previous_page",
        "state_change": {"current_page": "previous"},
        "toast": "",
        "loading": False,
        "fallback": "\u56de\u5230\u804a\u5929\u9875",
    },
    "close_modal": {
        "label": "\u5173\u95ed",
        "trigger": "\u5f39\u7a97 / \u62bd\u5c49\u5185\u90e8",
        "feedback": "close_overlay",
        "target": None,
        "state_change": {"active_modal": None},
        "toast": "",
        "loading": False,
        "fallback": "\u5f3a\u5236\u5173\u95ed\u5f39\u7a97",
    },

    # ------------------------------------------------------------------
    # Reimbursement List Page
    # ------------------------------------------------------------------
    "filter_synced": {
        "label": "\u5df2\u540c\u6b65",
        "trigger": "\u62a5\u9500\u8bb0\u5f55\u5217\u8868\u9875\u72b6\u6001\u6807\u7b7e",
        "feedback": "tab_switch",
        "target": None,
        "state_change": {"record_filter": "synced"},
        "toast": "",
        "loading": False,
        "fallback": "\u663e\u793a\u5168\u90e8\u8bb0\u5f55",
    },
    "filter_need_supplement": {
        "label": "\u5f85\u8865\u5145",
        "trigger": "\u62a5\u9500\u8bb0\u5f55\u5217\u8868\u9875\u72b6\u6001\u6807\u7b7e",
        "feedback": "tab_switch",
        "target": None,
        "state_change": {"record_filter": "need_supplement"},
        "toast": "",
        "loading": False,
        "fallback": "\u663e\u793a\u5168\u90e8\u8bb0\u5f55",
    },
    "filter_sync_failed": {
        "label": "\u540c\u6b65\u5931\u8d25",
        "trigger": "\u62a5\u9500\u8bb0\u5f55\u5217\u8868\u9875\u72b6\u6001\u6807\u7b7e",
        "feedback": "tab_switch",
        "target": None,
        "state_change": {"record_filter": "sync_failed"},
        "toast": "",
        "loading": False,
        "fallback": "\u663e\u793a\u5168\u90e8\u8bb0\u5f55",
    },
    "open_record_detail": {
        "label": "\u67e5\u770b\u8be6\u60c5",
        "trigger": "\u62a5\u9500\u8bb0\u5f55\u5361\u7247",
        "feedback": "page_navigate",
        "target": "record_detail",
        "state_change": {"current_page": "record_detail", "selected_record_id": "<dynamic>"},
        "toast": "",
        "loading": False,
        "fallback": "Toast \u201c\u52a0\u8f7d\u5931\u8d25\u201d",
    },
    "open_supplement_page": {
        "label": "\u53bb\u8865\u5145",
        "trigger": "\u5f85\u8865\u5145\u8bb0\u5f55\u5361\u7247",
        "feedback": "page_navigate",
        "target": "supplement_page",
        "state_change": {"current_page": "supplement_page", "selected_record_id": "<dynamic>"},
        "toast": "",
        "loading": False,
        "fallback": "Toast \u201c\u52a0\u8f7d\u5931\u8d25\u201d",
    },

    # ------------------------------------------------------------------
    # Supplement Page
    # ------------------------------------------------------------------
    "upload_invoice": {
        "label": "\u4e0a\u4f20\u53d1\u7968",
        "trigger": "\u8865\u5145\u6750\u6599\u9875",
        "feedback": "file_selected",
        "target": None,
        "state_change": {"supplement_invoice": "<filename>"},
        "toast": "\u53d1\u7968\u5df2\u9009\u62e9",
        "loading": False,
        "fallback": "Toast \u201c\u4e0a\u4f20\u5931\u8d25\uff0c\u8bf7\u91cd\u8bd5\u201d",
    },
    "select_expense_type": {
        "label": "\u8d39\u7528\u7c7b\u578b\u9009\u62e9",
        "trigger": "\u8865\u5145\u6750\u6599\u9875",
        "feedback": "selection_change",
        "target": None,
        "state_change": {"supplement_expense_type": "<selected>"},
        "toast": "",
        "loading": False,
        "fallback": "\u4fdd\u6301\u539f\u9009\u9879",
    },
    "submit_supplement": {
        "label": "\u63d0\u4ea4\u8865\u5145\u6750\u6599",
        "trigger": "\u8865\u5145\u6750\u6599\u9875\u5e95\u90e8",
        "feedback": "loading_then_toast",
        "target": "reimbursement_list",
        "state_change": {
            "record.ai_check": "passed",
            "record.sync_status": "synced",
            "record.sync_time": "<now>",
        },
        "toast": "\u63d0\u4ea4\u6210\u529f\uff0cAI \u6821\u9a8c\u5df2\u901a\u8fc7\uff0c\u5df2\u540c\u6b65",
        "loading": True,
        "fallback": "Toast \u201c\u63d0\u4ea4\u5931\u8d25\uff0c\u8bf7\u91cd\u8bd5\u201d",
    },

    # ------------------------------------------------------------------
    # Sync Failed Detail
    # ------------------------------------------------------------------
    "retry_sync": {
        "label": "\u91cd\u65b0\u540c\u6b65",
        "trigger": "\u540c\u6b65\u5931\u8d25\u8be6\u60c5\u9875",
        "feedback": "loading_then_toast",
        "target": None,
        "state_change": {
            "record.sync_status": "synced",
            "record.sync_time": "<now>",
        },
        "toast": "\u540c\u6b65\u6210\u529f",
        "loading": True,
        "fallback": "Toast \u201c\u540c\u6b65\u5931\u8d25\uff0c\u8bf7\u7a0d\u540e\u91cd\u8bd5\u201d",
    },

    # ------------------------------------------------------------------
    # Chat Card Buttons (inside iframe)
    # ------------------------------------------------------------------
    "confirm_and_sync": {
        "label": "\u786e\u8ba4\u5e76\u540c\u6b65",
        "trigger": "\u81ea\u52a8\u586b\u5145\u5361\u7247\u5185\u6309\u94ae",
        "feedback": "append_message",
        "target": None,
        "state_change": {"demo_step": 5, "current_task_state": "synced"},
        "toast": "",
        "loading": False,
        "fallback": "\u8ffd\u52a0\u201c\u64cd\u4f5c\u5931\u8d25\u201d\u6587\u672c\u6d88\u606f",
    },
    "open_edit_detail": {
        "label": "\u67e5\u770b/\u7f16\u8f91\u8be6\u60c5",
        "trigger": "\u5f85\u8865\u7968\u5361\u7247 / \u81ea\u52a8\u586b\u5145\u5361\u7247",
        "feedback": "open_modal",
        "target": None,
        "state_change": {"active_modal": "expense_detail"},
        "toast": "",
        "loading": False,
        "fallback": "Toast \u201c\u52a0\u8f7d\u5931\u8d25\u201d",
    },
    "save_detail_update": {
        "label": "\u66f4\u65b0\u8be6\u60c5\u4fe1\u606f",
        "trigger": "\u540c\u6b65\u6210\u529f\u5361\u7247\u5185\u6309\u94ae",
        "feedback": "append_message",
        "target": None,
        "state_change": {},
        "toast": "",
        "loading": False,
        "fallback": "\u8ffd\u52a0\u201c\u64cd\u4f5c\u5931\u8d25\u201d\u6587\u672c\u6d88\u606f",
    },
    "upload_receipt": {
        "label": "\u4e0a\u4f20\u7968\u636e",
        "trigger": "\u5f85\u8865\u7968\u5361\u7247\u5185\u6309\u94ae",
        "feedback": "append_message",
        "target": None,
        "state_change": {"demo_step": 2, "current_task_state": "receipt_uploaded"},
        "toast": "",
        "loading": False,
        "fallback": "\u8ffd\u52a0\u201c\u64cd\u4f5c\u5931\u8d25\u201d\u6587\u672c\u6d88\u606f",
    },
    "confirm_diff": {
        "label": "\u786e\u8ba4\u5dee\u5f02\u5408\u7406",
        "trigger": "\u91d1\u989d\u5dee\u5f02\u5361\u7247\u5185\u6309\u94ae",
        "feedback": "append_message",
        "target": None,
        "state_change": {},
        "toast": "",
        "loading": False,
        "fallback": "\u8ffd\u52a0\u201c\u64cd\u4f5c\u5931\u8d25\u201d\u6587\u672c\u6d88\u606f",
    },
    "reupload_receipt": {
        "label": "\u91cd\u65b0\u4e0a\u4f20",
        "trigger": "\u91d1\u989d\u5dee\u5f02\u5361\u7247\u5185\u6309\u94ae",
        "feedback": "append_message",
        "target": None,
        "state_change": {},
        "toast": "",
        "loading": False,
        "fallback": "\u8ffd\u52a0\u201c\u64cd\u4f5c\u5931\u8d25\u201d\u6587\u672c\u6d88\u606f",
    },
    "apply_temp_limit": {
        "label": "\u7533\u8bf7\u4e34\u65f6\u8c03\u989d",
        "trigger": "\u652f\u4ed8\u5931\u8d25\u5361\u7247\u5185\u6309\u94ae",
        "feedback": "append_message",
        "target": None,
        "state_change": {},
        "toast": "",
        "loading": False,
        "fallback": "\u8ffd\u52a0\u201c\u64cd\u4f5c\u5931\u8d25\u201d\u6587\u672c\u6d88\u606f",
    },
    "open_travel_rule": {
        "label": "\u67e5\u770b\u5dee\u65c5\u89c4\u5219",
        "trigger": "\u652f\u4ed8\u5931\u8d25\u5361\u7247\u5185\u6309\u94ae",
        "feedback": "open_modal",
        "target": None,
        "state_change": {"active_modal": "travel_rules"},
        "toast": "",
        "loading": False,
        "fallback": "Toast \u201c\u52a0\u8f7d\u5931\u8d25\u201d",
    },

    # ------------------------------------------------------------------
    # Chat Input Bar
    # ------------------------------------------------------------------
    "send_message": {
        "label": "\u53d1\u6d88\u606f",
        "trigger": "\u5e95\u90e8\u8f93\u5165\u6846",
        "feedback": "toast",
        "target": None,
        "state_change": {},
        "toast": "Demo \u6a21\u5f0f\u4e0b\u8bf7\u4f7f\u7528\u4f53\u9a8c\u6d41\u7a0b\u6309\u94ae",
        "loading": False,
        "fallback": "\u65e0",
    },
    "upload_attachment": {
        "label": "\u9644\u4ef6\u4e0a\u4f20 (+)",
        "trigger": "\u5e95\u90e8\u8f93\u5165\u680f\u52a0\u53f7",
        "feedback": "toast",
        "target": None,
        "state_change": {},
        "toast": "Demo \u6a21\u5f0f\u4e0b\u8bf7\u70b9\u51fb\u201c\u2461 \u7528\u6237\u4e0a\u4f20\u9152\u5e97\u7968\u636e\u201d",
        "loading": False,
        "fallback": "\u65e0",
    },
    "emoji_tap": {
        "label": "\u8868\u60c5",
        "trigger": "\u5e95\u90e8\u8f93\u5165\u680f\u8868\u60c5\u56fe\u6807",
        "feedback": "toast",
        "target": None,
        "state_change": {},
        "toast": "Demo \u6682\u4e0d\u652f\u6301\u8868\u60c5",
        "loading": False,
        "fallback": "\u65e0",
    },
    "voice_tap": {
        "label": "\u8bed\u97f3",
        "trigger": "\u5e95\u90e8\u8f93\u5165\u680f\u8bed\u97f3\u56fe\u6807",
        "feedback": "toast",
        "target": None,
        "state_change": {},
        "toast": "Demo \u6682\u4e0d\u652f\u6301\u8bed\u97f3",
        "loading": False,
        "fallback": "\u65e0",
    },

    # ------------------------------------------------------------------
    # Chat Header
    # ------------------------------------------------------------------
    "header_back": {
        "label": "\u8fd4\u56de (\u2039)",
        "trigger": "\u804a\u5929\u9876\u680f\u5de6\u4fa7",
        "feedback": "toast",
        "target": None,
        "state_change": {},
        "toast": "\u5df2\u5728\u4e3b\u9875\uff0c\u65e0\u9700\u8fd4\u56de",
        "loading": False,
        "fallback": "\u65e0",
    },
    "header_more": {
        "label": "\u66f4\u591a (\u22ef)",
        "trigger": "\u804a\u5929\u9876\u680f\u53f3\u4fa7",
        "feedback": "open_menu",
        "target": None,
        "state_change": {"active_modal": "more_menu"},
        "toast": "",
        "loading": False,
        "fallback": "Toast \u201c\u83dc\u5355\u52a0\u8f7d\u5931\u8d25\u201d",
    },
    "start_demo_tour": {
        "label": "\u4f53\u9a8c\u6d41\u7a0b (FAB)",
        "trigger": "\u804a\u5929\u533a\u53f3\u4e0b\u89d2\u60ac\u6d6e\u6309\u94ae",
        "feedback": "scroll_to_panel",
        "target": None,
        "state_change": {},
        "toast": "\u8bf7\u5728\u4e0b\u65b9\u6d41\u7a0b\u9762\u677f\u4e2d\u70b9\u51fb\u6309\u94ae\u4f53\u9a8c",
        "loading": False,
        "fallback": "\u65e0",
    },
}


# =============================================================================
# Feedback types
# =============================================================================

FEEDBACK_TYPES = {
    "page_navigate":     "\u8df3\u8f6c\u5230\u76ee\u6807\u9875\u9762",
    "tab_switch":        "\u5207\u6362\u5217\u8868\u7b5b\u9009\u6807\u7b7e",
    "append_message":    "\u5728\u804a\u5929\u533a\u8ffd\u52a0\u4e00\u6761\u6d88\u606f",
    "open_modal":        "\u6253\u5f00\u5f39\u7a97 / \u62bd\u5c49",
    "close_overlay":     "\u5173\u95ed\u5f39\u7a97 / \u62bd\u5c49",
    "open_menu":         "\u6253\u5f00\u83dc\u5355\u6d6e\u5c42",
    "toast":             "\u663e\u793a\u77ed\u6682 Toast \u63d0\u793a",
    "loading_then_toast": "\u663e\u793a Loading \u2192 \u5b8c\u6210\u540e Toast + \u72b6\u6001\u66f4\u65b0",
    "file_selected":     "\u6a21\u62df\u6587\u4ef6\u9009\u62e9\u53cd\u9988",
    "selection_change":  "\u4e0b\u62c9\u6846 / \u5207\u6362\u9009\u9879\u53d8\u66f4",
    "scroll_to_panel":   "\u6eda\u52a8\u5230\u6d41\u7a0b\u9762\u677f\u533a\u57df",
}


# =============================================================================
# Helpers
# =============================================================================

def get_action(action_id: str) -> dict:
    """Look up an action by ID. Returns empty dict if not found."""
    return DEMO_ACTIONS.get(action_id, {})


def get_toast_text(action_id: str) -> str:
    """Get the toast text for an action, empty string if none."""
    return DEMO_ACTIONS.get(action_id, {}).get("toast", "")


def get_all_action_ids() -> list:
    """Return sorted list of all registered action IDs."""
    return sorted(DEMO_ACTIONS.keys())


def validate_coverage(required_labels: list) -> dict:
    """Check which labels from a required list are covered by the action map."""
    registered = {a["label"] for a in DEMO_ACTIONS.values()}
    covered = []
    missing = []
    for label in required_labels:
        if label in registered:
            covered.append(label)
        else:
            missing.append(label)
    return {"covered": covered, "missing": missing, "total": len(required_labels)}
