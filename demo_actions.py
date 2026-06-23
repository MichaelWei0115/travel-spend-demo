"""
Demo Action Dispatcher
======================
Unified event handler for every clickable element in the Demo.
All buttons route through handle_demo_action(action, payload).
"""

import streamlit as st
from query_params import set_query_params_preserving_auth
import time
from datetime import datetime
from demo_state import append_message, reset_demo
from feedback import show_success_toast, show_error_toast, show_info_toast
from reimbursement_data import (
    get_default_records, find_record, update_record_fields,
    format_amount, get_status_label, get_cta_action, get_pill_class,
    STATUS_PENDING_RECEIPT, STATUS_PENDING_SUBMIT, STATUS_SUBMITTED, STATUS_ERROR,
)


# =============================================================================
# Mock Reimbursement Records
# =============================================================================

def init_full_state():
    """Initialize all session_state keys safely (never overwrite existing values)."""
    defaults = {
        "messages": [],
        "demo_step": 0,
        "current_task_state": "idle",
        "active_modal": None,
        "current_phone_page": "chat",
        "previous_phone_page": "chat",
        "reimbursement_records": get_default_records(),
        "record_filter": "all",
        "selected_record_id": None,
        "toast_message": "",
        "h5_completed_actions": {},
    }

    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

    # Sidebar action queue keys must exist so on_click callbacks can write them.
    if "_pending_sidebar_action" not in st.session_state:
        st.session_state._pending_sidebar_action = None
    if "_last_sidebar_action" not in st.session_state:
        st.session_state._last_sidebar_action = None
    if "_ui_nonce" not in st.session_state:
        st.session_state._ui_nonce = 0

    # Compat: migrate old set() to dict
    actions = st.session_state.get("h5_completed_actions")
    if isinstance(actions, set):
        st.session_state.h5_completed_actions = {k: True for k in actions}

    # NOTE: We do NOT restore page/rid from query params here.
    # consume_phone_action() handles that correctly after processing phone clicks.
    # Restoring from query params here would overwrite sidebar-driven state
    # changes on the next rerun, causing the phone UI to "jump back".


# =============================================================================
# Toast helpers
# =============================================================================

def set_toast(message: str):
    st.session_state.toast_message = message

def clear_toast():
    st.session_state.toast_message = ""

def sync_ui_state():
    """Increment UI version counter to force Streamlit to detect state change and rerender."""
    st.session_state.ui_version = st.session_state.get("ui_version", 0) + 1

def render_toast():
    msg = st.session_state.get("toast_message", "")
    if msg:
        st.toast(msg)
        st.session_state.toast_message = ""




def append_phone_message(role: str, content: str, msg_type: str = "text"):
    """Append a chat message to session state."""
    from demo_state import append_message
    append_message({"role": role, "type": msg_type, "content": content})


def force_chat_page():
    """Ensure the phone UI shows the chat page."""
    st.session_state.current_phone_page = "chat"
    st.session_state.selected_record_id = None


def clear_phone_query_params_for_sidebar():
    set_query_params_preserving_auth(pa=None, rid=None, filter=None, _t=None)

# =============================================================================
# Record helpers
# =============================================================================

def get_record(record_id: str):
    return find_record(st.session_state.reimbursement_records, record_id)

def update_record(record_id: str, updates: dict):
    return update_record_fields(st.session_state.reimbursement_records, record_id, updates)


def get_filtered_records(filter_key: str = "all"):
    """Backward-compatible filter helper used by h5_pages."""
    from reimbursement_data import filter_records
    records = st.session_state.get("reimbursement_records", [])
    return filter_records(records, filter_key)


def find_first_record_by_status(prefer_status=None):
    records = st.session_state.get("reimbursement_records", [])
    if not records:
        return None
    if prefer_status:
        for r in records:
            if r.get("status") == prefer_status:
                return r
    return records[0]


def ensure_selected_record(prefer_status=None):
    rid = st.session_state.get("selected_record_id")
    records = st.session_state.get("reimbursement_records", [])
    if rid:
        for r in records:
            if r.get("id") == rid:
                return rid
    rec = find_first_record_by_status(prefer_status)
    if rec:
        st.session_state.selected_record_id = rec["id"]
        return rec["id"]
    return None


def queue_sidebar_action(action, payload=None):
    st.session_state._pending_sidebar_action = {"action": action, "payload": payload or {}}


def process_pending_sidebar_action():
    pending = st.session_state.pop("_pending_sidebar_action", None)
    if not pending:
        return False
    action = pending.get("action")
    payload = pending.get("payload") or {}
    handle_demo_action(action, payload)
    st.session_state._last_sidebar_action = action
    st.session_state._ui_nonce = st.session_state.get("_ui_nonce", 0) + 1
    return True


# =============================================================================
# H5->Chat linkage helpers
# =============================================================================

def _h5_action_key(action: str, record_id: str) -> str:
    return f"{action}:{record_id}"

def _h5_append_once(action: str, record_id: str, msg: dict):
    key = _h5_action_key(action, record_id)
    if key not in st.session_state.h5_completed_actions:
        st.session_state.h5_completed_actions[key] = True
        append_message(msg)


# =============================================================================
# Unified Action Dispatcher
# =============================================================================


# =============================================================================
# Chat helpers for new 3-step main flow
# =============================================================================

def force_chat_page():
    """Ensure the phone UI shows the chat page."""
    st.session_state.current_phone_page = "chat"


def get_primary_demo_record():
    records = st.session_state.get("reimbursement_records", [])
    if not records:
        return None
    return records[0]


def append_chat_message(msg: dict):
    if "messages" not in st.session_state:
        st.session_state.messages = []
    st.session_state.messages.append(msg)


def append_assistant_text(content: str):
    append_chat_message({
        "role": "assistant",
        "type": "text",
        "content": content,
    })


def append_user_file(filename: str):
    append_chat_message({
        "role": "user",
        "type": "file",
        "filename": filename,
        "content": filename,
    })


def handle_demo_action(action: str, payload: dict = None):
    """
    Central dispatcher for all demo interactions.
    Every sidebar button routes through here.
    """
    if payload is None:
        payload = {}

    # ---- Phone Page Navigation ----
    if action == "open_chat":
        st.session_state.current_phone_page = "chat"
        st.session_state.selected_record_id = None

    elif action == "open_records":
        st.session_state.current_phone_page = "reimbursement_list"
        st.session_state.record_filter = "all"
        st.session_state.selected_record_id = None

    elif action == "open_detail":
        rid = payload.get("record_id") if payload else None
        if not rid:
            rid = ensure_selected_record(STATUS_PENDING_RECEIPT)
        else:
            st.session_state.selected_record_id = rid
        if rid:
            st.session_state.current_phone_page = "consume_detail"

    elif action == "open_upload":
        rid = payload.get("record_id", st.session_state.selected_record_id or "record_003")
        st.session_state.selected_record_id = rid
        st.session_state.current_phone_page = "consume_detail"

    # ---- New 3-step main flow ----
    elif action == "chat_push_expense_record":
        force_chat_page()

        rec = get_primary_demo_record()
        if rec:
            rec["status"] = STATUS_PENDING_RECEIPT
            rec["attachments"] = []
            rec["ai_check_message"] = "请上传收据，完成补票后方可继续报销流程。"
            st.session_state.selected_record_id = rec["id"]

            append_chat_message({
                "role": "assistant",
                "type": "expense_card",
                "record_id": rec["id"],
            })

    elif action == "chat_upload_receipt":
        force_chat_page()

        rec = get_primary_demo_record()
        if rec:
            st.session_state.selected_record_id = rec["id"]
            append_user_file("Tokyo_Hilton_Receipt.jpg")
            append_assistant_text("票据凭证已收到，正在准备解析并匹配对应消费记录。")

    elif action == "chat_parse_and_match":
        force_chat_page()

        rec = get_primary_demo_record()
        if rec:
            st.session_state.selected_record_id = rec["id"]
            append_chat_message({
                "role": "assistant",
                "type": "parse_card",
                "record_id": rec["id"],
            })

    # ---- Phone CTA from chat cards ----
    elif action == "chat_confirm_submit":
        # Find record by selected or primary
        rec = get_primary_demo_record()
        if not rec:
            selected_rid = st.session_state.get("selected_record_id")
            if selected_rid:
                rec = get_record(selected_rid)
        if rec:
            rid = rec["id"]
            rec["status"] = STATUS_SUBMITTED
            rec["sync_time"] = datetime.now().strftime("%Y-%m-%d %H:%M")
            rec["sync_order_no"] = f"BX{datetime.now().strftime('%Y%m%d%H%M')}{rid[-3:]}"
            rec["ai_check_message"] = "AI 校验通过，费用已提交至报销系统。"
            if not rec.get("attachments"):
                rec["attachments"] = ["收据"]
            st.session_state.selected_record_id = rec["id"]

        # Preserve chat history
        if "messages" not in st.session_state:
            st.session_state.messages = []

        # Fallback: if history lost, rebuild main flow messages
        message_types = [m.get("type") for m in st.session_state.messages]
        has_expense_card = "expense_card" in message_types
        has_file = "file" in message_types
        has_parse_card = "parse_card" in message_types
        if rec and (not has_expense_card or not has_file or not has_parse_card):
            st.session_state.messages = rebuild_main_chat_messages(rec["id"])

        last_msg = st.session_state.messages[-1] if st.session_state.messages else {}
        if not (
            last_msg.get("role") == "assistant"
            and last_msg.get("type") == "text"
            and last_msg.get("content") == "报销内容已提交成功"
        ):
            append_chat_message({
                "role": "assistant",
                "type": "text",
                "content": "报销内容已提交成功",
            })
        st.session_state.current_phone_page = "chat"

    # ---- State Transitions (aligned with 4-state model) ----
    elif action == "confirm_submit":
        rid = st.session_state.selected_record_id or ensure_selected_record(STATUS_PENDING_SUBMIT)
        if rid:
            rec = get_record(rid)
            if rec:
                if rec.get("status") in (STATUS_PENDING_SUBMIT, STATUS_SUBMITTED):
                    now = datetime.now().strftime("%Y-%m-%d %H:%M")
                    order_no = f"BX{datetime.now().strftime('%Y%m%d%H%M')}{rid[-3:]}"
                    update_record(rid, {
                        "status": STATUS_SUBMITTED,
                        "sync_time": now,
                        "sync_order_no": order_no,
                        "ai_check_message": "AI 校验通过，费用已提交至报销系统。",
                    })
                    merchant = rec.get("merchant_name", "")
                    _h5_append_once("confirm_submit", rid, {
                        "role": "assistant", "type": "text",
                        "content": f"{merchant} 已成功提交报销。",
                    })
                    show_success_toast("已提交报销")
                else:
                    show_info_toast("当前状态不可提交")
                st.session_state.selected_record_id = rid
        st.session_state.current_phone_page = "reimbursement_list"

    elif action == "upload_receipt":
        rid = st.session_state.selected_record_id or ensure_selected_record(STATUS_PENDING_RECEIPT)
        if rid:
            rec = get_record(rid)
            if rec:
                if rec.get("status") == STATUS_PENDING_RECEIPT:
                    update_record(rid, {
                        "status": STATUS_PENDING_SUBMIT,
                        "ai_check_message": "收据已上传，AI 校验通过，可以提交报销。",
                        "attachments": rec.get("attachments", []) + ["Tokyo_Hilton_Receipt.jpg"],
                    })
                    merchant = rec.get("merchant_name", "")
                    _h5_append_once("upload_receipt", rid, {
                        "role": "assistant", "type": "text",
                        "content": f"{merchant} 收据已上传，校验通过。",
                    })
                    show_success_toast("收据已上传")
                else:
                    show_info_toast("当前状态无需上传")
                st.session_state.selected_record_id = rid
        st.session_state.current_phone_page = "consume_detail"

    elif action == "submit_error_note":
        rid = st.session_state.selected_record_id or ensure_selected_record(STATUS_ERROR)
        if rid:
            rec = get_record(rid)
            if rec:
                update_record(rid, {
                    "ai_check_message": "异常说明已提交，等待财务复核。",
                })
                st.session_state.selected_record_id = rid
                show_success_toast("异常说明已提交")
        st.session_state.current_phone_page = "reimbursement_list"

    elif action == "retry_process":
        rid = st.session_state.selected_record_id or ensure_selected_record(STATUS_ERROR)
        if rid:
            rec = get_record(rid)
            if rec and rec.get("status") == STATUS_ERROR:
                update_record(rid, {
                    "status": STATUS_PENDING_SUBMIT,
                    "ai_check_message": "问题已处理，可以提交报销。",
                })
                merchant = rec.get("merchant_name", "")
                _h5_append_once("retry_process", rid, {
                    "role": "assistant", "type": "text",
                    "content": f"{merchant} 问题已处理。",
                })
                show_success_toast("已重新处理")
            else:
                show_info_toast("当前状态无需重新处理")
        st.session_state.current_phone_page = "consume_detail"

    elif action == "go_back":
        prev = st.session_state.get("previous_phone_page", "chat")
        st.session_state.current_phone_page = prev
        st.session_state.selected_record_id = None

    # ---- H5 page bridging actions ----
    elif action == "go_supplement":
        rid = payload.get("record_id") if payload else st.session_state.selected_record_id
        if rid:
            st.session_state.selected_record_id = rid
        st.session_state.current_phone_page = "supplement_material"

    elif action == "confirm_single_sync":
        # Same logic as confirm_submit, but navigates to detail page instead of list
        rid = payload.get("record_id") if payload else st.session_state.selected_record_id
        if not rid:
            rid = ensure_selected_record(STATUS_PENDING_SUBMIT)
        if rid:
            st.session_state.selected_record_id = rid
            rec = get_record(rid)
            if rec:
                if rec.get("status") in (STATUS_PENDING_SUBMIT, STATUS_SUBMITTED):
                    now = datetime.now().strftime("%Y-%m-%d %H:%M")
                    order_no = f"BX{datetime.now().strftime('%Y%m%d%H%M')}{rid[-3:]}"
                    update_record(rid, {
                        "status": STATUS_SUBMITTED,
                        "sync_time": now,
                        "sync_order_no": order_no,
                        "ai_check_message": "AI 校验通过，费用已提交至报销系统。",
                    })
                    merchant = rec.get("merchant_name", "")
                    _h5_append_once("confirm_single_sync", rid, {
                        "role": "assistant", "type": "text",
                        "content": f"{merchant} 该笔消费已同步至报销系统。",
                    })
                    show_success_toast("已提交报销")
                else:
                    show_info_toast("当前状态不可提交")
        st.session_state.current_phone_page = "reimbursement_detail"

    elif action == "view_record_detail":
        rid = payload.get("record_id") if payload else st.session_state.selected_record_id
        if rid:
            st.session_state.selected_record_id = rid
        st.session_state.current_phone_page = "reimbursement_detail"

    elif action == "go_back_to_list":
        st.session_state.current_phone_page = "reimbursement_list"

    elif action == "go_back_to_detail":
        rid = st.session_state.selected_record_id
        st.session_state.current_phone_page = "reimbursement_detail"

    elif action == "upload_invoice":
        filename = payload.get("filename", "invoice.pdf") if payload else "invoice.pdf"
        if "supplement_form" not in st.session_state:
            st.session_state.supplement_form = {
                "invoice_uploaded": False, "invoice_name": "",
                "receipt_uploaded": False, "receipt_name": "",
                "note": "", "expense_type": "",
            }
        st.session_state.supplement_form["invoice_uploaded"] = True
        st.session_state.supplement_form["invoice_name"] = filename
        show_success_toast("发票已上传")
        st.rerun()

    elif action == "upload_receipt_voucher":
        filename = payload.get("filename", "receipt.jpg") if payload else "receipt.jpg"
        if "supplement_form" not in st.session_state:
            st.session_state.supplement_form = {
                "invoice_uploaded": False, "invoice_name": "",
                "receipt_uploaded": False, "receipt_name": "",
                "note": "", "expense_type": "",
            }
        st.session_state.supplement_form["receipt_uploaded"] = True
        st.session_state.supplement_form["receipt_name"] = filename
        show_success_toast("消费凭证已上传")
        st.rerun()

    elif action == "submit_supplement":
        rid = st.session_state.selected_record_id
        rec = get_record(rid) if rid else None
        if rec:
            update_record(rid, {
                "status": STATUS_PENDING_SUBMIT,
                "ai_check_message": "收据已上传，AI 校验通过，可以提交报销。",
            })
            merchant = rec.get("merchant_name", "")
            _h5_append_once("submit_supplement", rid, {
                "role": "assistant", "type": "text",
                "content": f"{merchant} 补充材料已提交，校验通过。",
            })
            show_success_toast("补充材料已提交")
        st.session_state.current_phone_page = "reimbursement_detail"

    # ---- Sidebar Demo Flow Steps ----
    elif action == "step_push_receipt":
        from demo_state import run_step_push_pending_receipt
        run_step_push_pending_receipt()
        force_chat_page()

    elif action == "step_upload_receipt":
        from demo_state import run_step_upload_receipt
        run_step_upload_receipt()
        force_chat_page()

    elif action == "step_parse_receipt":
        from demo_state import run_step_parse_receipt
        run_step_parse_receipt()
        force_chat_page()

    elif action == "step_auto_fill":
        from demo_state import run_step_auto_fill
        run_step_auto_fill()
        force_chat_page()

    elif action == "step_sync_success":
        from demo_state import run_step_sync_success
        run_step_sync_success()
        force_chat_page()
        append_phone_message(
            role="assistant",
            content="已完成同步，费用已提交至报销系统。",
            msg_type="text",
        )

    elif action == "full_main_flow":
        handle_demo_action("chat_push_expense_record", {})
        handle_demo_action("chat_upload_receipt", {})
        handle_demo_action("chat_parse_and_match", {})

    elif action == "flow_amount_mismatch":
        force_chat_page()
        # Double-insurance: find and set the primary record to pending_submit
        records = st.session_state.get("reimbursement_records", [])
        rec = None
        for r in records:
            if r.get("status") == STATUS_PENDING_SUBMIT:
                rec = r
                break
        if not rec and records:
            rec = records[0]
        if rec:
            rec["status"] = STATUS_PENDING_SUBMIT
            attachments = rec.get("attachments") or []
            if "Tokyo_Hilton_Receipt.jpg" not in attachments:
                attachments.append("Tokyo_Hilton_Receipt.jpg")
            rec["attachments"] = attachments
            rec["ai_check_message"] = "检测到金额差异，已补票完成，可提交报销。"
            st.session_state.selected_record_id = rec["id"]
            append_chat_message({
                "role": "assistant",
                "type": "amount_mismatch_card",
                "record_id": rec["id"],
            })
        else:
            append_chat_message({
                "role": "assistant",
                "type": "amount_mismatch_card",
                "record_id": "record_001",
            })

    elif action == "flow_payment_failed":
        force_chat_page()
        rec = get_primary_demo_record()
        if rec:
            st.session_state.selected_record_id = rec["id"]
        append_chat_message({
            "role": "assistant",
            "type": "payment_failed_card",
            "record_id": "record_005",
        })

    # ---- Sidebar Card Button Actions ----
    elif action == "confirm_and_sync":
        from demo_state import run_step_sync_success
        run_step_sync_success()

    elif action == "open_edit_detail":
        st.session_state.active_modal = "expense_detail"

    elif action == "save_detail_update":
        append_message({"role": "assistant", "type": "text", "content": "当前 Demo 暂不支持真实编辑。"})

    elif action == "confirm_diff":
        append_message({"role": "assistant", "type": "text", "content": "已记录你的确认，后续将按企业规则进入审核。"})

    elif action == "reupload_receipt":
        append_message({"role": "assistant", "type": "text", "content": "请重新上传正确票据，本 Demo 将使用 mock 票据继续演示。"})

    elif action == "apply_temp_limit":
        append_message({"role": "assistant", "type": "text", "content": "已为你生成临时调额申请草稿。"})

    elif action == "open_travel_rule":
        st.session_state.active_modal = "travel_rules"

    # ---- Reset ----
    elif action == "reset_demo":
        reset_demo()
        init_full_state()
        st.session_state.messages = []
        st.session_state.current_phone_page = "chat"
        st.session_state.selected_record_id = None

    # ---- Fallback ----
    else:
        set_toast(f"未知操作: {action}")

    # Force UI state sync — ensures phone_ui picks up changes on rerun
    sync_ui_state()
    clear_phone_query_params_for_sidebar()

def rebuild_main_chat_messages(record_id: str) -> list:
    """Rebuild the main flow chat messages when history is lost."""
    return [
        {"role": "assistant", "type": "expense_card", "record_id": record_id},
        {"role": "user", "type": "file", "filename": "Tokyo_Hilton_Receipt.jpg", "content": "Tokyo_Hilton_Receipt.jpg"},
        {"role": "assistant", "type": "text", "content": "票据凭证已收到，正在准备解析并匹配对应消费记录。"},
        {"role": "assistant", "type": "parse_card", "record_id": record_id},
    ]
