"""
Phone UI - Pure HTML/CSS with form-based navigation.
=====================================================
Phone buttons = <form method="get" target="_self"><button type="submit">
No JavaScript. No st.button inside phone.

Unified 3-layer architecture:
  Chat (entry) -> Inbox (list) -> Decision Page (detail + upload)
"""

import html as html_mod
import time as time_mod
import streamlit as st
from datetime import datetime
from urllib.parse import urlencode

from query_params import AUTH_QUERY_KEY, set_query_params_preserving_auth
from reimbursement_data import (
    STATUS_PENDING_RECEIPT, STATUS_PENDING_SUBMIT, STATUS_SUBMITTED, STATUS_ERROR,
    get_status_label, get_pill_class, format_amount, get_cta_action,
    find_record as _find_record_in_list,
)


# ═══ Helpers ═════════════════════════════════════════════════════

def esc(value):
    return html_mod.escape(str(value or ""))

def now_display():
    return datetime.now().strftime("%Y-%m-%d %H:%M")

def find_record(record_id):
    for r in st.session_state.get("reimbursement_records", []):
        if r["id"] == record_id:
            return r
    return None

def append_chat_msg(text):
    st.session_state.setdefault("chat_messages", [])
    st.session_state.chat_messages.append({"role": "assistant", "text": text})

def qp_value(name, default=None):
    v = st.query_params.get(name)
    if isinstance(v, list):
        return v[0] if v else default
    return v if v is not None else default

STATUS_LABEL = {
    STATUS_PENDING_RECEIPT: "待补票",
    STATUS_PENDING_SUBMIT: "待提交",
    STATUS_SUBMITTED: "已提交",
    STATUS_ERROR: "异常",
}

def status_label(s):
    return STATUS_LABEL.get(s, s)

def amount_text(r):
    return format_amount(r.get("amount", ""), r.get("currency", "CNY"))

def list_amount_text(r):
    currency = r.get("currency")
    amount = r.get("amount")
    if currency == "JPY":
        return f"JPY {amount:,}"
    if currency == "SGD":
        return f"SGD {amount:,.2f}"
    if currency == "USD":
        return f"USD {amount:,.2f}"
    if currency == "GBP":
        return f"GBP {amount:,.2f}"
    if currency == "HKD":
        return f"HK${amount:,}"
    if currency == "CNY":
        return f"¥{amount:,}"
    return f"{currency} {amount}"


def detail_amount_text(r):
    """Detail-page amount format. Shows foreign currency, no RMB symbol."""
    currency = r.get("currency")
    amount = r.get("amount")
    if currency == "JPY":
        return f"JPY {int(amount):,}"
    if currency in ("SGD", "USD", "GBP"):
        return f"{currency} {float(amount):,.2f}"
    if currency == "HKD":
        return f"HK${int(amount):,}"
    if currency == "CNY":
        return f"¥{int(amount):,}"
    return f"{currency} {amount}"


# ═══ Core: phone_action_form ═════════════════════════════════════

def phone_action_form(label, action, cls, rid=None, filter_value=None, name=None):
    """Generate a native HTML GET form button. No JS needed."""
    hiddens = f'<input type="hidden" name="pa" value="{esc(action)}">'
    hiddens += f'<input type="hidden" name="_t" value="{int(time_mod.time()*1000)}">'
    if rid:
        hiddens += f'<input type="hidden" name="rid" value="{esc(rid)}">'
    if filter_value:
        hiddens += f'<input type="hidden" name="filter" value="{esc(filter_value)}">'
    # Preserve demo_authed across GET form submissions
    if st.query_params.get(AUTH_QUERY_KEY) == "1":
        hiddens += f'<input type="hidden" name="{AUTH_QUERY_KEY}" value="1">'
    da = f' data-action="{esc(name or action)}"' if (name or action) else ""
    return f'<form class="phone-action-form" method="get" action="" target="_self"{da}>{hiddens}<button type="submit" class="{cls}">{esc(label)}</button></form>'


# ═══ Action Router ═══════════════════════════════════════════════

def consume_phone_action():
    """Read query params from form submission, update state."""
    action = qp_value("pa")
    rid = qp_value("rid")

    # Only restore rid from query params when there is an actual phone
    # action (pa=<action>). Without pa, rid is stale from a previous
    # navigation and would override sidebar-driven state changes.
    if action and rid:
        st.session_state.selected_record_id = rid

    if not action:
        return

    filt = qp_value("filter")

    if action == "open_chat":
        st.session_state.current_phone_page = "chat"

    elif action == "open_records":
        st.session_state.current_phone_page = "reimbursement_list"

    elif action == "set_filter":
        st.session_state.record_filter = filt or "all"
        st.session_state.current_phone_page = "reimbursement_list"

    elif action == "open_detail":
        if rid:
            st.session_state.selected_record_id = rid
        st.session_state.current_phone_page = "consume_detail"

    elif action == "open_amount_mismatch_detail":
        rec = find_record(rid)
        if not rec:
            selected_rid = st.session_state.get("selected_record_id")
            rec = find_record(selected_rid) if selected_rid else None
        if not rec:
            records = st.session_state.get("reimbursement_records", [])
            rec = records[0] if records else None
        if rec:
            rec["status"] = STATUS_PENDING_SUBMIT
            attachments = rec.get("attachments") or []
            if "Tokyo_Hilton_Receipt.jpg" not in attachments:
                attachments.append("Tokyo_Hilton_Receipt.jpg")
            rec["attachments"] = attachments
            rec["ai_check_message"] = "检测到金额差异：票据金额与支付交易金额不一致，需要确认后提交。"
            st.session_state.selected_record_id = rec["id"]
        st.session_state.current_phone_page = "consume_detail"

    elif action == "confirm_submit":
        rec = find_record(rid)
        if not rec:
            selected_rid = st.session_state.get("selected_record_id")
            rec = find_record(selected_rid) if selected_rid else None
        if rec:
            if rec.get("status") in (STATUS_PENDING_RECEIPT, STATUS_PENDING_SUBMIT, STATUS_SUBMITTED):
                rec["status"] = STATUS_SUBMITTED
                rec["sync_time"] = now_display()
                rec["sync_order_no"] = rec.get("sync_order_no") or f"BX{datetime.now().strftime('%Y%m%d%H%M')}"
                rec["ai_check_message"] = "AI 校验通过，费用已提交至报销系统。"
                append_chat_msg(f"{rec['merchant_name']} 已成功提交报销。")
                from demo_state import append_message
                append_message({"role": "assistant", "type": "text", "content": f"{rec['merchant_name']} 已成功提交报销。"})
            st.session_state.selected_record_id = rec["id"]
        st.session_state.current_phone_page = "reimbursement_list"

    elif action == "upload_receipt":
        rec = find_record(rid)
        if not rec:
            selected_rid = st.session_state.get("selected_record_id")
            rec = find_record(selected_rid) if selected_rid else None
        if rec:
            if rec.get("status") == STATUS_PENDING_RECEIPT:
                rec["status"] = STATUS_PENDING_SUBMIT
                rec["ai_check_message"] = "收据已上传，AI 校验通过，可以提交报销。"
                rec["attachments"] = rec.get("attachments", []) + ["Tokyo_Hilton_Receipt.jpg"]
                append_chat_msg(f"{rec['merchant_name']} 收据已上传，校验通过。")
                from demo_state import append_message
                append_message({"role": "assistant", "type": "text", "content": f"{rec['merchant_name']} 收据已上传，校验通过。"})
            st.session_state.selected_record_id = rec["id"]
        st.session_state.current_phone_page = "consume_detail"


    elif action == "submit_error_note":
        rec = find_record(rid)
        if rec:
            rec["ai_check_message"] = "异常说明已提交，等待财务复核。"
            st.session_state.selected_record_id = rec["id"]
        st.session_state.current_phone_page = "reimbursement_list"

    elif action == "retry_process":
        rec = find_record(rid)
        if rec and rec.get("status") == STATUS_ERROR:
            rec["status"] = STATUS_PENDING_SUBMIT
            rec["ai_check_message"] = "问题已处理，可以提交报销。"
            append_chat_msg(f"{rec['merchant_name']} 问题已处理。")
            from demo_state import append_message
            append_message({"role": "assistant", "type": "text", "content": f"{rec['merchant_name']} 问题已处理。"})
        st.session_state.current_phone_page = "consume_detail"

    elif action == "chat_confirm_submit":
        rec = find_record(rid)
        if rec:
            rec["status"] = STATUS_SUBMITTED
            rec["sync_time"] = now_display()
            rec["sync_order_no"] = rec.get("sync_order_no") or f"BX{datetime.now().strftime('%Y%m%d%H%M')}"
            rec["ai_check_message"] = "AI 校验通过，费用已提交至报销系统。"
            if not rec.get("attachments"):
                rec["attachments"] = ["收据"]
        # Fallback: if rid lost, try selected or first record
        if not rec:
            selected_rid = st.session_state.get("selected_record_id")
            rec = find_record(selected_rid) if selected_rid else None
        if not rec:
            records = st.session_state.get("reimbursement_records", [])
            rec = records[0] if records else None
        if rec:
            rec["status"] = STATUS_SUBMITTED
            rec["sync_time"] = now_display()
            rec["sync_order_no"] = rec.get("sync_order_no") or f"BX{datetime.now().strftime('%Y%m%d%H%M')}"
            rec["ai_check_message"] = "AI 校验通过，费用已提交至报销系统。"
            if not rec.get("attachments"):
                rec["attachments"] = ["收据"]

        # Preserve chat history
        if "messages" not in st.session_state:
            st.session_state.messages = []

        # Fallback: if history lost, rebuild main flow messages
        message_types = [m.get("type") for m in st.session_state.messages]
        has_expense_card = "expense_card" in message_types
        has_file = "file" in message_types
        has_parse_card = "parse_card" in message_types
        if rec and (not has_expense_card or not has_file or not has_parse_card):
            try:
                from demo_actions import rebuild_main_chat_messages
                st.session_state.messages = rebuild_main_chat_messages(rec["id"])
            except Exception:
                st.session_state.messages = [
                    {"role": "assistant", "type": "expense_card", "record_id": rec["id"]},
                    {"role": "user", "type": "file", "filename": "Tokyo_Hilton_Receipt.jpg", "content": "Tokyo_Hilton_Receipt.jpg"},
                    {"role": "assistant", "type": "text", "content": "票据凭证已收到，正在准备解析并匹配对应消费记录。"},
                    {"role": "assistant", "type": "parse_card", "record_id": rec["id"]},
                ]

        last_msg = st.session_state.messages[-1] if st.session_state.messages else {}
        if not (
            last_msg.get("role") == "assistant"
            and last_msg.get("type") == "text"
            and last_msg.get("content") == "报销内容已提交成功"
        ):
            from demo_state import append_message
            append_message({
                "role": "assistant",
                "type": "text",
                "content": "报销内容已提交成功",
            })
        st.session_state.current_phone_page = "chat"

    elif action == "open_travel_policy":
        if rid:
            st.session_state.selected_record_id = rid
        st.session_state.current_phone_page = "travel_policy"

    elif action == "quick_rules":
        append_chat_msg("差旅规则包括住宿、交通、餐饮等费用标准。当前酒店住宿需提供发票或消费凭证。")
        st.session_state.current_phone_page = "chat"

    elif action == "quick_files":
        append_chat_msg("你可以上传发票、行程单、支付截图等附件，AI 会自动识别并校验。")
        st.session_state.current_phone_page = "chat"

    # Update query params for page reload survival (preserving demo_authed)
    updates = {"page": st.session_state.get("current_phone_page") or "chat"}
    if st.session_state.get("selected_record_id"):
        updates["rid"] = st.session_state["selected_record_id"]
    # Clear action trigger params to prevent re-processing
    for key in ["pa", "_t", "filter"]:
        updates[key] = None
    set_query_params_preserving_auth(**updates)

    # Force UI version increment so sidebar/render loop detects the change
    st.session_state.ui_version = st.session_state.get("ui_version", 0) + 1


def process_pending_action():
    """No-op placeholder. State changes are now handled directly in consume_phone_action."""
    pass


# ═══ CSS ═════════════════════════════════════════════════════════

PHONE_CSS = """
<style>
:root{--phone-w:390px;--phone-h:867px;--content-w:358px;--bg:#f5f6f8;--card:#fff;--text-main:#1f2329;--text-secondary:#646a73;--text-tertiary:#8f959e;--border:#e5e8ef;--border-strong:#d8dde8;--primary:#1677ff;--warning-bg:#fff7e8;--success-bg:#eafaf2;--danger:#e5484d;--danger-bg:#fff1f0;--success:#12b76a;--info-bg:#eff6ff;--info:#1565c0}
#MainMenu,footer,.stAppDeployButton,div[data-testid="stToolbar"],div[data-testid="stDecoration"],header[data-testid="stHeader"]{display:none!important}
.block-container{max-width:1280px!important;padding-top:.5rem!important}
.stApp{background:#F0F1F3!important}
.stTabs [data-baseweb="tab-panel"]{padding:0}
.stTabs [data-baseweb="tab-list"]{gap:14px !important;background:#f8f8f8;border-bottom:1px solid #e8e8e8;padding-left:8px !important}
.stTabs [data-baseweb="tab"]{padding:8px 10px !important;margin-right:0 !important}
iframe{border:none!important}
.st-key-phone_shell{width:var(--phone-w)!important;min-width:var(--phone-w)!important;max-width:var(--phone-w)!important;height:var(--phone-h)!important;min-height:var(--phone-h)!important;max-height:var(--phone-h)!important;margin:0 auto!important;border-radius:32px!important;overflow:hidden!important;background:var(--bg)!important;border:1px solid rgba(15,23,42,.08)!important;box-shadow:0 20px 48px rgba(15,23,42,.14)!important}
.st-key-side_panel .stButton>button{font-size:13px!important;min-height:36px!important;padding:4px 10px!important;border-radius:10px!important;background:#fff!important;border:1px solid #d8dde8!important;color:#4E5969!important}
.st-key-side_panel .stButton>button[kind="primary"]{min-height:40px!important;background:#1677ff!important;border-color:#1677ff!important;color:#fff!important;font-weight:600!important}
.phone-app-v2{width:390px;height:867px;overflow:hidden;position:relative;background:var(--bg);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;color:var(--text-main)}
.phone-status{width:390px;height:24px;background:#fff;padding:0 22px;box-sizing:border-box;display:flex;align-items:center;justify-content:space-between;font-size:12px;font-weight:700}
.phone-nav{width:390px;height:56px;background:#fff;border-bottom:1px solid #edf0f5;position:relative;display:flex;align-items:center;justify-content:center;box-sizing:border-box}
.phone-title{text-align:center;font-size:17px;font-weight:700;line-height:20px}
.phone-subtitle{margin-top:3px;font-size:11px;color:var(--text-tertiary);font-weight:400;text-align:center}
.phone-more{position:absolute;right:16px;top:13px;font-size:22px}
.phone-back-wrap{position:absolute;left:12px;top:10px;width:36px;height:36px}
.phone-back-wrap .phone-action-form{width:36px;height:36px}
.phone-back-btn{width:36px!important;height:36px!important;border-radius:18px!important;background:transparent!important;border:none!important;color:#1f2329!important;font-size:24px!important}
.phone-body{width:390px;height:calc(867px - 24px - 56px);overflow-y:auto;box-sizing:border-box;background:var(--bg)}
.phone-body.has-bottom{height:calc(867px - 24px - 56px - 160px);padding:12px 16px 16px}
.phone-body.has-action-bottom{height:calc(867px - 24px - 56px - 104px);padding:12px 16px 16px}
.phone-body.scroll-body{height:calc(867px - 24px - 56px);padding:12px 16px 16px}
.phone-bottom{width:390px;height:160px;background:rgba(255,255,255,.98);border-top:1px solid #edf0f5;padding:10px 16px 12px;box-sizing:border-box}
.phone-action-bottom{width:390px;height:104px;background:rgba(255,255,255,.98);border-top:1px solid #edf0f5;padding:10px 16px 12px;box-sizing:border-box}
.home-indicator{width:120px;height:4px;border-radius:999px;background:#111827;margin:9px auto 0;opacity:.9}
.chat-date{width:fit-content;margin:0 auto 12px;padding:4px 10px;border-radius:999px;background:#edf0f5;color:var(--text-tertiary);font-size:11px}
.chat-row{width:var(--content-w);margin:0 auto 10px;display:flex;align-items:flex-start;gap:8px;box-sizing:border-box}
.chat-assistant-row{justify-content:flex-start}
.bot-avatar{width:32px;height:32px;border-radius:16px;background:var(--primary);color:#fff;flex:0 0 32px;display:flex;align-items:center;justify-content:center;font-size:17px;box-shadow:0 4px 10px rgba(22,119,255,.2)}
.chat-bubble{display:inline-block;width:fit-content;max-width:250px;padding:10px 12px;border-radius:4px 14px 14px 14px;box-sizing:border-box;font-size:13px;line-height:20px;color:var(--text-main);word-break:break-word;overflow-wrap:anywhere}
.assistant-bubble{background:#fff;box-shadow:0 2px 8px rgba(15,23,42,.04)}
.user-row{width:var(--content-w);margin:0 auto 10px;display:flex;flex-direction:row;justify-content:flex-end;align-items:flex-start;gap:8px;box-sizing:border-box;overflow:visible}
.user-bubble{background:#95d4ff;color:#1f2329;padding:10px 12px;border-radius:14px 4px 14px 14px;box-shadow:0 2px 8px rgba(15,23,42,.04);max-width:238px;flex:0 1 auto}
.user-avatar{width:32px;height:32px;border-radius:16px;background:#e5e8ef;color:#1f2329;flex:0 0 32px;display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:600}
.chat-welcome{width:318px;background:#fff;border-radius:13px;padding:14px 14px 12px;box-sizing:border-box;font-size:13px;line-height:1.7;color:var(--text-main);box-shadow:0 2px 8px rgba(15,23,42,.04)}
.ticket-card{width:318px;background:#fff;border:1px solid rgba(22,119,255,.45);border-radius:14px;padding:12px;box-sizing:border-box;box-shadow:0 4px 12px rgba(22,119,255,.08)}
.ticket-title-row{display:flex;align-items:center;justify-content:space-between;gap:8px;margin-bottom:10px}
.ticket-title{font-size:13px;font-weight:700;line-height:18px;color:#1f2329}
.ticket-merchant{font-size:16px;font-weight:700;line-height:22px;color:#1f2329;margin-bottom:8px}
.ticket-amount-row{display:flex;align-items:flex-end;justify-content:space-between;gap:12px;margin-bottom:8px}
.ticket-meta-label{font-size:11px;color:#8f959e;line-height:16px}
.ticket-meta{font-size:12px;color:#646a73;line-height:17px;margin-top:2px}
.ticket-amount{font-size:20px;font-weight:800;color:#111827;line-height:24px;white-space:nowrap}
.ticket-tag{display:inline-block;font-size:11px;font-weight:600;padding:2px 6px;border-radius:4px;background:rgba(22,119,255,.08);color:var(--primary);margin-bottom:10px}
.ticket-actions{width:294px;display:grid;grid-template-columns:1fr;gap:8px}
.ticket-actions.single{width:100%;display:block}
.ticket-actions.single .phone-action-form{width:100%;height:40px}
.ticket-actions.single button{width:100%;height:40px;border-radius:10px;font-size:13px;font-weight:700}
.ticket-actions .phone-action-form{height:42px}
.ticket-actions .phone-action-form button{height:42px;border-radius:10px;font-size:13px;font-weight:600;padding:0 6px}
.phone-action-form{margin:0;padding:0;width:100%;height:100%;display:block}
.phone-action-form button{width:100%;height:100%;margin:0;padding:0;border:none;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;cursor:pointer;box-sizing:border-box;white-space:nowrap;display:flex;align-items:center;justify-content:center}
.phone-btn{display:flex;align-items:center;justify-content:center;box-sizing:border-box;white-space:nowrap;cursor:pointer}
.btn-card{height:36px;border-radius:10px;font-size:13px;font-weight:600}
.btn-secondary{background:#fff;color:#1f2329!important;border:1px solid #d8dde8!important}
.btn-primary{background:#1677ff;color:#fff!important;border:1px solid #1677ff!important}
.quick-title{width:var(--content-w);margin:0 auto 8px;font-size:12px;line-height:18px;color:var(--text-secondary);font-weight:500}
.quick-pills{width:var(--content-w);display:flex;justify-content:flex-start;margin:0 auto 12px}
.quick-pills .phone-action-form{flex:0 0 auto;height:32px;width:112px}
.quick-pills .phone-action-form button{width:100%;height:32px;border-radius:16px;font-size:12px;font-weight:500;background:#f4f5f7;color:var(--text-main)!important;border:1px solid var(--border)!important;padding:0 14px;white-space:nowrap}
.input-bar{width:var(--content-w);display:flex;gap:8px;align-items:center;margin:0 auto}
.input-bar-icon{width:28px;height:28px;border-radius:14px;background:transparent;border:none;color:var(--text-tertiary)!important;font-size:16px;display:flex;align-items:center;justify-content:center;flex:0 0 28px;cursor:default}
.input-bar-field{flex:1;height:36px;border-radius:18px;background:#fff;border:1px solid var(--border);color:var(--text-tertiary);display:flex;align-items:center;padding:0 14px;box-sizing:border-box;font-size:13px;box-shadow:0 1px 3px rgba(15,23,42,.05)}
.input-bar-send{width:28px;height:28px;border-radius:14px;background:var(--primary);border:none;color:#fff!important;font-size:13px;display:flex;align-items:center;justify-content:center;flex:0 0 28px;cursor:default;box-shadow:0 2px 6px rgba(22,119,255,.3)}
.user-file-bubble{width:fit-content;max-width:270px;padding:9px 12px;background:#95d4FF;color:#1f2329;border-radius:14px 2px 14px 14px;font-size:13px;line-height:1.45;display:flex;align-items:center;gap:6px;word-break:break-word}
.chat-user-row{width:var(--content-w);margin:0 auto 10px;display:flex;flex-direction:row;justify-content:flex-end;align-items:flex-start;gap:8px;box-sizing:border-box;overflow:visible}
.chat-user-file{white-space:normal}
.user-avatar{width:32px;height:32px;border-radius:16px;background:#d9d9d9;color:#1f2329;flex:0 0 32px;display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:600}
.user-row{width:var(--content-w);margin:0 auto 10px;display:flex;justify-content:flex-end;gap:8px;align-items:flex-start}
.user-file-icon{font-size:15px}
.expense-msg-card{width:var(--content-w);margin:0 auto 10px;padding:12px;background:#fff;border:1px solid var(--border);border-radius:14px;box-shadow:0 4px 12px rgba(15,23,42,.04);box-sizing:border-box}
.expense-msg-title{font-size:13px;font-weight:700;margin-bottom:10px;color:var(--text-main)}
.expense-msg-row{display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:8px}
.expense-msg-left{min-width:0}
.expense-msg-merchant{font-size:15px;font-weight:700;color:#1f2329;line-height:21px;margin-bottom:4px}
.expense-msg-time{font-size:12px;color:var(--text-secondary);margin-bottom:4px}
.expense-msg-type{font-size:12px;color:var(--text-secondary)}
.expense-msg-right{text-align:right}
.expense-msg-amount{font-size:18px;font-weight:800;color:#111827;line-height:24px;margin-top:2px}
.parse-card{width:var(--content-w);margin:0 auto 10px;padding:14px;background:#fff;border:1px solid var(--border);border-radius:14px;box-shadow:0 4px 12px rgba(15,23,42,.04);box-sizing:border-box}
.parse-card-title{font-size:14px;font-weight:700;margin-bottom:10px;color:var(--text-main)}
.parse-row{display:flex;justify-content:space-between;margin-bottom:6px;font-size:13px;line-height:20px}
.parse-row span{color:var(--text-secondary);flex:0 0 68px}
.parse-row strong{color:var(--text-main);font-weight:600;text-align:right;flex:1}
.parse-match-note{margin-top:10px;padding:8px 10px;border-radius:8px;background:#eafaf2;color:#079455;font-size:12px;line-height:18px;font-weight:600}
.parse-actions{margin-top:10px;height:40px}
.parse-actions .phone-action-form{height:40px}
.parse-submit-btn{height:40px;border-radius:10px;font-size:14px;font-weight:700;width:100%;background:#1677ff;color:#fff!important;border:1px solid #1677ff}
.card{width:var(--content-w);background:#fff;border:1px solid var(--border);border-radius:14px;box-shadow:0 4px 12px rgba(15,23,42,.04);padding:12px;box-sizing:border-box;margin:0 auto 10px}
.filter-bar{width:var(--content-w);display:flex;gap:12px;overflow-x:auto;margin:20px auto 16px;padding-bottom:2px}
.filter-bar .phone-action-form{flex:0 0 auto;width:auto;height:36px}
.filter-bar button{height:36px;padding:0 16px;border-radius:18px;border:none;background:#f2f4f7;color:#1f2329;font-size:14px;font-weight:600;width:auto}
.filter-bar button.active{background:#1677ff;color:#fff}
.record-card-form{width:var(--content-w);margin:0 auto 10px;padding:0}
.record-inbox-card{width:100%;min-height:122px;padding:18px 16px;border-radius:14px;border:1px solid #e5e8ef;background:#fff;box-shadow:0 4px 12px rgba(15,23,42,.04);display:flex;justify-content:space-between;align-items:stretch;text-align:left;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;cursor:pointer;box-sizing:border-box}
.record-left{display:flex;flex-direction:column;justify-content:flex-start;min-width:0}
.record-merchant{font-size:17px;line-height:24px;font-weight:700;color:#111827;margin-bottom:10px}
.record-time{font-size:15px;line-height:20px;color:#7b8494;margin-bottom:12px}
.record-ai-ok{display:flex;align-items:center;gap:6px;font-size:14px;line-height:18px;color:#12b76a;font-weight:500}
.record-ai-icon{width:16px;height:16px;border-radius:8px;background:#12b76a;color:#fff;font-size:11px;line-height:16px;text-align:center;font-weight:700;flex:0 0 16px}
.record-ai-fail{display:flex;align-items:center;gap:6px;font-size:14px;line-height:18px;color:#e5484d;font-weight:500}
.record-ai-icon-fail{width:16px;height:16px;border-radius:8px;background:#e5484d;color:#fff;font-size:11px;line-height:16px;text-align:center;font-weight:700;flex:0 0 16px}
.record-right{display:flex;flex-direction:column;align-items:flex-end;justify-content:flex-start;min-width:116px}
.record-right .status-pill{margin-bottom:22px}
.record-amount{font-size:20px;line-height:24px;font-weight:800;color:#111827;margin-bottom:10px;white-space:nowrap}
.record-arrow{font-size:28px;line-height:20px;color:#98a2b3;font-weight:300}
.record-inbox-card .status-pill{display:inline-flex;align-items:center;justify-content:center;height:24px;padding:0 10px;border-radius:999px;font-size:13px;font-weight:700;background:#fff4e5;color:#f97316}
.record-inbox-card .pill-info{background:#eaf2ff;color:#1677ff}
.record-inbox-card .pill-success{background:#eafaf2;color:#12b76a}
.record-inbox-card .pill-danger{background:#fff1f0;color:#e5484d}
.status-pill{display:inline-flex;align-items:center;height:22px;padding:0 8px;border-radius:999px;font-size:11px;font-weight:700}
.pill-success{background:var(--success-bg);color:#079455}
.pill-warning{background:var(--warning-bg);color:#c2410c}
.pill-danger{background:var(--danger-bg);color:var(--danger)}
.pill-info{background:var(--info-bg);color:var(--info)}
.pill-neutral{background:#f2f4f7;color:var(--text-secondary)}
.info-grid{display:grid;grid-template-columns:92px 1fr;gap:8px 10px;font-size:13px;line-height:20px}
.info-label{color:var(--text-secondary)}
.info-value{color:var(--text-main);text-align:right;word-break:break-word}
.warning-bar{width:var(--content-w);margin:0 auto 10px;padding:9px 10px;border-radius:10px;border:1px solid #ffd7a3;background:var(--warning-bg);color:#c2410c;font-size:12px;box-sizing:border-box}
.upload-area{width:var(--content-w);margin:0 auto 10px;padding:16px;background:#fff;border:2px dashed var(--border-strong);border-radius:14px;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:6px;box-sizing:border-box;color:var(--primary);font-size:13px;font-weight:500}
.upload-icon{font-size:28px;line-height:1}
.upload-hint{font-size:11px;color:var(--text-tertiary);font-weight:400}
.full-btn{width:var(--content-w);height:44px;border-radius:12px;font-size:14px;font-weight:700}
.secondary-full-btn{width:var(--content-w);height:40px;border-radius:12px;font-size:14px;font-weight:600;margin-top:8px}
.phone-action-bottom .phone-action-form{width:358px;margin:0 auto}
.phone-action-bottom .phone-action-form+.phone-action-form{margin-top:8px}
.ai-status-bar{width:var(--content-w);margin:0 auto 10px;padding:10px 12px;border-radius:10px;display:flex;align-items:center;gap:8px;font-size:13px;font-weight:600;box-sizing:border-box}
.ai-status-bar.status-pending_receipt{background:var(--warning-bg);color:#c2410c;border:1px solid #ffd7a3}
.ai-status-bar.status-pending_submit{background:var(--info-bg);color:var(--info);border:1px solid #b3d4fc}
.ai-status-bar.status-submitted{background:var(--success-bg);color:#079455;border:1px solid #a7f3d0}
.ai-status-bar.status-error{background:var(--danger-bg);color:var(--danger);border:1px solid #fecaca}
.ai-status-icon{width:20px;height:20px;border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:12px;flex:0 0 20px}
@media(max-width:768px){
  html,body,.stApp,[data-testid="stAppViewContainer"]{min-height:100svh!important;height:auto!important;overflow-y:auto!important;overflow-x:hidden!important}
  .st-key-phone_shell{width:100vw!important;min-width:0!important;max-width:100vw!important;min-height:100svh!important;height:auto!important;max-height:none!important;border-radius:0!important;box-shadow:none!important;border:none!important;overflow:visible!important}
  .phone-app-v2{width:100vw!important;max-width:100vw!important;min-height:100svh!important;height:auto!important;max-height:none!important;overflow:visible!important}
  .phone-body{width:100vw!important;max-width:100vw!important;height:auto!important;max-height:none!important;overflow-y:auto!important}
  .phone-body.has-bottom-cta{width:100vw!important;max-width:100vw!important;height:auto!important;max-height:none!important;min-height:calc(100svh - 72px)!important;overflow-y:auto!important}
  .st-key-side_panel{display:none!important}
  .stTabs [data-baseweb="tab-list"]{display:none!important}
  .stTabs [data-baseweb="tab-panel"]:nth-child(2),.stTabs [data-baseweb="tab-panel"]:nth-child(3){display:none!important}
}
.expense-card{width:var(--content-w);margin:0 auto 10px;padding:14px 16px;background:#fff;border:1px solid #e5e8ef;border-radius:14px;box-shadow:0 4px 12px rgba(15,23,42,.04);box-sizing:border-box}
.expense-top{display:flex;align-items:center;justify-content:space-between;margin-bottom:8px}
.expense-foreign{font-size:12px;line-height:17px;font-weight:600;color:#8f959e}
.expense-merchant{font-size:16px;line-height:22px;font-weight:700;color:#1f2329;margin-bottom:2px}
.expense-amount{font-size:22px;line-height:28px;font-weight:800;color:#111827;letter-spacing:-.02em;margin-bottom:6px}
.expense-pay{font-size:12px;line-height:17px;color:#8f959e;margin-bottom:4px}
.expense-meta{font-size:12px;line-height:17px;color:#8f959e}
.ai-banner{width:var(--content-w);min-height:36px;margin:0 auto 10px;padding:8px 12px;border-radius:10px;display:flex;align-items:center;gap:8px;box-sizing:border-box;font-size:13px;line-height:18px;font-weight:600}
.ai-banner-icon{width:18px;height:18px;border-radius:9px;display:inline-flex;align-items:center;justify-content:center;flex:0 0 18px;font-size:12px;font-weight:800}
.ai-banner-warning{background:#fff7e8;border:1px solid #ffd7a3;color:#c2410c}
.ai-banner-warning .ai-banner-icon{background:#f97316;color:#fff}
.ai-banner-success{background:#eafaf2;border:1px solid #a7f3d0;color:#079455}
.ai-banner-success .ai-banner-icon{background:#12b76a;color:#fff}
.ai-banner-info{background:#eff6ff;border:1px solid #b3d4fc;color:#1677ff}
.ai-banner-info .ai-banner-icon{background:#1677ff;color:#fff}
.ai-banner-error{background:#fff1f0;border:1px solid #fecaca;color:#e5484d}
.ai-banner-error .ai-banner-icon{background:#e5484d;color:#fff}
.detail-section-title{width:var(--content-w);margin:12px auto 8px;font-size:15px;line-height:22px;font-weight:700;color:#1f2329}
.upload-card{width:var(--content-w);margin:0 auto 10px;padding:14px 16px;background:#fff;border:1px solid #e5e8ef;border-radius:14px;box-shadow:0 4px 12px rgba(15,23,42,.04);box-sizing:border-box}
.upload-card-title{font-size:16px;line-height:22px;font-weight:700;color:#1f2329;margin-bottom:4px}
.upload-card-desc{font-size:12px;line-height:17px;color:#8f959e;margin-bottom:12px}
.upload-box-button{width:100%;height:64px;border-radius:10px;border:1px dashed #d8dde8;background:#fbfdff;color:#1677ff;font-size:13px;font-weight:600}
.note-card{width:var(--content-w);margin:0 auto 10px;padding:14px 16px;background:#fff;border:1px solid #e5e8ef;border-radius:14px;box-shadow:0 4px 12px rgba(15,23,42,.04);box-sizing:border-box}
.note-card.error-note-card{border-color:#fecaca}
.note-card-title{font-size:16px;line-height:22px;font-weight:700;color:#1f2329;margin-bottom:10px}
.note-placeholder{height:62px;border-radius:10px;border:1px solid #e5e8ef;background:#fff;color:#b0b7c3;font-size:13px;line-height:18px;padding:12px;box-sizing:border-box}
.form-card{width:var(--content-w);margin:0 auto 12px;background:#fff;border:1px solid #e5e8ef;border-radius:14px;box-shadow:0 4px 12px rgba(15,23,42,.04);box-sizing:border-box;overflow:hidden}
.form-row{min-height:40px;padding:0 14px;display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid #edf0f5;font-size:13px;line-height:18px;box-sizing:border-box}
.form-row:last-child{border-bottom:none}
.form-row span:first-child{color:#646a73}
.form-row span:last-child{color:#1f2329;text-align:right}
.uploaded-card{width:var(--content-w);margin:0 auto 10px;padding:14px 16px;background:#fff;border:1px solid #e5e8ef;border-radius:14px;box-shadow:0 4px 12px rgba(15,23,42,.04);box-sizing:border-box}
.uploaded-card-title{font-size:16px;line-height:22px;font-weight:700;color:#1f2329;margin-bottom:10px}
.uploaded-file{min-height:70px;border:1px solid #e5e8ef;border-radius:10px;padding:10px;display:flex;align-items:center;box-sizing:border-box;margin-bottom:10px}
.file-icon{width:38px;height:38px;border-radius:8px;background:#eaf2ff;color:#1677ff;display:flex;align-items:center;justify-content:center;flex:0 0 38px;margin-right:10px;font-size:18px}
.file-main{flex:1;min-width:0}
.file-name{font-size:13px;line-height:18px;font-weight:600;color:#1f2329;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.file-meta{font-size:11px;line-height:16px;color:#8f959e;margin-top:2px}
.file-link{font-size:12px;line-height:16px;color:#1677ff;font-weight:600;margin-top:4px}
.file-arrow{font-size:22px;color:#8f959e;padding-left:8px}
.add-receipt-box{height:36px;border-radius:8px;border:1px dashed #d8dde8;color:#1677ff;font-size:13px;font-weight:600;display:flex;align-items:center;justify-content:center}
.phone-body.has-bottom-cta{height:calc(867px - 24px - 56px - 72px);padding:12px 16px 12px;overflow-y:auto;box-sizing:border-box}
.phone-bottom-cta{width:390px;height:72px;background:rgba(255,255,255,.98);border-top:1px solid #edf0f5;padding:10px 16px 8px;box-sizing:border-box}
.phone-bottom-cta .phone-action-form{height:40px;margin:0 auto;display:block}
.bottom-cta{width:var(--content-w);height:40px;border-radius:10px;background:#1677ff;color:#fff!important;border:1px solid #1677ff;font-size:15px;font-weight:700}
.policy-card{width:var(--content-w);margin:12px auto 0;padding:14px 16px;background:#fff;border:1px solid #e5e8ef;border-radius:14px;box-shadow:0 4px 12px rgba(15,23,42,.04);box-sizing:border-box}
.policy-title{font-size:16px;line-height:22px;font-weight:700;color:#1f2329;margin-bottom:12px}
.policy-row{min-height:36px;display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid #edf0f5;font-size:13px;line-height:18px}
.policy-row:last-of-type{border-bottom:none}
.policy-row span{color:#646a73}
.policy-row strong{color:#1f2329;font-weight:600;text-align:right}
.policy-desc{margin-top:12px;padding:10px 12px;background:#fff7e8;color:#c2410c;border-radius:10px;font-size:13px;line-height:20px}
.policy-list{display:flex;flex-direction:column;gap:8px;color:#646a73;font-size:13px;line-height:20px}
</style>
"""


# ═══ HTML Builders ═══════════════════════════════════════════════

def _status_bar():
    return '<div class="phone-status"><div>9:41</div><div>\u25ae\u25ae\u25ae \u2318 \u25b0</div></div>'

def _nav(title, subtitle=None, back_action=None, back_rid=None, more=False):
    back = ""
    if back_action:
        back = '<div class="phone-back-wrap">' + phone_action_form("\u2039", back_action, "phone-back-btn", rid=back_rid, name=f"back_{back_action}") + '</div>'
    sub = f'<div class="phone-subtitle">{esc(subtitle)}</div>' if subtitle else ""
    more_h = '<div class="phone-more">\u2026</div>' if more else ""
    return f'<div class="phone-nav">{back}<div><div class="phone-title">{esc(title)}</div>{sub}</div>{more_h}</div>'


# ═══ Chat Page ═══════════════════════════════════════════════════

def _render_card_html(msg: dict) -> str:
    """Render a `type: card` message as HTML."""
    title = esc(msg.get("title", ""))
    subtitle = esc(msg.get("subtitle", ""))
    hint = esc(msg.get("hint", ""))
    status = esc(msg.get("status", ""))
    fields = msg.get("fields", [])
    actions = msg.get("actions", [])

    fields_html = ""
    for label, value in fields:
        fields_html += f'<div class="form-row"><span>{esc(label)}</span><span>{esc(str(value))}</span></div>'

    actions_html = ""
    if actions:
        actions_html = '<div class="card-actions" style="margin-top:10px;">' + "".join(
            f'<span class="phone-btn btn-card" style="margin-right:8px;display:inline-block;">{esc(a)}</span>' for a in actions
        ) + '</div>'

    subtitle_html = f'<div class="card-subtitle" style="font-size:12px;color:#646a73;margin-bottom:8px;">{subtitle}</div>' if subtitle else ""
    hint_html = f'<div class="card-hint" style="font-size:11px;color:#8f959e;margin-top:8px;">{hint}</div>' if hint else ""
    status_html = f'<div class="card-status" style="margin-bottom:8px;font-weight:600;color:#1677ff;font-size:12px;">{status}</div>' if status else ""

    return f'''<div class="card" style="width:100%;padding:12px;box-sizing:border-box;background:#fff;border:1px solid #e5e8ef;border-radius:14px;box-shadow:0 4px 12px rgba(15,23,42,.04);">
    <div class="card-title" style="font-size:15px;font-weight:600;margin-bottom:6px;">{title}</div>
    {status_html}
    {subtitle_html}
    {fields_html}
    {actions_html}
    {hint_html}
</div>'''


def _render_expense_card_message(msg: dict) -> str:
    rec = find_record(msg.get("record_id")) or st.session_state.get("reimbursement_records", [{}])[0]
    status = rec.get("status", STATUS_PENDING_RECEIPT)
    pill_cls = get_pill_class(status)
    s_label = status_label(status)
    return f'''<div class="expense-msg-card">
<div class="expense-msg-title">🛎️ 检测到一笔酒店消费待补票</div>
<div class="expense-msg-row">
<div class="expense-msg-left">
<div class="expense-msg-merchant">{esc(rec.get("merchant_name", ""))}</div>
<div class="expense-msg-time">消费时间 {esc(rec.get("transaction_time", ""))}</div>
<div class="expense-msg-type">{esc(rec.get("expense_type", ""))}</div>
</div>
<div class="expense-msg-right">
<div class="status-pill {pill_cls}">{esc(s_label)}</div>
<div class="expense-msg-amount">{esc(detail_amount_text(rec))}</div>
</div>
</div>
{phone_action_form("查看详情", "open_detail", "phone-btn btn-card btn-secondary", rid=rec.get("id"), name="chat_expense_detail")}
</div>'''


def _render_parse_card_message(msg: dict) -> str:
    rec = find_record(msg.get("record_id")) or st.session_state.get("reimbursement_records", [{}])[0]
    merchant = esc(rec.get("merchant_name", ""))
    expense_type = esc(rec.get("expense_type", ""))
    expense_description = esc(rec.get("expense_description", "未填写"))
    tax_rate = esc(rec.get("tax_rate", "未填写"))
    return f'''<div class="parse-card">
<div class="parse-card-title">🧾 票据解析完成</div>
<div class="parse-row"><span>商户</span><strong>{merchant}</strong></div>
<div class="parse-row"><span>费用类别</span><strong>{expense_type}</strong></div>
<div class="parse-row"><span>费用说明</span><strong>{expense_description}</strong></div>
<div class="parse-row"><span>税率</span><strong>{tax_rate}</strong></div>
<div class="parse-match-note">已匹配到该笔消费记录，可立即提交报销。</div>
<div class="parse-actions">{phone_action_form("立即提交", "chat_confirm_submit", "parse-submit-btn", rid=rec.get("id"), name="chat_parse_submit")}</div>
</div>'''


# ═══ Chat Expense Card (unified with home ticket-card) ═════════════

def render_chat_expense_card_only(record_id):
    """Render only the inner ticket-card HTML (no avatar wrapper)."""
    rec = find_record(record_id)
    if not rec:
        return ""

    rid = rec["id"]
    merchant = rec.get("merchant_name", "")
    expense_type = rec.get("expense_type", "")
    transaction_time = rec.get("transaction_time", "")
    amount = detail_amount_text(rec)
    status = rec.get("status", "")
    pill_cls = get_pill_class(status)
    status_text = status_label(status)

    return f'''
  <div class="ticket-card">
    <div class="ticket-title-row">
      <div class="ticket-title">🔔 有一笔消费待补票</div>
      <div class="status-pill {pill_cls}">{esc(status_text)}</div>
    </div>
    <div class="ticket-merchant">{esc(merchant)}</div>
    <div class="ticket-amount-row">
      <div>
        <div class="ticket-meta-label">交易时间</div>
        <div class="ticket-meta">{esc(transaction_time)}</div>
      </div>
      <div class="ticket-amount">{esc(amount)}</div>
    </div>
    <div class="ticket-tag">{esc(expense_type)}</div>
    <div class="ticket-actions single">
      {phone_action_form("查看详情", "open_detail", "phone-btn btn-card btn-primary", rid=rid, name=f"chat_card_detail_{rid}")}
    </div>
  </div>'''


def render_chat_expense_card(record_id):
    """Render a chat expense card using the same ticket-card as the home page.""" 
    return render_chat_expense_card_only(record_id)


def render_user_file_message(msg: dict) -> str:
    filename = esc(msg.get("filename", ""))
    return f'''<div class="chat-user-row">
  <div class="chat-bubble user-bubble chat-user-file"><span class="user-file-icon">📎</span><span>{filename}</span></div>
  <div class="user-avatar">我</div>
</div>'''


def render_amount_mismatch_card(_record_id=None) -> str:
    target = find_record("record_001") or st.session_state.get("reimbursement_records", [{}])[0]
    target_id = target.get("id", "record_001")
    # Ensure detail page shows the "pending_submit" view for amount mismatch.
    if target.get("status") == STATUS_PENDING_RECEIPT:
        target["status"] = STATUS_PENDING_SUBMIT
        target["ai_check_message"] = "检测到金额差异，已补票完成，可提交报销。"
        target["attachments"] = target.get("attachments", []) or ["Tokyo_Hilton_Receipt.jpg"]
    return f'''<div class="ticket-card" style="border-color:#ffd7a3;box-shadow:0 4px 12px rgba(249,115,22,.08);">
  <div class="ticket-title-row">
    <div class="ticket-title">⚠️ 金额差异，需要确认</div>
  </div>
  <div class="parse-row" style="margin-bottom:6px;"><span style="color:#646a73;flex:0 0 80px;">交易金额</span><strong style="text-align:right;">96 USD</strong></div>
  <div class="parse-row" style="margin-bottom:6px;"><span style="color:#646a73;flex:0 0 80px;">票据金额</span><strong style="text-align:right;">88 USD</strong></div>
  <div class="parse-row" style="margin-bottom:6px;"><span style="color:#646a73;flex:0 0 80px;">差异</span><strong style="text-align:right;color:#c2410c;">8 USD</strong></div>
  <div class="parse-row" style="margin-bottom:10px;"><span style="color:#646a73;flex:0 0 80px;">匹配置信度</span><strong style="text-align:right;">72%</strong></div>
  <div class="ticket-actions single">
    {phone_action_form("查看详情", "open_amount_mismatch_detail", "phone-btn btn-card btn-secondary", rid=target_id, name="mismatch_detail")}
  </div>
</div>'''

def render_payment_failed_card(_record_id=None) -> str:
    return f'''<div class="ticket-card" style="border-color:#fecaca;box-shadow:0 4px 12px rgba(229,72,77,.08);">
  <div class="ticket-title-row">
    <div class="ticket-title">❌ 支付失败：超过酒店单笔限额</div>
  </div>
  <div class="parse-row" style="margin-bottom:6px;"><span style="color:#646a73;flex:0 0 80px;">商户</span><strong style="text-align:right;">Tokyo Hotel</strong></div>
  <div class="parse-row" style="margin-bottom:6px;"><span style="color:#646a73;flex:0 0 80px;">交易金额</span><strong style="text-align:right;">1500 USD</strong></div>
  <div class="parse-row" style="margin-bottom:10px;"><span style="color:#646a73;flex:0 0 80px;">规则</span><strong style="text-align:right;">酒店类单笔限额 1000 USD</strong></div>
  <div style="font-size:12px;line-height:18px;color:#8f959e;margin-bottom:12px;">当前交易金额超过酒店单笔限额 1000 USD，付款被拒绝。</div>
  <div class="ticket-actions single">
    {phone_action_form("查看差旅政策", "open_travel_policy", "phone-btn btn-card btn-primary", rid="record_005", name="payment_failed_policy")}
  </div>
</div>'''



def render_assistant_text_message(content: str) -> str:
    return f'''<div class="chat-row chat-assistant-row">
  <div class="bot-avatar">🤖</div>
  <div class="chat-bubble assistant-bubble">{esc(content)}</div>
</div>'''


def render_user_text_message(content: str) -> str:
    return f'''<div class="chat-user-row">
  <div class="chat-bubble user-bubble">{esc(content)}</div>
  <div class="user-avatar">我</div>
</div>'''


def _render_chat_message(msg: dict) -> str:
    r = msg.get("role", "")
    t = msg.get("type", "")
    if t == "text":
        if r == "user":
            return render_user_text_message(msg.get("content", ""))
        return render_assistant_text_message(msg.get("content", ""))
    if t == "receipt_upload":
        return render_user_file_message(msg)
    if t == "expense_card":
        return f'''<div class="chat-row chat-assistant-row"><div class="bot-avatar">{esc("🤖")}</div>{render_chat_expense_card(msg.get("record_id"))}</div>'''
    if t == "file":
        return render_user_file_message(msg)
    if t == "parse_card":
        return f'''<div class="chat-row chat-assistant-row"><div class="bot-avatar">{esc("🤖")}</div>{_render_parse_card_message(msg)}</div>'''
    if t == "amount_mismatch_card":
        return f'''<div class="chat-row chat-assistant-row"><div class="bot-avatar">{esc("🤖")}</div>{render_amount_mismatch_card(msg.get("record_id"))}</div>'''
    if t == "payment_failed_card":
        return f'''<div class="chat-row chat-assistant-row"><div class="bot-avatar">{esc("🤖")}</div>{render_payment_failed_card(msg.get("record_id"))}</div>'''
    if t == "time_chip":
        return f'''<div class="chat-date">{esc(msg.get("time",""))}</div>'''
    if t == "card":
        return f'''<div class="chat-row chat-assistant-row"><div class="bot-avatar">{esc("🤖")}</div>{_render_card_html(msg)}</div>'''
    if r == "user":
        c = msg.get("content", msg.get("filename", ""))
        return render_user_text_message(c)
    return ""


def render_chat_html():
    msgs_html = ""
    for msg in st.session_state.get("chat_messages", []):
        msgs_html += render_assistant_text_message(msg.get("text", ""))
    for msg in st.session_state.get("messages", []):
        msgs_html += _render_chat_message(msg)

    # 首页待补票卡片：仅当该记录尚未被推送过消费卡片才显示，避免主流程重复
    records = st.session_state.get("reimbursement_records", [])
    home_card_html = ""
    pushed_rids = {m.get("record_id") for m in st.session_state.get("messages", []) if m.get("type") == "expense_card"}
    if records and records[0]["id"] not in pushed_rids:
        home_card_html = f'<div class="chat-row"><div class="bot-avatar">🤖</div>{render_chat_expense_card_only(records[0]["id"])}</div>'


    quick = '<div class="quick-pills">' + phone_action_form("📋 报销记录", "open_records", "phone-btn", name="quick_records") + '</div>'
    welcome = "你好，我是你的 AI 差旅支出助手。出差刷员工卡支付后，我会在钉钉里提醒你补票，帮你识别票据、填好报销，并在异常时告诉你怎么处理。"

    return f'''<div class="phone-app-v2">
{_status_bar()}
{_nav("差旅支出助手")}
<div class="phone-body has-bottom">
<div class="chat-date">今天 09:30</div>
<div class="chat-row"><div class="bot-avatar">🤖</div><div class="chat-welcome">{esc(welcome)}</div></div>
{home_card_html}
{msgs_html}
</div>
<div class="phone-bottom">
<div class="quick-title">快捷入口</div>
{quick}
<div class="input-bar"><div class="input-bar-icon">+</div><div class="input-bar-field">发送消息</div><div class="input-bar-send">➜</div></div>
<div class="home-indicator"></div>
</div>
</div>'''

def render_records_html():
    current = st.session_state.get("record_filter", "all")
    records = st.session_state.get("reimbursement_records", [])

    if current == "all":
        filtered = records
    else:
        filtered = [r for r in records if r.get("status") == current]
    filtered = sorted(filtered, key=lambda r: r.get("transaction_time", ""), reverse=True)

    # Filter chips
    chips_data = [
        ("all", "\u5168\u90e8"),
        (STATUS_PENDING_RECEIPT, "\u5f85\u8865\u7968"),
        (STATUS_PENDING_SUBMIT, "\u5f85\u63d0\u4ea4"),
        (STATUS_SUBMITTED, "\u5df2\u63d0\u4ea4"),
        (STATUS_ERROR, "\u5f02\u5e38"),
    ]
    chips_html = '<div class="filter-bar">' + "".join(
        phone_action_form(l, "set_filter", f"phone-btn{' active' if v==current else ''}", filter_value=v, name=f"filter_{v}")
        for v, l in chips_data
    ) + '</div>'

    # Inbox cards: 整卡可点击进入详情
    cards_html = ""
    for r in filtered:
        status = r.get("status", STATUS_PENDING_RECEIPT)
        pill_cls = get_pill_class(status)
        s_label = status_label(status)
        ai_status_html = (f'''<div class="record-ai-fail"><span class="record-ai-icon-fail">!</span><span>AI校验未通过</span></div>''' if status == STATUS_ERROR else f'''<div class="record-ai-ok"><span class="record-ai-icon">\u2713</span><span>AI\u6821\u9a8c\u901a\u8fc7</span></div>''')
        cards_html += f'''<form class="record-card-form" method="get" action="" target="_self">
<input type="hidden" name="pa" value="open_detail">
<input type="hidden" name="_t" value="{int(time_mod.time()*1000)}">
<input type="hidden" name="rid" value="{esc(r["id"])}">
<button type="submit" class="record-inbox-card">
<div class="record-left">
<div class="record-merchant">{esc(r.get("merchant_name", ""))}</div>
<div class="record-time">{esc(r.get("transaction_time", ""))}</div>
{ai_status_html}
</div>
<div class="record-right">
<div class="status-pill {pill_cls}">{esc(s_label)}</div>
<div class="record-amount">{esc(list_amount_text(r))}</div>
<div class="record-arrow">\u203a</div>
</div>
</button>
</form>'''

    return f'''<div class="phone-app-v2">
{_status_bar()}
{_nav("\u62a5\u9500\u8bb0\u5f55", back_action="open_chat")}
<div class="phone-body" style="padding:0 16px 16px;">{chips_html}{cards_html}</div>
</div>'''



# ═══ Travel Policy Page ═══════════════════════════════════════

def render_travel_policy_html():
    return f'''<div class="phone-app-v2">
{_status_bar()}
{_nav("差旅政策", back_action="open_chat")}
<div class="phone-body">
<div class="policy-card">
<div class="policy-title">酒店消费政策</div>
<div class="policy-row">
<span>单笔限额</span>
<strong>1000 USD</strong>
</div>
<div class="policy-row">
<span>适用范围</span>
<strong>境外酒店住宿</strong>
</div>
<div class="policy-row">
<span>超额处理</span>
<strong>需补充说明并经财务复核</strong>
</div>
<div class="policy-desc">
当酒店类消费单笔金额超过公司差旅政策限额时，支付可能被拒绝，或报销时需要补充业务说明和审批材料。
</div>
</div>
<div class="policy-card">
<div class="policy-title">建议处理方式</div>
<div class="policy-list">
<div>1. 检查是否选择了正确的员工卡或支付方式。</div>
<div>2. 如确为业务必要支出，请补充说明。</div>
<div>3. 金额超过政策限额时，提交后将进入财务复核。</div>
</div>
</div>
</div>
</div>'''

# ═══ Unified Consume Detail Page ════════════════════════════════

def render_consume_detail_html():
    rid = st.session_state.get("selected_record_id") or "record_001"
    rec = find_record(rid) or st.session_state.get("reimbursement_records", [{}])[0]
    status = rec.get("status", STATUS_PENDING_RECEIPT)
    cta = get_cta_action(status)

    cta_label = cta["label"]
    cta_action = cta["action"]
    cta_style = cta["style"]

    if status == STATUS_PENDING_RECEIPT:
        cta_label = "立即提交"
        cta_action = "upload_receipt"
        cta_style = "btn-primary"
    elif status == STATUS_PENDING_SUBMIT:
        cta_label = "立即提交"
        cta_action = "confirm_submit"
        cta_style = "btn-primary"
    elif status == STATUS_SUBMITTED:
        cta_label = "重新提交"
        cta_action = "confirm_submit"
        cta_style = "btn-primary"
    elif status == STATUS_ERROR:
        cta_label = "提交异常说明"
        cta_action = "submit_error_note"
        cta_style = "btn-primary"

    status_text = status_label(status)
    pill_cls = get_pill_class(status)

    merchant = esc(rec.get("merchant_name", ""))
    transaction_time = esc(rec.get("transaction_time", ""))
    expense_type = esc(rec.get("expense_type", "--"))
    expense_description = esc(rec.get("expense_description", "未填写"))
    tax_rate = esc(rec.get("tax_rate", "未填写"))
    note = esc(rec.get("note", "未填写"))
    ai_msg = rec.get("ai_check_message", "")
    attachments = rec.get("attachments", []) or []

    def _ai_banner(cls_text, icon, text):
        return (
            f'<div class="ai-banner ai-banner-{cls_text}">'
            f'<span class="ai-banner-icon">{icon}</span>'
            f'<span>{text}</span></div>'
        )

    def _form_row(label, value):
        return f'<div class="form-row"><span>{label}</span><span>{value}\u203a</span></div>'

    # ── Expense card (same for all states) ───────────────────────
    expense_html = f'''<div class="expense-card">
<div class="expense-top">
<div class="expense-foreign">\u5883\u5916\u6d88\u8d39</div>
<div class="status-pill {pill_cls}">{esc(status_text)}</div>
</div>
<div class="expense-merchant">{merchant}</div>
<div class="expense-amount">{esc(detail_amount_text(rec))}</div>
<div class="expense-pay">\u4f7f\u7528 Mia Tao\'s card \u2022\u2022\u2022\u2022 9423 \u652f\u4ed8</div>
<div class="expense-meta">{transaction_time}</div>
</div>'''

    # ── AI banners per status ────────────────────────────────────
    if status == STATUS_PENDING_RECEIPT:
        banners_html = (
            _ai_banner("warning", "!", "\u8bf7\u4e0a\u4f20\u6536\u636e\uff0c\u5b8c\u6210\u8865\u7968\u540e\u65b9\u53ef\u7ee7\u7eed\u62a5\u9500\u6d41\u7a0b")
            + _ai_banner("success", "\u2713", "AI\u6821\u9a8c\u901a\u8fc7")
        )
    elif status == STATUS_PENDING_SUBMIT:
        banners_html = _ai_banner("success", "\u2713", "AI\u6821\u9a8c\u901a\u8fc7")
    elif status == STATUS_SUBMITTED:
        banners_html = _ai_banner("success", "\u2713", "AI\u6821\u9a8c\u901a\u8fc7 \u2014 \u5df2\u63d0\u4ea4\u81f3\u62a5\u9500\u7cfb\u7edf")
    else:  # error
        err_text = esc(ai_msg) if ai_msg and ai_msg != "\u5f02\u5e38" else "MCC Code\uff1a\u6d88\u8d39\u5546\u6237\u7c7b\u578b\u4e0d\u7b26\u5408\u516c\u53f8\u653f\u7b56"
        banners_html = _ai_banner("error", "!", err_text)

    detail_title_html = '<div class="detail-section-title">\u8d39\u7528\u8be6\u60c5</div>'

    # ── pending_receipt: upload card + note card + form card ─────
    upload_btn = phone_action_form("\u70b9\u51fb\u4e0a\u4f20", cta_action, "upload-box-button", rid=rec.get("id"), name=f"upload_{status}")
    upload_card_html = f'''<div class="upload-card">
<div class="upload-card-title">\u4e0a\u4f20\u6536\u636e\uff08\u5fc5\u586b\uff09</div>
<div class="upload-card-desc">\u8bf7\u4e0a\u4f20\u7535\u5b50\u6536\u636e\u6216\u7eb8\u8d28\u6536\u636e\u7167\u7247</div>
{upload_btn}
</div>'''

    note_card_html = f'''<div class="note-card">
<div class="note-card-title">\u8865\u5145\u8bf4\u660e\uff08\u9009\u586b\uff09</div>
<div class="note-placeholder">\u8bf7\u8bf4\u660e\u672c\u6b21\u652f\u51fa\u7684\u60c5\u51b5...</div>
</div>'''

    pending_form_card_html = f'''<div class="form-card">
{_form_row("\u5546\u6237", merchant)}
{_form_row("\u8d39\u7528\u7c7b\u522b", expense_type)}
{_form_row("\u8d39\u7528\u8bf4\u660e", expense_description)}
{_form_row("\u7a0e\u7387", tax_rate)}
</div>'''

    # ── pending_submit / submitted: uploaded card + form card ────
    file_name = attachments[0] if attachments else "INV_20260610_001.pdf"
    file_meta = f"2.4 MB \u00b7 {transaction_time}"
    uploaded_card_html = f'''<div class="uploaded-card">
<div class="uploaded-card-title">\u5df2\u4e0a\u4f20\u6536\u636e\uff08\u5fc5\u586b\uff09</div>
<div class="uploaded-file">
<div class="file-icon">\U0001f4c4</div>
<div class="file-main">
<div class="file-name">{esc(file_name)}</div>
<div class="file-meta">{esc(file_meta)}</div>
<div class="file-link">\u67e5\u770b\u6536\u636e</div>
</div>
<div class="file-arrow">\u203a</div>
</div>
<div class="add-receipt-box">\u2295 \u6dfb\u52a0\u65b0\u7684\u6536\u636e</div>
</div>'''

    submit_form_card_html = f'''<div class="form-card">
{_form_row("\u5546\u6237", merchant)}
{_form_row("\u8d39\u7528\u7c7b\u522b", expense_type)}
{_form_row("\u8d39\u7528\u8bf4\u660e", expense_description)}
{_form_row("\u7a0e\u7387", tax_rate)}
{_form_row("\u5907\u6ce8", note)}
</div>'''

    error_form_card_html = f'''<div class="form-card">
{_form_row("\u5546\u6237", merchant)}
{_form_row("\u8d39\u7528\u7c7b\u522b", expense_type)}
{_form_row("\u8d39\u7528\u8bf4\u660e", expense_description)}
{_form_row("\u7a0e\u7387", tax_rate)}
</div>'''

    error_note_card_html = '''<div class="note-card error-note-card">
<div class="note-card-title">补充说明（必填）</div>
<div class="note-placeholder">请说明该笔消费的业务背景或特殊原因...</div>
</div>'''

    # ── Assemble content per status ──────────────────────────────
    if status == STATUS_PENDING_RECEIPT:
        content_html = expense_html + banners_html + detail_title_html + upload_card_html + note_card_html + pending_form_card_html
    elif status == STATUS_PENDING_SUBMIT:
        content_html = expense_html + banners_html + detail_title_html + uploaded_card_html + submit_form_card_html
    elif status == STATUS_SUBMITTED:
        content_html = expense_html + banners_html + detail_title_html + uploaded_card_html + submit_form_card_html
    else:  # error
        content_html = expense_html + banners_html + detail_title_html + error_note_card_html + error_form_card_html

    cta_btn = phone_action_form(cta_label, cta_action, f"phone-btn bottom-cta {cta_style}", rid=rec.get("id"), name=f"detail_cta_{status}")

    return f'''<div class="phone-app-v2">
{_status_bar()}
{_nav("\u6d88\u8d39\u8be6\u60c5", back_action="open_records")}
<div class="phone-body has-bottom-cta">
{content_html}
</div>
<div class="phone-bottom-cta">{cta_btn}<div class="home-indicator"></div></div>
</div>'''

def render_phone_app_html():
    page = st.session_state.get("current_phone_page", "chat")
    if page == "reimbursement_list":
        return render_records_html()
    if page in ("reimbursement_detail", "supplement_material", "consume_detail"):
        return render_consume_detail_html()
    if page == "travel_policy":
        return render_travel_policy_html()
    return render_chat_html()


def render_phone_shell():
    # Force state sync hook — ensures Streamlit tracks this render as
    # dependent on session_state changes from sidebar or phone clicks
    _ = st.session_state.get("ui_version", 0)
    st.markdown(PHONE_CSS, unsafe_allow_html=True)
    with st.container(key="phone_shell"):
        st.markdown(render_phone_app_html(), unsafe_allow_html=True)
