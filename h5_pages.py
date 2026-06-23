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
    get_ai_check_label, get_sync_status_label, format_amount, format_sync_time,
    get_ai_check_color, get_sync_status_color,
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
# Reimbursement List Page (工单4: DingTalk mobile list)
# =============================================================================

def render_reimbursement_list_page():
    """Render the reimbursement records list page - DingTalk mobile style."""
    _render_h5_header("AI\u62a5\u9500\u6821\u9a8c", "go_back")

    # --- Filter tabs (horizontal scrollable) ---
    all_records = st.session_state.reimbursement_records
    counts = {
        "all": len(all_records),
        "need_supplement": len([r for r in all_records if r["ai_check_result"] == "need_supplement"]),
        "passed": len([r for r in all_records if r["ai_check_result"] == "passed" and r["sync_status"] in ("not_synced", "syncing")]),
        "synced": len([r for r in all_records if r["sync_status"] == "synced"]),
        "sync_failed": len([r for r in all_records if r["sync_status"] == "sync_failed"]),
    }
    current_filter = st.session_state.get("record_filter", "all")

    filter_options = [
        ("all", f"\u5168\u90e8 {counts['all']}"),
        ("need_supplement", f"\u5f85\u8865\u5145 {counts['need_supplement']}"),
        ("passed", f"\u6821\u9a8c\u901a\u8fc7 {counts['passed']}"),
        ("synced", f"\u5df2\u540c\u6b65 {counts['synced']}"),
        ("sync_failed", f"\u540c\u6b65\u5931\u8d25 {counts['sync_failed']}"),
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

    # --- Banner for need_supplement ---
    if current_filter == "need_supplement" and counts["need_supplement"] > 0:
        st.html('''
        <div style="margin:8px 12px; padding:10px 14px; background:#FFF7E6; border:1px solid #FFE0B2;
                    border-radius:8px; font-size:13px; color:#E65100;">
            <span style="margin-right:6px;">&#9888;</span>
            \u8bf7\u5c3d\u5feb\u8865\u5145\u6750\u6599\uff0c\u4ee5\u514d\u5f71\u54cd\u62a5\u9500\u8fdb\u5ea6\u3002
        </div>
        ''')

    # --- Record cards ---
    records = get_filtered_records(current_filter)

    if not records:
        st.html('''
        <div style="text-align:center; padding:80px 24px; color:#86909C;">
            <div style="font-size:48px; margin-bottom:16px; opacity:0.4;">&#128237;</div>
            <div style="font-size:14px;">\u6682\u65e0\u7b26\u5408\u6761\u4ef6\u7684\u8bb0\u5f55</div>
        </div>
        ''')
        return

    for rec in records:
        _render_record_card(rec)


def _render_record_card(rec):
    """Render a single reimbursement record card - DingTalk compact style."""
    rid = rec["id"]
    ai_label = get_ai_check_label(rec["ai_check_result"])
    ai_color = get_ai_check_color(rec["ai_check_result"])
    sync_label = get_sync_status_label(rec["sync_status"])
    sync_color = get_sync_status_color(rec["sync_status"])
    amount_str = format_amount(rec["amount"], rec["currency"])
    sync_time_str = format_sync_time(rec["sync_time"])
    ai_msg = rec.get("ai_check_message", "")

    # Card HTML (visual) - compact mobile card
    card_html = f'''
    <div style="
        background:#fff; border-radius:12px; margin:8px 12px; padding:14px 16px;
        box-shadow:0 1px 4px rgba(0,0,0,0.06); border:1px solid #f2f3f5;
    ">
        <!-- Header: merchant + amount -->
        <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:6px;">
            <div>
                <div style="font-size:15px; font-weight:600; color:#1D2129;">{rec["merchant_name"]}</div>
                <div style="font-size:12px; color:#86909C; margin-top:2px;">{rec["transaction_time"]}</div>
            </div>
            <div style="font-size:16px; font-weight:600; color:#1D2129;">{amount_str}</div>
        </div>
        <!-- Status rows -->
        <div style="font-size:12px; margin-top:8px;">
            <div style="display:flex; justify-content:space-between; padding:3px 0;">
                <span style="color:#86909C;">AI\u6821\u9a8c</span>
                <span style="color:{ai_color}; font-weight:500; padding:1px 8px; border-radius:4px;
                       background:{ai_color}15;">{ai_label}</span>
            </div>
            <div style="display:flex; justify-content:space-between; padding:3px 0;">
                <span style="color:#86909C;">\u540c\u6b65\u72b6\u6001</span>
                <span style="color:{sync_color}; font-weight:500; padding:1px 8px; border-radius:4px;
                       background:{sync_color}15;">{sync_label}</span>
            </div>
            <div style="display:flex; justify-content:space-between; padding:3px 0;">
                <span style="color:#86909C;">\u6700\u65b0\u540c\u6b65</span>
                <span style="color:#4E5969;">{sync_time_str}</span>
            </div>
            <div style="display:flex; justify-content:space-between; padding:3px 0;">
                <span style="color:#86909C;">\u6821\u9a8c\u8bf4\u660e</span>
                <span style="color:#4E5969; max-width:180px; text-align:right;">{ai_msg}</span>
            </div>
        </div>
    </div>
    '''
    st.html(card_html)

    # Action buttons (Streamlit native - functional)
    if rec["ai_check_result"] == "need_supplement":
        bc1, bc2 = st.columns(2)
        with bc1:
            if st.button("\u67e5\u770b\u8be6\u60c5", key=f"detail_{rid}", use_container_width=True):
                handle_demo_action("open_record_detail", {"record_id": rid})
                st.rerun()
        with bc2:
            if st.button("\u53bb\u8865\u5145", key=f"supplement_{rid}", type="primary", use_container_width=True):
                handle_demo_action("open_supplement_page", {"record_id": rid})
                st.rerun()
    elif rec["ai_check_result"] == "passed" and rec["sync_status"] in ("not_synced", "syncing"):
        bc1, bc2 = st.columns(2)
        with bc1:
            if st.button("\u67e5\u770b\u8be6\u60c5", key=f"detail_{rid}", use_container_width=True):
                handle_demo_action("open_record_detail", {"record_id": rid})
                st.rerun()
        with bc2:
            if st.button("\u786e\u8ba4\u5e76\u540c\u6b65", key=f"sync_{rid}", type="primary", use_container_width=True):
                handle_demo_action("confirm_single_sync", {"record_id": rid})
                st.rerun()
    elif rec["sync_status"] == "sync_failed":
        bc1, bc2 = st.columns(2)
        with bc1:
            if st.button("\u67e5\u770b\u8be6\u60c5", key=f"detail_{rid}", use_container_width=True):
                handle_demo_action("open_record_detail", {"record_id": rid})
                st.rerun()
        with bc2:
            if st.button("\u91cd\u65b0\u540c\u6b65", key=f"retry_{rid}", type="primary", use_container_width=True):
                handle_demo_action("retry_sync", {"record_id": rid})
                st.rerun()
    else:
        if st.button("\u67e5\u770b\u8be6\u60c5", key=f"detail_{rid}", use_container_width=True):
            handle_demo_action("open_record_detail", {"record_id": rid})
            st.rerun()


# =============================================================================
# Detail Page (工单5: DingTalk mobile detail)
# =============================================================================

def render_reimbursement_detail_page():
    """Render the reimbursement detail/verification page - DingTalk mobile style."""
    _render_h5_header("\u6821\u9a8c\u8be6\u60c5", "go_back")

    rid = st.session_state.get("selected_record_id")
    rec = get_record(rid) if rid else None
    if not rec:
        st.error("\u8bb0\u5f55\u4e0d\u5b58\u5728")
        return

    ai_label = get_ai_check_label(rec["ai_check_result"])
    ai_color = get_ai_check_color(rec["ai_check_result"])
    sync_label = get_sync_status_label(rec["sync_status"])
    sync_color = get_sync_status_color(rec["sync_status"])
    amount_str = format_amount(rec["amount"], rec["currency"])
    sync_time_str = format_sync_time(rec["sync_time"])
    sync_order = rec.get("sync_order_no") or "--"
    ai_status = rec["ai_check_result"]
    sync_status = rec["sync_status"]

    # --- Core Info Card ---
    st.html(f'''
    <div style="background:#fff; border-radius:12px; margin:8px 12px; padding:16px; box-shadow:0 1px 4px rgba(0,0,0,0.04);">
        <div style="font-size:14px; font-weight:600; color:#1D2129; margin-bottom:12px;">\u6838\u5fc3\u4fe1\u606f</div>
        <div style="font-size:13px;">
            <div style="display:flex; justify-content:space-between; padding:8px 0; border-bottom:1px solid #f2f3f5;">
                <span style="color:#86909C;">AI\u6821\u9a8c</span>
                <span style="color:{ai_color}; font-weight:600; padding:2px 10px; border-radius:4px;
                       background:{ai_color}15;">{ai_label}</span>
            </div>
            <div style="display:flex; justify-content:space-between; padding:8px 0; border-bottom:1px solid #f2f3f5;">
                <span style="color:#86909C;">\u540c\u6b65\u72b6\u6001</span>
                <span style="color:{sync_color}; font-weight:600; padding:2px 10px; border-radius:4px;
                       background:{sync_color}15;">{sync_label}</span>
            </div>
            <div style="display:flex; justify-content:space-between; padding:8px 0;">
                <span style="color:#86909C;">\u6700\u65b0\u540c\u6b65\u65f6\u95f4</span>
                <span style="color:#1D2129;">{sync_time_str}</span>
            </div>
        </div>
    </div>
    ''')

    # --- Expense Info Card ---
    info_rows = [
        ("\u8d39\u7528\u7c7b\u578b", rec["expense_type"]),
        ("\u540c\u6b65\u5355\u53f7", sync_order),
        ("\u5173\u8054\u6d88\u8d39", rec["merchant_name"]),
        ("\u91d1\u989d", f'<span style="font-size:16px;font-weight:600;color:#1D2129;">{amount_str}</span>'),
        ("\u65f6\u95f4", rec["transaction_time"]),
    ]
    rows_html = ""
    for label, value in info_rows:
        rows_html += f'''
        <div style="display:flex; justify-content:space-between; padding:8px 0; border-bottom:1px solid #f2f3f5; font-size:13px;">
            <span style="color:#86909C;">{label}</span>
            <span style="color:#1D2129;">{value}</span>
        </div>
        '''

    st.html(f'''
    <div style="background:#fff; border-radius:12px; margin:8px 12px; padding:16px; box-shadow:0 1px 4px rgba(0,0,0,0.04);">
        <div style="font-size:14px; font-weight:600; color:#1D2129; margin-bottom:12px;">\u6d88\u8d39\u4fe1\u606f</div>
        {rows_html}
    </div>
    ''')

    # --- AI Explanation Card (color-coded) ---
    if sync_status == "synced":
        explanation = "\u8be5\u6d88\u8d39\u7b26\u5408\u4f01\u4e1a\u5dee\u65c5\u4f4f\u5bbf\u89c4\u5219\uff0c\u5df2\u901a\u8fc7 AI \u6821\u9a8c\u5e76\u6210\u529f\u540c\u6b65\u3002"
        bg = "#E8F5E9"; border_color = "#4CAF50"; icon = "\u2705"; text_color = "#2E7D32"
    elif ai_status == "passed" and sync_status in ("not_synced", "syncing"):
        explanation = "\u8be5\u6d88\u8d39\u5df2\u901a\u8fc7 AI \u6821\u9a8c\uff0c\u53ef\u540c\u6b65\u81f3\u62a5\u9500\u7cfb\u7edf\u3002"
        bg = "#E3F2FD"; border_color = "#1565C0"; icon = "\u2705"; text_color = "#1565C0"
    elif ai_status == "need_supplement":
        explanation = rec.get("ai_check_message") or "\u8be5\u6d88\u8d39\u7f3a\u5c11\u53d1\u7968\uff0c\u8bf7\u4e0a\u4f20\u53d1\u7968\u6216\u6d88\u8d39\u51ed\u8bc1\u540e\u91cd\u65b0\u63d0\u4ea4\u6821\u9a8c\u3002"
        bg = "#FFF3E0"; border_color = "#FF9800"; icon = "\u26a0\ufe0f"; text_color = "#E65100"
    elif sync_status == "sync_failed":
        explanation = "\u8be5\u6d88\u8d39\u5df2\u901a\u8fc7 AI \u6821\u9a8c\uff0c\u4f46\u540c\u6b65\u81f3\u62a5\u9500\u7cfb\u7edf\u5931\u8d25\uff0c\u8bf7\u7a0d\u540e\u91cd\u65b0\u540c\u6b65\u3002"
        bg = "#FFEBEE"; border_color = "#F44336"; icon = "\u274c"; text_color = "#C62828"
    elif ai_status == "failed":
        explanation = rec.get("ai_check_message") or "\u8be5\u6d88\u8d39\u4e0d\u7b26\u5408\u5f53\u524d\u4f01\u4e1a\u62a5\u9500\u89c4\u5219\u3002"
        bg = "#FFEBEE"; border_color = "#F44336"; icon = "\u274c"; text_color = "#C62828"
    else:
        explanation = rec.get("ai_check_message") or "\u6821\u9a8c\u4fe1\u606f\u6682\u65e0\u3002"
        bg = "#F5F5F5"; border_color = "#999"; icon = "\u2139\ufe0f"; text_color = "#666"

    st.html(f'''
    <div style="background:#fff; border-radius:12px; margin:8px 12px; padding:16px; box-shadow:0 1px 4px rgba(0,0,0,0.04);">
        <div style="font-size:14px; font-weight:600; color:#1D2129; margin-bottom:12px;">AI \u6821\u9a8c\u8bf4\u660e</div>
        <div style="background:{bg}; border-left:3px solid {border_color}; border-radius:8px; padding:12px 14px;">
            <div style="font-size:13px; color:{text_color}; line-height:1.6;">
                {icon} {explanation}
            </div>
        </div>
    </div>
    ''')

    # --- Attachments Card ---
    attachments = rec.get("attachments", [])
    att_items = ""
    if attachments:
        for att in attachments:
            # Determine icon by type
            if "\u53d1\u7968" in att or "invoice" in att.lower():
                ficon = "\U0001f4c4"; ftype = "PDF"; fsize = "768 KB"
            elif "\u51ed\u8bc1" in att or "receipt" in att.lower():
                ficon = "\U0001f5bc"; ftype = "JPG"; fsize = "1.2 MB"
            else:
                ficon = "\U0001f4ce"; ftype = "FILE"; fsize = "--"
            att_items += f'''
            <div style="display:flex; align-items:center; justify-content:space-between; padding:10px 0;
                        border-bottom:1px solid #f2f3f5;">
                <div style="display:flex; align-items:center; gap:10px;">
                    <span style="font-size:20px;">{ficon}</span>
                    <div>
                        <div style="font-size:13px; color:#1D2129; font-weight:500;">{att}</div>
                        <div style="font-size:11px; color:#86909C;">{ftype} \u00b7 {fsize}</div>
                    </div>
                </div>
                <span style="color:#C9CDD4; font-size:16px;">\u203a</span>
            </div>
            '''
    else:
        att_items = '<div style="font-size:13px; color:#86909C; padding:8px 0;">\u6682\u65e0\u9644\u4ef6</div>'

    st.html(f'''
    <div style="background:#fff; border-radius:12px; margin:8px 12px; padding:16px; box-shadow:0 1px 4px rgba(0,0,0,0.04);">
        <div style="font-size:14px; font-weight:600; color:#1D2129; margin-bottom:8px;">\u9644\u4ef6</div>
        {att_items}
    </div>
    ''')

    # --- Bottom Action Buttons (Streamlit native - functional) ---
    st.markdown("---")
    if sync_status == "synced":
        if st.button("\u8fd4\u56de\u5217\u8868", key="detail_back_list", use_container_width=True):
            handle_demo_action("go_back")
            st.rerun()
    elif ai_status == "need_supplement":
        bc1, bc2 = st.columns(2)
        with bc1:
            if st.button("\u8fd4\u56de\u5217\u8868", key="detail_back_list", use_container_width=True):
                handle_demo_action("go_back")
                st.rerun()
        with bc2:
            if st.button("\u53bb\u8865\u5145", key="detail_go_supplement", type="primary", use_container_width=True):
                handle_demo_action("open_supplement_page", {"record_id": rid})
                st.rerun()
    elif sync_status == "sync_failed":
        bc1, bc2 = st.columns(2)
        with bc1:
            if st.button("\u8fd4\u56de\u5217\u8868", key="detail_back_list", use_container_width=True):
                handle_demo_action("go_back")
                st.rerun()
        with bc2:
            if st.button("\u91cd\u65b0\u540c\u6b65", key="detail_retry_sync", type="primary", use_container_width=True):
                handle_demo_action("retry_sync", {"record_id": rid})
                st.rerun()
    elif ai_status == "passed" and sync_status in ("not_synced", "syncing"):
        bc1, bc2 = st.columns(2)
        with bc1:
            if st.button("\u8fd4\u56de\u5217\u8868", key="detail_back_list", use_container_width=True):
                handle_demo_action("go_back")
                st.rerun()
        with bc2:
            if st.button("\u786e\u8ba4\u5e76\u540c\u6b65", key="detail_confirm_sync", type="primary", use_container_width=True):
                handle_demo_action("confirm_single_sync", {"record_id": rid})
                st.rerun()
    elif ai_status == "failed":
        bc1, bc2 = st.columns(2)
        with bc1:
            if st.button("\u8fd4\u56de\u5217\u8868", key="detail_back_list", use_container_width=True):
                handle_demo_action("go_back")
                st.rerun()
        with bc2:
            if st.button("\u67e5\u770b\u5dee\u65c5\u89c4\u5219", key="detail_travel_rule", use_container_width=True):
                st.session_state.active_modal = "travel_rules"
                st.rerun()
    else:
        if st.button("\u8fd4\u56de\u5217\u8868", key="detail_back_list", use_container_width=True):
            handle_demo_action("go_back")
            st.rerun()


# =============================================================================
# Supplement Material Page (工单6: DingTalk mobile form)
# =============================================================================

def render_supplement_material_page():
    """Render the supplement material page - DingTalk mobile form style."""
    _render_h5_header("\u8865\u5145\u6750\u6599", "go_back")

    rid = st.session_state.get("selected_record_id")
    rec = get_record(rid) if rid else None
    if not rec:
        st.error("\u8bb0\u5f55\u4e0d\u5b58\u5728")
        return

    amount_str = format_amount(rec["amount"], rec["currency"])
    ai_msg = rec.get("ai_check_message") or "\u7f3a\u5c11\u53d1\u7968"

    # --- Record summary card ---
    st.html(f'''
    <div style="background:#fff; border-radius:12px; margin:8px 12px; padding:14px 16px;
                box-shadow:0 1px 4px rgba(0,0,0,0.04);">
        <div style="display:flex; justify-content:space-between; align-items:flex-start;">
            <div>
                <div style="font-size:15px; font-weight:600; color:#1D2129;">{rec["merchant_name"]}</div>
                <div style="font-size:12px; color:#86909C; margin-top:2px;">{rec["transaction_time"]}</div>
                <div style="font-size:12px; color:#86909C; margin-top:2px;">\u8d39\u7528\u7c7b\u578b: {rec["expense_type"]}</div>
            </div>
            <div style="font-size:16px; font-weight:600; color:#1D2129;">{amount_str}</div>
        </div>
    </div>
    ''')

    # --- AI check result banner ---
    st.html(f'''
    <div style="margin:6px 12px; padding:10px 14px; background:#FFF7E6; border:1px solid #FFE0B2;
                border-radius:8px; font-size:13px; color:#E65100; display:flex; align-items:center; gap:6px;">
        <span style="font-size:16px;">\u26a0\ufe0f</span>
        <span>AI\u6821\u9a8c\u7ed3\u679c\uff1a{ai_msg}</span>
    </div>
    ''')

    form = st.session_state.supplement_form

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
                <div style="font-size:13px; color:#4E5969; font-weight:500;">\u4e0a\u4f20\u53d1\u7968\u6216\u6d88\u8d39\u51ed\u8bc1</div>
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
