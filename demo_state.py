"""
Demo State Management
=====================
Manages chat messages, demo steps, and flow execution for the DingTalk demo.
"""

import streamlit as st
from datetime import datetime
from reimbursement_data import get_default_records


# =============================================================================
# State Init
# =============================================================================

def init_state():
    """Initialize all session state keys needed for the demo."""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "demo_step" not in st.session_state:
        st.session_state.demo_step = 0
    if "current_task_state" not in st.session_state:
        st.session_state.current_task_state = "idle"
    if "active_modal" not in st.session_state:
        st.session_state.active_modal = None


def append_message(msg: dict):
    """Append a message to the chat history. Never overwrites existing messages."""
    st.session_state.messages.append(msg)


def reset_demo():
    """Clear all messages and reset demo state."""
    st.session_state.messages = []
    st.session_state.demo_step = 0
    st.session_state.current_task_state = "idle"
    st.session_state.active_modal = None
    # Reset phone page to chat
    st.session_state.current_phone_page = "chat"
    st.session_state.previous_phone_page = "chat"
    # Reset reimbursement records to fresh defaults
    st.session_state.reimbursement_records = get_default_records()
    st.session_state.record_filter = "all"
    st.session_state.selected_record_id = None
    # Clear H5->chat linkage tracking so actions can re-fire after reset
    if "h5_completed_actions" in st.session_state:
        st.session_state.h5_completed_actions = {}


# =============================================================================
# Main Flow Steps
# =============================================================================

def run_step_push_pending_receipt():
    """Step 1: AI proactively pushes a pending receipt notification."""
    append_message({"role": "assistant", "type": "time_chip", "time": "06-12 21:30"})
    append_message({
        "role": "assistant",
        "type": "card",
        "title": "\u4f60\u6709\u4e00\u7b14\u8d39\u7528\u5f85\u8865\u7968",
        "fields": [
            ["\u5546\u6237", "Tokyo Bay Hotel"],
            ["\u91d1\u989d", "\u00a51,280.00"],
            ["\u5e01\u79cd", "JPY \u65e5\u5143"],
            ["\u65f6\u95f4", "06-12 21:30"],
            ["\u5361\u53f7", "WF Card ****1234"],
            ["\u7c7b\u578b", "\u9152\u5e97"],
            ["\u884c\u7a0b", "\u4e1c\u4eac\u5dee\u65c5"],
        ],
        "status": "\u5f85\u8865\u7968",
        "actions": ["\u4e0a\u4f20\u7968\u636e", "\u67e5\u770b/\u7f16\u8f91\u8be6\u60c5"],
    })
    st.session_state.demo_step = 1
    st.session_state.current_task_state = "pending_receipt"


def run_step_upload_receipt():
    """Step 2: User uploads a hotel receipt."""
    append_message({
        "role": "user",
        "type": "receipt_upload",
        "filename": "Tokyo_Bay_Hotel_Receipt.jpg",
        "size": "1.2 MB",
        "image_path": "assets/receipts/tokyo_hotel_receipt.png",
    })
    append_message({
        "role": "assistant",
        "type": "text",
        "content": "\u7968\u636e\u5df2\u6536\u5230\uff0c\u6b63\u5728\u51c6\u5907\u5206\u6790\u7968\u636e\u5185\u5bb9\uff0c\u8bf7\u7a0d\u5019\u3002",
    })
    st.session_state.demo_step = 2
    st.session_state.current_task_state = "receipt_uploaded"


def run_step_parse_receipt():
    """Step 3: AI parses the receipt (progress card)."""
    append_message({
        "role": "assistant",
        "type": "card",
        "title": "\u6b63\u5728\u89e3\u6790\u7968\u636e...",
        "fields": [
            ["\u8bc6\u522b\u5546\u6237", "\u2705"],
            ["\u8bc6\u522b\u91d1\u989d", "\u2705"],
            ["\u8bc6\u522b\u65e5\u671f", "\u2705"],
            ["\u8bc6\u522b\u5e01\u79cd", "\u2705"],
            ["\u5339\u914d\u4ea4\u6613\u8bb0\u5f55", "\u2705"],
            ["\u751f\u6210\u8d39\u7528\u660e\u7ec6", "\u2705"],
        ],
        "hint": "\u89e3\u6790\u4e2d\u8bf7\u52ff\u5173\u95ed\u4f1a\u8bdd\uff0c\u9884\u8ba1\u8017\u65f6 10\u201320 \u79d2\u3002",
    })
    st.session_state.demo_step = 3
    st.session_state.current_task_state = "parsing"


def run_step_auto_fill():
    """Step 4: AI auto-fills expense details from receipt + transaction."""
    append_message({
        "role": "assistant",
        "type": "card",
        "title": "\u7968\u636e\u8bc6\u522b\u5b8c\u6210\uff0c\u5df2\u81ea\u52a8\u586b\u5145\u8d39\u7528\u660e\u7ec6",
        "fields": [
            ["\u5546\u6237", "Tokyo Bay Hotel"],
            ["\u91d1\u989d", "\u00a51,280.00"],
            ["\u5e01\u79cd", "JPY \u65e5\u5143"],
            ["\u65e5\u671f", "2025-06-12"],
            ["\u5361\u53f7\u672b\u56db\u4f4d", "1234"],
            ["\u8d39\u7528\u7c7b\u578b", "\u9152\u5e97"],
            ["\u7a0e\u7387", "10% \u6d88\u8d39\u7a0e"],
            ["\u8d39\u7528\u5f52\u7c7b", "\u4f4f\u5bbf\u8d39"],
            ["\u884c\u7a0b", "\u4e1c\u4eac\u5dee\u65c5"],
            ["\u652f\u4ed8\u65b9\u5f0f", "WF Card ****1234"],
            ["\u63cf\u8ff0", "\u4e1c\u4eac\u51fa\u5dee\u4f4f\u5bbf\u8d39"],
        ],
        "status": "\u5df2\u8bc6\u522b",
        "actions": ["\u786e\u8ba4\u5e76\u540c\u6b65", "\u67e5\u770b/\u7f16\u8f91\u8be6\u60c5"],
        "subtitle": "\u5b57\u6bb5\u6765\u6e90\uff1a\u7968\u636e\u8bc6\u522b \u00b7 \u4ea4\u6613\u8bb0\u5f55 \u00b7 AI \u81ea\u52a8\u5206\u7c7b",
        "hint": "\u5546\u6237/\u91d1\u989d/\u5e01\u79cd/\u65e5\u671f/\u7a0e\u7387 \u2190 \u7968\u636e\u8bc6\u522b\uff5c\u5361\u53f7/\u652f\u4ed8\u65b9\u5f0f \u2190 \u4ea4\u6613\u8bb0\u5f55\uff5c\u8d39\u7528\u7c7b\u578b/\u5f52\u7c7b/\u63cf\u8ff0/\u884c\u7a0b \u2190 AI \u81ea\u52a8\u5206\u7c7b",
    })
    st.session_state.demo_step = 4
    st.session_state.current_task_state = "auto_filled"


def run_step_sync_success():
    """Step 5: Sync completed."""
    append_message({
        "role": "assistant",
        "type": "card",
        "title": "\u5df2\u540c\u6b65\u81f3\u62a5\u9500\u7cfb\u7edf",
        "subtitle": "\u4ea4\u6613\u540c\u6b65\u5b8c\u6210\uff0c\u8d39\u7528\u8bb0\u5f55\u5df2\u751f\u6210\u3002",
        "fields": [
            ["\u5546\u6237", "Tokyo Bay Hotel"],
            ["\u91d1\u989d", "\u00a51,280.00 JPY"],
            ["\u65e5\u671f", "2025-06-12"],
            ["\u8d39\u7528\u7c7b\u578b", "\u9152\u5e97"],
        ],
        "status": "\u5df2\u540c\u6b65",
        "actions": ["\u66f4\u65b0\u8be6\u60c5\u4fe1\u606f"],
    })
    st.session_state.demo_step = 5
    st.session_state.current_task_state = "synced"


# =============================================================================
# Exception Flows
# =============================================================================

def run_flow_amount_mismatch():
    """Exception flow: amount difference needs confirmation."""
    append_message({"role": "assistant", "type": "time_chip", "time": "06-12 20:15"})
    append_message({
        "role": "assistant",
        "type": "card",
        "title": "\u68c0\u6d4b\u5230\u91d1\u989d\u5dee\u5f02\uff0c\u8bf7\u786e\u8ba4",
        "subtitle": "\u53ef\u80fd\u56e0\u7a0e\u8d39\u3001\u670d\u52a1\u8d39\u6216\u5c0f\u8d39\u5bfc\u81f4\u91d1\u989d\u5dee\u5f02\u3002",
        "fields": [
            ["\u4ea4\u6613\u91d1\u989d", "96 USD"],
            ["\u7968\u636e\u91d1\u989d", "88 USD"],
            ["\u5dee\u5f02", "8 USD"],
            ["\u5339\u914d\u7f6e\u4fe1\u5ea6", "72%"],
        ],
        "status": "\u9700\u8981\u786e\u8ba4",
        "actions": ["\u786e\u8ba4\u5dee\u5f02\u5408\u7406", "\u91cd\u65b0\u4e0a\u4f20"],
        "hint": "\u53ef\u80fd\u539f\u56e0\uff1a\u9910\u996e\u5c0f\u8d39\u3001\u7a0e\u8d39\u6216\u670d\u52a1\u8d39\u672a\u4f53\u73b0\u5728\u7968\u636e\u91d1\u989d\u4e2d\u3002",
    })
    st.session_state.current_task_state = "amount_mismatch"


def run_flow_payment_failed():
    """Exception flow: payment failed explanation."""
    append_message({"role": "assistant", "type": "time_chip", "time": "06-13 09:00"})
    append_message({
        "role": "assistant",
        "type": "card",
        "title": "\u652f\u4ed8\u5931\u8d25\uff1a\u8d85\u8fc7\u9152\u5e97\u5355\u7b14\u9650\u989d",
        "fields": [
            ["\u5546\u6237", "Tokyo Hotel"],
            ["\u4ea4\u6613\u91d1\u989d", "1500 USD"],
            ["\u89c4\u5219", "\u9152\u5e97\u7c7b\u5355\u7b14\u9650\u989d 1000 USD"],
        ],
        "status": "\u652f\u4ed8\u5931\u8d25",
        "actions": ["\u7533\u8bf7\u4e34\u65f6\u8c03\u989d", "\u67e5\u770b\u5dee\u65c5\u89c4\u5219"],
        "hint": "\u5f53\u524d\u4ea4\u6613\u91d1\u989d\u8d85\u8fc7\u9152\u5e97\u5355\u7b14\u9650\u989d 1000 USD\uff0c\u4ed8\u6b3e\u88ab\u62d2\u7edd\u3002",
    })
    st.session_state.current_task_state = "payment_failed"


# =============================================================================
# Card Button Responses (mock feedback)
# =============================================================================

def handle_confirm_sync():
    """Mock response when user clicks 'Confirm & Sync' on step 4 card."""
    run_step_sync_success()


def handle_view_detail():
    """Mock response for 'View/Edit Detail' button."""
    st.session_state.active_modal = "expense_detail"


def handle_update_detail():
    """Mock response for 'Update Detail' button on sync success card."""
    append_message({
        "role": "assistant",
        "type": "text",
        "content": "\u5f53\u524d Demo \u6682\u4e0d\u652f\u6301\u771f\u5b9e\u7f16\u8f91\uff0c\u53ef\u5728\u6b63\u5f0f\u7cfb\u7edf\u4e2d\u4fee\u6539\u8d39\u7528\u8be6\u60c5\u3002",
    })


def close_modal():
    """Close any open modal/drawer."""
    st.session_state.active_modal = None


def handle_confirm_diff():
    """Mock response for 'Confirm difference is reasonable' button."""
    append_message({
        "role": "assistant",
        "type": "text",
        "content": "已记录你的确认，后续将按企业规则进入审核。",
    })


def handle_reupload():
    """Mock response for 'Re-upload' button."""
    append_message({
        "role": "assistant",
        "type": "text",
        "content": "请重新上传正确票据，本 Demo 将使用 mock 票据继续演示。",
    })


def handle_apply_limit_increase():
    """Mock response for 'Apply temporary limit increase' button."""
    append_message({
        "role": "assistant",
        "type": "text",
        "content": "已为你生成临时调额申请草稿。",
    })


def handle_view_travel_rules():
    """Open travel rules modal."""
    st.session_state.active_modal = "travel_rules"


# =============================================================================
# Composite Flow
# =============================================================================

def run_full_main_flow():
    """Run all 5 main flow steps at once."""
    run_step_push_pending_receipt()
    run_step_upload_receipt()
    run_step_parse_receipt()
    run_step_auto_fill()
    run_step_sync_success()
