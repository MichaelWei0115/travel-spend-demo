"""
H5 Pages - DingTalk Mobile-Style Interactive Pages
===================================================
All H5 pages are rendered with Streamlit native components.
Every button is a real st.button() that reliably captures clicks.
Styled to look like DingTalk embedded H5 pages.

Pages:
- reimbursement_list: AI报销校验 list page with filter tabs and compact cards
- reimbursement_detail: 校验详情 detail page with segmented info cards
- supplement_material: 补充材料 form page with upload areas and submit
"""

import streamlit as st
from demo_actions import get_record, get_filtered_records, handle_demo_action
from reimbursement_data import (
    get_status_label, get_status_color, get_pill_class,
    derive_ai_check_result, derive_sync_status,
    format_amount, format_sync_time,
    STATUS_PENDING_RECEIPT, STATUS_PENDING_SUBMIT, STATUS_SUBMITTED, STATUS_ERROR,
)
from feedback import show_success_toast, show_error_toast, show_info_toast


# =============================================================================
# Shared: H5 page header with back button (DingTalk style)
# =============================================================================

def _render_h5_header(title, back_action="go_back", show_right_icon=False):
    """Render a standard DingTalk-style H5 page header."""
    st.html(f'''
    <div style="
        display:flex; align-items:center; justify-content:space-between;
        padding: 12px 16px 8px; background: #fff;
        border-bottom: 1px solid #f0f0f0;
    ">
        <div style="width:40px;"></div>
        <div style="font-size:17px; font-weight:600; color:#1D2129; text-align:center; flex:1;">
            {title}
        </div>
        <div style="width:40px;"></div>
    </div>
    ''')
    # Streamlit back button (functional)
    if st.button("\u2190 \u8fd4\u56de", key=f"h5_back_{title}", use_container_width=False):
        handle_demo_action(back_action)
        st.rerun()


# =============================================================================
# Reimbursement List Page
# =============================================================================

def render_reimbursement_list_page():
    """Render the reimbursement records list page - DingTalk mobile style."""
    _render_h5_header("AI\u62a5\u9500\u6821\u9a8c", "go_back")

    # --- Filter tabs (horizontal scrollable) ---
    all_records = st.session_state.reimbursement_records
    counts = {
        "all": len(all_records),
        "pending_receipt": len([r for r in all_records if r.get("status") == STATUS_PENDING_RECEIPT]),
        "pending_submit": len([r for r in all_records if r.get("status") == STATUS_PENDING_SUBMIT]),
        "submitted": len([r for r in all_records if r.get("status") == STATUS_SUBMITTED]),
        "error": len([r for r in all_records if r.get("status") == STATUS_ERROR]),
    }
    current_filter = st.session_state.get("record_filter", "all")

    filter_options = [
        ("all", f"\u5168\u90e8 {counts['all']}"),
        ("pending_receipt", f"\u5f85\u8865\u7968 {counts['pending_receipt']}"),
        ("pending_submit", f"\u5f85\u63d0\u4ea4 {counts['pending_submit']}"),
        ("submitted", f"\u5df2\u63d0\u4ea4 {counts['submitted']}"),
        ("error", f"\u5f02\u5e38 {counts['error']}"),
    ]

    # Filter tabs - horizontal chip bar (DingTalk style)
    chips_html = '<div style="display:flex;gap:8px;padding:8px 16px;overflow-x:auto;background:#fff;border-bottom:1px solid #E9EAEC;-webkit-overflow-scrolling:touch;">'
    for key, label in filter_options:
        active = key == current_filter
        bg = "#1677FF" if active else "#F7F8FA"
        color = "#fff" if active else "#4E5969"
        border = "none" if active else "1px solid #D9DDE3"
        chips_html += f'<div style="height:32px;padding:0 12px;border-radius:16px;background:{bg};color:{color};border:{border};font-size:13px;font-weight:500;display:flex;align-items:center;white-space:nowrap;flex-shrink:0;">{label}</div>'
    chips_html += '</div>'
    st.html(chips_html)
    # Functional buttons (hidden visual, small)
    filter_cols = st.columns(len(filter_options))
    for col, (key, label) in zip(filter_cols, filter_options):
        with col:
            btn_type = "primary" if key == current_filter else "secondary"
            if st.button(label, key=f"filter_{key}", type=btn_type, use_container_width=True):
                st.session_state.record_filter = key
                st.rerun()

    # --- Banner for pending_receipt ---
    if current_filter == "pending_receipt" and counts["pending_receipt"] > 0:
        st.html('''
        <div style="margin:8px 12px; padding:10px 14px; background:#FFF7E6; border:1px solid #FFE0B2;
                    border-radius:8px; font-size:13px; color:#E65100;">
            <span style="margin-right:6px;">&#9888;</span>
            \u8bf7\u5c3d\u5feb\u4e0a\u4f20\u7968\u636e\uff0c\u4ee5\u514d\u5f71\u54cd\u62a5\u9500\u8fdb\u5ea6\u3002
        </div>
        ''')

    # --- Record cards ---
    records = get_filtered_records(current_filter)

    if not records:
        st.html('''
        <div style="text-align:center; padding:40px 20px; color:#86909C;">
            <div style="font-size:32px; margin-bottom:8px;">&#128203;</div>
            <div style="font-size:14px;">\u6682\u65e0\u8bb0\u5f55</div>
        </div>
        ''')
        return

    for rec in records:
        _render_list_card(rec)


def _render_list_card(rec):
    """Render a single record card in the list view."""
    status = rec.get("status", "")
    status_label = get_status_label(status)
    status_color = get_status_color(status)
    pill_class = get_pill_class(status)

    # Card HTML (DingTalk compact style)
    st.html(f'''
    <div style="background:#fff; border-radius:12px; margin:8px 12px; padding:14px 16px;
                box-shadow:0 1px 4px rgba(0,0,0,0.04); position:relative;">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
            <span style="font-size:15px; font-weight:600; color:#1D2129;">{rec["merchant_name"]}</span>
            <span style="font-size:12px; padding:2px 8px; border-radius:10px;
                         background:{status_color}15; color:{status_color}; font-weight:500;">
                {status_label}
            </span>
        </div>
        <div style="display:flex; justify-content:space-between; align-items:baseline;">
            <span style="font-size:13px; color:#4E5969;">{rec["expense_type"]} | {rec.get("transaction_time", "--")}</span>
            <span style="font-size:16px; font-weight:700; color:#1D2129;">{format_amount(rec["amount"], rec["currency"])}</span>
        </div>
    </div>
    ''')

    # CTA button row
    cta = _get_cta_for_record(rec)
    col1, col2 = st.columns([3, 2])
    with col1:
        if st.button(f"\u67e5\u770b\u8be6\u60c5", key=f"list_detail_{rec['id']}", use_container_width=True):
            st.session_state.selected_record_id = rec["id"]
            handle_demo_action("view_record_detail", {"record_id": rec["id"]})
    with col2:
        if cta:
            if st.button(cta["label"], key=f"list_cta_{rec['id']}", type="primary", use_container_width=True):
                handle_demo_action(cta["action"], {"record_id": rec["id"]})


def _get_cta_for_record(rec):
    """Return CTA config based on record status."""
    status = rec.get("status", "")
    if status == STATUS_PENDING_RECEIPT:
        return {"label": "\u4e0a\u4f20\u7968\u636e", "action": "go_supplement"}
    elif status == STATUS_PENDING_SUBMIT:
        return {"label": "\u63d0\u4ea4\u62a5\u9500", "action": "confirm_single_sync"}
    elif status == STATUS_ERROR:
        return {"label": "\u91cd\u65b0\u5904\u7406", "action": "retry_process"}
    return None


# =============================================================================
# Reimbursement Detail Page
# =============================================================================

def render_reimbursement_detail_page():
    """Render the detail page for a single reimbursement record."""
    _render_h5_header("\u6821\u9a8c\u8be6\u60c5", "go_back_to_list")

    rid = st.session_state.get("selected_record_id")
    rec = get_record(rid) if rid else None

    if not rec:
        st.html('''
        <div style="text-align:center; padding:40px 20px; color:#86909C;">
            <div style="font-size:14px;">\u8bb0\u5f55\u4e0d\u5b58\u5728</div>
        </div>
        ''')
        return

    status = rec.get("status", "")
    status_label = get_status_label(status)
    status_color = get_status_color(status)
    ai_check = derive_ai_check_result(status)
    sync_st = derive_sync_status(status)

    # --- Status header ---
    st.html(f'''
    <div style="background: linear-gradient(135deg, {status_color}15 0%, {status_color}08 100%);
                border-radius:12px; margin:8px 12px; padding:16px;
                border-left:4px solid {status_color};">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <div>
                <div style="font-size:17px; font-weight:700; color:#1D2129; margin-bottom:4px;">
                    {rec["merchant_name"]}
                </div>
                <div style="font-size:13px; color:#4E5969;">
                    {rec["expense_type"]} | {rec.get("transaction_time", "--")}
                </div>
            </div>
            <div style="text-align:right;">
                <div style="font-size:20px; font-weight:700; color:#1D2129;">
                    {format_amount(rec["amount"], rec["currency"])}
                </div>
                <div style="font-size:12px; padding:2px 8px; border-radius:10px;
                             background:{status_color}15; color:{status_color}; font-weight:500; margin-top:4px;">
                    {status_label}
                </div>
            </div>
        </div>
    </div>
    ''')

    # --- AI Check Result Section ---
    ai_check_label = {"pending": "\u5f85\u6821\u9a8c", "passed": "\u5df2\u901a\u8fc7", "need_supplement": "\u5f85\u8865\u5145", "failed": "\u672a\u901a\u8fc7"}.get(ai_check, ai_check)
    ai_check_color_map = {"pending": "#999", "passed": "#2E7D32", "need_supplement": "#E65100", "failed": "#C62828"}
    ai_color = ai_check_color_map.get(ai_check, "#999")

    sync_label_map = {"not_synced": "\u672a\u540c\u6b65", "syncing": "\u540c\u6b65\u4e2d", "synced": "\u5df2\u540c\u6b65", "sync_failed": "\u540c\u6b65\u5931\u8d25"}
    sync_color_map = {"not_synced": "#999", "syncing": "#1565C0", "synced": "#2E7D32", "sync_failed": "#C62828"}
    sync_lbl = sync_label_map.get(sync_st, sync_st)
    sync_clr = sync_color_map.get(sync_st, "#999")

    st.html(f'''
    <div style="background:#fff; border-radius:12px; margin:8px 12px; padding:14px 16px;
                box-shadow:0 1px 4px rgba(0,0,0,0.04);">
        <div style="font-size:14px; font-weight:600; color:#1D2129; margin-bottom:12px;">AI \u6821\u9a8c\u7ed3\u679c</div>
        <div style="display:flex; gap:12px; margin-bottom:12px;">
            <div style="flex:1; padding:10px 12px; background:{ai_color}10; border-radius:8px; text-align:center;">
                <div style="font-size:12px; color:#86909C; margin-bottom:4px;">\u6821\u9a8c\u72b6\u6001</div>
                <div style="font-size:14px; font-weight:600; color:{ai_color};">{ai_check_label}</div>
            </div>
            <div style="flex:1; padding:10px 12px; background:{sync_clr}10; border-radius:8px; text-align:center;">
                <div style="font-size:12px; color:#86909C; margin-bottom:4px;">\u540c\u6b65\u72b6\u6001</div>
                <div style="font-size:14px; font-weight:600; color:{sync_clr};">{sync_lbl}</div>
            </div>
        </div>
        <div style="font-size:13px; color:#4E5969; line-height:1.6;">
            {rec.get("ai_check_message", "")}
        </div>
    </div>
    ''')

    # --- Detail Info Cards ---
    _render_detail_info_section(rec)

    # --- Bottom Actions ---
    _render_detail_actions(rec)


def _render_detail_info_section(rec):
    """Render the detail information section."""
    sync_time_str = format_sync_time(rec.get("sync_time"))
    order_no = rec.get("sync_order_no", "")
    expense_desc = rec.get("expense_description", "")
    tax_rate = rec.get("tax_rate", "")
    note = rec.get("note", "")
    attachments = rec.get("attachments", [])

    # Basic info
    st.html(f'''
    <div style="background:#fff; border-radius:12px; margin:8px 12px; padding:14px 16px;
                box-shadow:0 1px 4px rgba(0,0,0,0.04);">
        <div style="font-size:14px; font-weight:600; color:#1D2129; margin-bottom:10px;">\u57fa\u672c\u4fe1\u606f</div>
        <div style="font-size:13px; color:#4E5969; line-height:2;">
            <div>\u8d39\u7528\u8bf4\u660e\uff1a{expense_desc}</div>
            <div>\u7a0e\u7387\uff1a{tax_rate}</div>
            <div>\u5907\u6ce8\uff1a{note}</div>
            <div>\u540c\u6b65\u65f6\u95f4\uff1a{sync_time_str}</div>
            <div>\u62a5\u9500\u5355\u53f7\uff1a{order_no or "--"}</div>
        </div>
    </div>
    ''')

    # Attachments
    if attachments:
        attach_html = '<div style="background:#fff; border-radius:12px; margin:8px 12px; padding:14px 16px; box-shadow:0 1px 4px rgba(0,0,0,0.04);"><div style="font-size:14px; font-weight:600; color:#1D2129; margin-bottom:10px;">\u9644\u4ef6</div>'
        for att in attachments:
            attach_html += f'''<div style="display:flex;align-items:center;gap:8px;padding:6px 0;">
                <span style="font-size:16px;">&#128206;</span>
                <span style="font-size:13px;color:#4E5969;">{att}</span>
            </div>'''
        attach_html += '</div>'
        st.html(attach_html)


def _render_detail_actions(rec):
    """Render bottom action buttons based on record status."""
    status = rec.get("status", "")

    if status == STATUS_SUBMITTED:
        st.html('''
        <div style="background:#E8F5E9; border-radius:12px; margin:8px 12px; padding:16px; text-align:center;">
            <div style="font-size:16px; font-weight:600; color:#2E7D32;">&#10003; \u5df2\u63d0\u4ea4\u62a5\u9500\u7cfb\u7edf</div>
            <div style="font-size:12px; color:#4E5969; margin-top:4px;">\u8bf7\u5728\u62a5\u9500\u7cfb\u7edf\u4e2d\u67e5\u770b\u5ba1\u6279\u8fdb\u5ea6</div>
        </div>
        ''')

    elif status == STATUS_PENDING_RECEIPT:
        if st.button("\U0001f4e4 \u4e0a\u4f20\u7968\u636e", key="detail_upload_receipt", type="primary", use_container_width=True):
            st.session_state.selected_record_id = rec["id"]
            handle_demo_action("go_supplement", {"record_id": rec["id"]})

    elif status == STATUS_PENDING_SUBMIT:
        if st.button("\u2705 \u786e\u8ba4\u63d0\u4ea4\u62a5\u9500", key="detail_confirm_sync", type="primary", use_container_width=True):
            handle_demo_action("confirm_single_sync", {"record_id": rec["id"]})

    elif status == STATUS_ERROR:
        col1, col2 = st.columns(2)
        with col1:
            if st.button("\U0001f504 \u91cd\u65b0\u5904\u7406", key="detail_retry", type="primary", use_container_width=True):
                handle_demo_action("retry_process", {"record_id": rec["id"]})
        with col2:
            if st.button("\U0001f4dd \u67e5\u770b\u5f02\u5e38\u539f\u56e0", key="detail_view_error", use_container_width=True):
                st.info(rec.get("ai_check_message", "\u65e0\u5f02\u5e38\u8bf4\u660e"))


# =============================================================================
# Supplement Material Page
# =============================================================================

def render_supplement_material_page():
    """Render the supplement material upload form page."""
    _render_h5_header("\u8865\u5145\u6750\u6599", "go_back_to_detail")

    rid = st.session_state.get("selected_record_id")
    rec = get_record(rid) if rid else None

    if not rec:
        st.warning("\u672a\u9009\u62e9\u8bb0\u5f55")
        return

    # --- Record summary ---
    st.html(f'''
    <div style="background:#fff; border-radius:12px; margin:8px 12px; padding:14px 16px;
                box-shadow:0 1px 4px rgba(0,0,0,0.04);">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <div>
                <div style="font-size:15px; font-weight:600; color:#1D2129;">{rec["merchant_name"]}</div>
                <div style="font-size:13px; color:#4E5969; margin-top:2px;">{rec["expense_type"]}</div>
            </div>
            <div style="font-size:18px; font-weight:700; color:#1D2129;">
                {format_amount(rec["amount"], rec["currency"])}
            </div>
        </div>
    </div>
    ''')

    # --- Supplement Form ---
    form = st.session_state.get("supplement_form", {
        "invoice_uploaded": False, "invoice_name": "",
        "receipt_uploaded": False, "receipt_name": "",
        "note": "", "expense_type": "",
    })

    # --- Upload Invoice ---
    if form.get("invoice_uploaded"):
        st.html(f'''
        <div style="background:#fff; border-radius:12px; margin:8px 12px; padding:14px 16px;
                    box-shadow:0 1px 4px rgba(0,0,0,0.04);">
            <div style="font-size:14px; font-weight:600; color:#1D2129; margin-bottom:8px;">\u4e0a\u4f20\u53d1\u7968</div>
            <div style="display:flex; align-items:center; gap:8px; padding:8px 12px; background:#E8F5E9; border-radius:8px;">
                <span style="font-size:18px;">\u2705</span>
                <span style="font-size:13px; color:#2E7D32; font-weight:500;">{form["invoice_name"]}</span>
            </div>
        </div>
        ''')
    else:
        st.html('''
        <div style="background:#fff; border-radius:12px; margin:8px 12px; padding:14px 16px;
                    box-shadow:0 1px 4px rgba(0,0,0,0.04);">
            <div style="font-size:14px; font-weight:600; color:#1D2129; margin-bottom:10px;">\u4e0a\u4f20\u53d1\u7968</div>
            <div style="border:2px dashed #C9CDD4; border-radius:12px; padding:24px 16px; text-align:center;">
                <div style="font-size:28px; color:#86909C; margin-bottom:6px;">&#128196;</div>
                <div style="font-size:13px; color:#4E5969; font-weight:500;">\u4e0a\u4f20\u53d1\u7968\u6216\u7535\u5b50\u53d1\u7968</div>
                <div style="font-size:11px; color:#86909C; margin-top:4px;">\u652f\u6301\u56fe\u7247 / PDF\uff0c\u5355\u4e2a\u6587\u4ef6\u4e0d\u8d85\u8fc7 10MB</div>
            </div>
        </div>
        ''')
        if st.button("\U0001f4c4 \u70b9\u51fb\u4e0a\u4f20\u53d1\u7968", key="btn_upload_invoice", use_container_width=True):
            handle_demo_action("upload_invoice", {"filename": "invoice_demo.pdf"})
            st.rerun()

    # --- Upload Receipt ---
    if form.get("receipt_uploaded"):
        st.html(f'''
        <div style="background:#fff; border-radius:12px; margin:8px 12px; padding:14px 16px;
                    box-shadow:0 1px 4px rgba(0,0,0,0.04);">
            <div style="font-size:14px; font-weight:600; color:#1D2129; margin-bottom:8px;">\u4e0a\u4f20\u6d88\u8d39\u51ed\u8bc1</div>
            <div style="display:flex; align-items:center; gap:8px; padding:8px 12px; background:#E8F5E9; border-radius:8px;">
                <span style="font-size:18px;">\u2705</span>
                <span style="font-size:13px; color:#2E7D32; font-weight:500;">{form["receipt_name"]}</span>
            </div>
        </div>
        ''')
    else:
        st.html('''
        <div style="background:#fff; border-radius:12px; margin:8px 12px; padding:14px 16px;
                    box-shadow:0 1px 4px rgba(0,0,0,0.04);">
            <div style="font-size:14px; font-weight:600; color:#1D2129; margin-bottom:10px;">\u4e0a\u4f20\u6d88\u8d39\u51ed\u8bc1</div>
            <div style="border:2px dashed #C9CDD4; border-radius:12px; padding:24px 16px; text-align:center;">
                <div style="font-size:28px; color:#86909C; margin-bottom:6px;">&#128247;</div>
                <div style="font-size:13px; color:#4E5969; font-weight:500;">\u4e0a\u4f20\u6d88\u8d39\u51ed\u8bc1\u6216\u7167\u7247</div>
                <div style="font-size:11px; color:#86909C; margin-top:4px;">\u652f\u6301\u56fe\u7247 / PDF\uff0c\u5355\u4e2a\u6587\u4ef6\u4e0d\u8d85\u8fc7 10MB</div>
            </div>
        </div>
        ''')
        if st.button("\U0001f4f7 \u70b9\u51fb\u4e0a\u4f20\u6d88\u8d39\u51ed\u8bc1", key="btn_upload_receipt", use_container_width=True):
            handle_demo_action("upload_receipt_voucher", {"filename": "receipt_demo.jpg"})
            st.rerun()

    # --- Supplement Note ---
    st.html('''
    <div style="background:#fff; border-radius:12px 12px 0 0; margin:8px 12px 0; padding:14px 16px 4px;
                box-shadow:0 1px 4px rgba(0,0,0,0.04);">
        <div style="font-size:14px; font-weight:600; color:#1D2129;">\u8865\u5145\u8bf4\u660e</div>
    </div>
    ''')
    note = st.text_area(
        "\u8bf7\u8f93\u5165\u8865\u5145\u8bf4\u660e",
        value=form.get("note", ""),
        key="supplement_note_input",
        height=80,
        label_visibility="collapsed",
        placeholder="\u8bf7\u8f93\u5165\u8865\u5145\u8bf4\u660e...",
        max_chars=300,
    )
    st.session_state.supplement_form["note"] = note
    st.caption(f"{len(note)}/300")

    # --- Expense Type ---
    st.html('''
    <div style="background:#fff; border-radius:12px 12px 0 0; margin:8px 12px 0; padding:14px 16px 4px;
                box-shadow:0 1px 4px rgba(0,0,0,0.04);">
        <div style="font-size:14px; font-weight:600; color:#1D2129;">\u8d39\u7528\u7c7b\u578b</div>
    </div>
    ''')
    expense_types = ["\u5dee\u65c5\u4f4f\u5bbf", "\u4ea4\u901a\u51fa\u884c", "\u9910\u996e\u62db\u5f85", "\u529e\u516c\u7528\u54c1", "\u5176\u4ed6"]
    current_type = form.get("expense_type", "")

    type_cols = st.columns(len(expense_types))
    for col, etype in zip(type_cols, expense_types):
        with col:
            btn_type = "primary" if etype == current_type else "secondary"
            if st.button(etype, key=f"etype_{etype}", type=btn_type, use_container_width=True):
                st.session_state.supplement_form["expense_type"] = etype
                show_info_toast("\u8d39\u7528\u7c7b\u578b\u5df2\u66f4\u65b0")
                st.rerun()

    # --- Submit button ---
    st.markdown("---")
    can_submit = form.get("invoice_uploaded") or form.get("receipt_uploaded")
    if can_submit:
        if st.button("\u63d0\u4ea4\u8865\u5145\u6750\u6599", key="btn_submit_supplement", type="primary", use_container_width=True):
            handle_demo_action("submit_supplement")
            st.rerun()
    else:
        st.button("\u63d0\u4ea4\u8865\u5145\u6750\u6599", key="btn_submit_supplement_disabled", disabled=True, use_container_width=True)
        st.caption("\u8bf7\u5148\u4e0a\u4f20\u53d1\u7968\u6216\u6d88\u8d39\u51ed\u8bc1")


# Legacy function for backwards compatibility
def render_h5_page_in_phone(page):
    """Legacy entry point - now delegates to individual page renderers."""
    if page == "reimbursement_list":
        render_reimbursement_list_page()
    elif page == "reimbursement_detail":
        render_reimbursement_detail_page()
    elif page == "supplement_material":
        render_supplement_material_page()
    elif page == "anomaly_detail":
        render_reimbursement_detail_page()
    else:
        st.warning(f"\u672a\u77e5\u9875\u9762: {page}")

# Legacy aliases for backwards compatibility with tests
render_h5_page = render_h5_page_in_phone
