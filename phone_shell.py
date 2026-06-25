"""
Legacy / fallback phone shell renderer.

The current primary mobile UI and mobile CSS are implemented in phone_ui.py.
This module is retained only for backward compatibility and regression protection.

Do not add new UI logic here.
Do not migrate new mobile rendering work into this module.

---
Original description:
Phone App Shell - Stable Container Layout (390x867)
All layout uses st.container(key=...) and st.columns.
NO HTML divs wrapping across Streamlit controls.
NO position:absolute on buttons. NO use_container_width on card buttons.
"""
import streamlit as st
from demo_actions import handle_demo_action
from demo_state import close_modal, reset_demo, append_message
from feedback import show_info_toast


def inject_mobile_css():
    st.markdown("""<style>
:root{--phone-w:390px;--phone-h:867px;--content-w:358px;--bg:#f5f6f8;--text-main:#1f2329;--text-secondary:#646a73;--text-tertiary:#8f959e;--border:#e5e8ef;--border-strong:#d8dde8;--primary:#1677ff}

#MainMenu,footer,.stAppDeployButton,div[data-testid="stToolbar"],div[data-testid="stDecoration"],header[data-testid="stHeader"]{display:none!important}
.block-container{max-width:1280px!important;padding-top:.5rem!important}
div[data-testid="stVerticalBlock"]{gap:0!important}
div[data-testid="stHorizontalBlock"]{gap:0!important}
.stButton{margin:0!important}
.stButton>button{margin:0!important;box-shadow:none!important}
.stTextInput{margin:0!important}
.stTextInput>div{margin:0!important}
.stTextInput input{box-shadow:none!important}
.stApp{background:#F0F1F3!important}
.stTabs [data-baseweb="tab-panel"]{padding:0}
.stTabs [data-baseweb="tab-list"]{gap:0;background:#f8f8f8;border-bottom:1px solid #e8e8e8}
iframe{border:none!important}

/* Phone shell */
.st-key-phone_shell{width:var(--phone-w)!important;min-width:var(--phone-w)!important;max-width:var(--phone-w)!important;height:var(--phone-h)!important;min-height:var(--phone-h)!important;max-height:var(--phone-h)!important;margin:0 auto!important;background:var(--bg)!important;border-radius:32px!important;overflow:hidden!important;border:1px solid rgba(15,23,42,.08)!important;box-shadow:0 20px 48px rgba(15,23,42,.14)!important;position:relative!important;box-sizing:border-box!important}
.st-key-phone_shell>div,.st-key-phone_shell [data-testid="stVerticalBlock"]{width:var(--phone-w)!important;max-width:var(--phone-w)!important}
.st-key-phone_app{width:var(--phone-w)!important;height:var(--phone-h)!important;overflow:hidden!important;position:relative!important;background:var(--bg)!important}

/* Chat body area */
.st-key-chat_body_area{width:390px!important;height:639px!important;max-height:639px!important;overflow-y:auto!important;background:var(--bg)!important;padding:12px 16px 16px!important;box-sizing:border-box!important;scrollbar-width:none!important}
.st-key-chat_body_area::-webkit-scrollbar{display:none!important}
.st-key-chat_body_area>div{width:358px!important;max-width:358px!important;margin:0 auto!important}

/* Chat bottom bar */
.st-key-chat_bottom_bar{width:390px!important;height:148px!important;max-height:148px!important;background:rgba(255,255,255,.98)!important;border-top:1px solid #edf0f5!important;padding:10px 16px 12px!important;box-sizing:border-box!important;overflow:hidden!important}
.st-key-chat_bottom_bar>div{width:358px!important;max-width:358px!important;margin:0 auto!important}

/* Intro message row */
.st-key-chat_intro_row{width:358px!important;max-width:358px!important;margin:0 auto 10px!important}
.st-key-chat_intro_row [data-testid="stHorizontalBlock"]{gap:8px!important;align-items:flex-start!important}
.st-key-chat_intro_row [data-testid="column"]:nth-child(1){width:32px!important;min-width:32px!important;max-width:32px!important;flex:0 0 32px!important;padding:0!important}
.st-key-chat_intro_row [data-testid="column"]:nth-child(2){width:318px!important;min-width:318px!important;max-width:318px!important;flex:0 0 318px!important;padding:0!important}

/* Ticket card row */
.st-key-chat_ticket_row{width:358px!important;max-width:358px!important;margin:0 auto 10px!important}
.st-key-chat_ticket_row [data-testid="stHorizontalBlock"]{gap:8px!important;align-items:flex-start!important}
.st-key-chat_ticket_row [data-testid="column"]:nth-child(1){width:32px!important;min-width:32px!important;max-width:32px!important;flex:0 0 32px!important;padding:0!important}
.st-key-chat_ticket_row [data-testid="column"]:nth-child(2){width:318px!important;min-width:318px!important;max-width:318px!important;flex:0 0 318px!important;padding:0!important}

/* Ticket card */
.st-key-ticket_card{width:318px!important;max-width:318px!important;background:white!important;border:1px solid rgba(22,119,255,.45)!important;border-radius:14px!important;padding:12px!important;box-sizing:border-box!important;box-shadow:0 4px 12px rgba(22,119,255,.08)!important}

/* Ticket card actions */
.st-key-ticket_card_actions{width:294px!important;max-width:294px!important}
.st-key-ticket_card_actions [data-testid="stHorizontalBlock"]{gap:8px!important}
.st-key-ticket_card_actions [data-testid="column"]{width:143px!important;min-width:143px!important;max-width:143px!important;flex:0 0 143px!important;padding:0!important}
.st-key-chat_view_detail button,.st-key-chat_upload_ticket button{width:143px!important;min-width:143px!important;max-width:143px!important;height:36px!important;min-height:36px!important;border-radius:10px!important;padding:0!important;font-size:13px!important;font-weight:600!important;box-shadow:none!important;white-space:nowrap!important}
.st-key-chat_view_detail button{background:white!important;color:#1f2329!important;border:1px solid #d8dde8!important}
.st-key-chat_upload_ticket button,.st-key-chat_upload_ticket button:hover,.st-key-chat_upload_ticket button:focus,.st-key-chat_upload_ticket button:active{background:#1677ff!important;color:white!important;border:1px solid #1677ff!important}

/* Quick entry row */
.st-key-quick_entry_row{width:358px!important;max-width:358px!important;margin:0 auto 10px!important}
.st-key-quick_entry_row [data-testid="stHorizontalBlock"]{gap:8px!important}
.st-key-quick_entry_row [data-testid="column"]{width:114px!important;min-width:114px!important;max-width:114px!important;flex:0 0 114px!important;padding:0!important}
.st-key-quick_records button,.st-key-quick_rules button,.st-key-quick_files button{width:114px!important;min-width:114px!important;max-width:114px!important;height:40px!important;min-height:40px!important;border-radius:12px!important;border:1px solid #d8dde8!important;background:white!important;color:#1f2329!important;font-size:13px!important;font-weight:600!important;padding:0 4px!important;box-shadow:none!important;white-space:nowrap!important}

/* Input row */
.st-key-chat_input_row{width:358px!important;max-width:358px!important;margin:0 auto!important}
.st-key-chat_input_row [data-testid="stHorizontalBlock"]{gap:8px!important;align-items:center!important}
.st-key-chat_input_row [data-testid="column"]{padding:0!important}
.st-key-chat_input_row [data-testid="column"]:nth-child(1){width:32px!important;min-width:32px!important;max-width:32px!important;flex:0 0 32px!important}
.st-key-chat_input_row [data-testid="column"]:nth-child(2){width:238px!important;min-width:238px!important;max-width:238px!important;flex:0 0 238px!important}
.st-key-chat_input_row [data-testid="column"]:nth-child(3),.st-key-chat_input_row [data-testid="column"]:nth-child(4){width:32px!important;min-width:32px!important;max-width:32px!important;flex:0 0 32px!important}
.st-key-chat_plus button,.st-key-chat_emoji button,.st-key-chat_voice button{width:32px!important;min-width:32px!important;max-width:32px!important;height:32px!important;min-height:32px!important;border-radius:16px!important;padding:0!important;background:white!important;border:1px solid #e5e8ef!important;color:#1f2329!important;box-shadow:none!important}
.st-key-chat_message_input [data-testid="stTextInput"]{width:238px!important}
.st-key-chat_message_input input{width:238px!important;height:40px!important;min-height:40px!important;border-radius:20px!important;background:#f7f8fa!important;border:1px solid #e5e8ef!important;padding:0 14px!important;font-size:13px!important;box-shadow:none!important}
.st-key-chat_message_input label,.st-key-chat_message_input [data-testid="stWidgetLabel"]{display:none!important}

/* Side panel */
.st-key-side_panel .stButton>button{font-size:13px!important;min-height:36px!important;padding:4px 10px!important;border-radius:10px!important;background:white!important;border:1px solid #d8dde8!important;color:#4E5969!important}
.st-key-side_panel .stButton>button[kind="primary"]{min-height:40px!important;background:#1677ff!important;border-color:#1677ff!important;color:white!important;font-weight:600!important}

/* Detail/supplement */
.st-key-detail_primary button,.st-key-supplement_submit button{height:44px!important;min-height:44px!important;border-radius:12px!important;background:#1677ff!important;color:white!important;border:1px solid #1677ff!important;font-weight:700!important}
.st-key-detail_secondary button{height:40px!important;min-height:40px!important;border-radius:12px!important;background:white!important;color:#1f2329!important;border:1px solid #d8dde8!important;font-weight:600!important}

/* Nav back */
.st-key-nav_back_records,.st-key-nav_back_detail,.st-key-nav_back_supplement{position:absolute!important;top:34px!important;left:12px!important;width:36px!important;height:36px!important;z-index:30!important}
.st-key-nav_back_records button,.st-key-nav_back_detail button,.st-key-nav_back_supplement button{width:36px!important;min-width:36px!important;max-width:36px!important;height:36px!important;min-height:36px!important;border-radius:18px!important;padding:0!important;background:transparent!important;border:none!important;color:#1f2329!important;font-size:22px!important;box-shadow:none!important}

/* Upload chip */
.upload-file-chip{max-width:260px;margin:8px 16px 8px auto;padding:8px 12px;border-radius:12px;background:#d6efff;color:#1f2329;font-size:13px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;box-sizing:border-box}

/* Mobile */
@media(max-width:768px){
  html,body,.stApp,[data-testid="stAppViewContainer"]{min-height:100svh!important;height:auto!important;overflow-y:auto!important;overflow-x:hidden!important}
  .stTabs [data-baseweb="tab-list"]{display:none!important}
  .block-container{padding:0!important;width:100vw!important;max-width:100vw!important}
  .stApp{background:#f5f6f8!important}
  .st-key-side_panel{display:none!important}
  .st-key-desktop_ai_lab_panel,.st-key-desktop_eval_observe_panel{display:none!important;visibility:hidden!important;height:0!important;min-height:0!important;overflow:hidden!important;margin:0!important;padding:0!important}
  .stTabs [data-baseweb="tab-panel"]:has(.st-key-desktop_ai_lab_panel),.stTabs [data-baseweb="tab-panel"]:has(.st-key-desktop_eval_observe_panel){display:none!important;visibility:hidden!important;height:0!important;min-height:0!important;overflow:hidden!important}
  .st-key-phone_shell{width:100vw!important;min-width:0!important;max-width:100vw!important;height:100svh!important;min-height:100svh!important;max-height:100svh!important;border-radius:0!important;border:none!important;box-shadow:none!important;overflow:hidden!important;display:flex!important;flex-direction:column!important}
  .st-key-phone_app{width:100vw!important;min-width:0!important;max-width:100vw!important;flex:1!important;min-height:0!important;display:flex!important;flex-direction:column!important;overflow:hidden!important}
  .st-key-chat_body_area{width:100vw!important;max-width:100vw!important;height:auto!important;max-height:none!important;flex:1!important;min-height:0!important;overflow-y:auto!important;overflow-x:hidden!important}
  .st-key-chat_bottom_bar{width:100vw!important;max-width:100vw!important;height:auto!important;max-height:none!important;flex-shrink:0!important;position:sticky!important;bottom:0!important;padding-bottom:calc(12px + env(safe-area-inset-bottom, 0px))!important}
  .stTabs [data-baseweb="tab-panel"]{display:block!important;visibility:visible!important;height:auto!important;min-height:0!important;overflow:visible!important}
}
</style>""", unsafe_allow_html=True)


def render_phone_shell():
    inject_mobile_css()
    with st.container(key="phone_shell"):
        with st.container(key="phone_app"):
            _render_phone_app()


def _render_phone_app():
    # Status bar (self-contained HTML, no wrapping issue)
    st.markdown('<div style="height:24px;background:#fff;padding:5px 22px 0;display:flex;justify-content:space-between;align-items:center;font-size:12px;font-weight:700;color:#111827;box-sizing:border-box;"><span>9:41</span><span style="font-size:10px;">●●●● ⚡ █</span></div>', unsafe_allow_html=True)

    page = st.session_state.get("current_phone_page", "chat")
    modal = st.session_state.get("active_modal")

    if modal:
        _render_modal(modal)
    elif page == "chat":
        _render_chat_page()
    elif page == "reimbursement_list":
        from h5_pages import render_reimbursement_list_page
        render_reimbursement_list_page()
    elif page == "reimbursement_detail":
        from h5_pages import render_reimbursement_detail_page
        render_reimbursement_detail_page()
    elif page == "supplement_material":
        from h5_pages import render_supplement_material_page
        render_supplement_material_page()
    elif page == "anomaly_detail":
        from h5_pages import render_reimbursement_detail_page
        render_reimbursement_detail_page()
    else:
        _render_chat_page()


# ═══ MODALS ══════════════════════════════════════════════════════
def _render_modal(m):
    if m == "more_menu": _modal_more()
    elif m == "attachment_menu": _modal_attach()
    elif m == "expense_detail": _modal_detail()
    elif m == "travel_rules": _modal_rules()
    else: close_modal()

def _mhdr(t):
    st.markdown(f'<div style="padding:14px 16px 10px;background:#fff;border-bottom:1px solid #edf0f5;font-size:17px;font-weight:700;color:#1f2329;">{t}</div>', unsafe_allow_html=True)

def _modal_more():
    _mhdr("更多")
    if st.button("📋 报销记录", key="modal_reimb"): close_modal(); handle_demo_action("open_reimbursement_records"); st.rerun()
    if st.button("📖 差旅规则", key="modal_rules_btn"): st.session_state.active_modal = "travel_rules"; st.rerun()
    if st.button("🔄 重置 Demo", key="modal_reset"): close_modal(); reset_demo(); st.rerun()
    if st.button("关闭", key="modal_close"): close_modal(); st.rerun()

def _modal_attach():
    _mhdr("添加附件")
    if st.button("📄 上传发票", key="att_invoice"): close_modal(); handle_demo_action("chat_upload_attachment", {"type": "invoice", "filename": "invoice_upload.pdf"}); st.rerun()
    if st.button("🧾 上传消费凭证", key="att_receipt"): close_modal(); handle_demo_action("chat_upload_attachment", {"type": "receipt", "filename": "receipt_upload.jpg"}); st.rerun()
    if st.button("📷 拍照上传", key="att_photo"): close_modal(); handle_demo_action("chat_upload_attachment", {"type": "photo", "filename": "photo_upload.jpg"}); st.rerun()
    if st.button("关闭", key="att_close"): close_modal(); st.rerun()

def _modal_detail():
    _mhdr("费用详情")
    items=[("商户","Tokyo Bay Hotel"),("金额","¥1,280"),("币种","JPY"),("日期","2025-06-12"),("费用类型","酒店"),("行程","东京差旅"),("支付","WF ****1234")]
    rows="".join(f'<div style="display:flex;justify-content:space-between;padding:9px 16px;border-bottom:1px solid #f0f0f0;font-size:13px;"><span style="color:#646a73;">{k}</span><span style="color:#1f2329;font-weight:500;">{v}</span></div>' for k,v in items)
    st.markdown(f'<div style="background:#fff;">{rows}</div>', unsafe_allow_html=True)
    if st.button("关闭详情", key="close_expense_detail"): close_modal(); st.rerun()

def _modal_rules():
    _mhdr("差旅费用规则")
    items=[("酒店单笔","1000 USD"),("酒店日限","1500 USD"),("餐饮单笔","200 USD"),("交通单笔","500 USD"),("小费容差","20%"),("补传时限","48-72h"),("超额","主管审批")]
    rows="".join(f'<div style="display:flex;justify-content:space-between;padding:9px 16px;border-bottom:1px solid #f0f0f0;font-size:13px;"><span style="color:#646a73;">{k}</span><span style="color:#1f2329;font-weight:500;">{v}</span></div>' for k,v in items)
    st.markdown(f'<div style="background:#fff;">{rows}</div>', unsafe_allow_html=True)
    if st.button("关闭规则", key="close_travel_rules"): close_modal(); st.rerun()


# ═══ CHAT PAGE ═══════════════════════════════════════════════════

def _render_chat_page():
    # Nav (self-contained HTML)
    st.markdown('<div style="width:390px;height:56px;background:#fff;border-bottom:1px solid #edf0f5;display:flex;align-items:center;justify-content:center;box-sizing:border-box;flex-shrink:0;"><div><div style="font-size:17px;font-weight:700;color:#1f2329;text-align:center;">AI差旅助手</div><div style="font-size:11px;color:#8f959e;margin-top:3px;text-align:center;">企业财务助手</div></div></div>', unsafe_allow_html=True)

    # Chat body area - real st.container, NOT an HTML div
    with st.container(key="chat_body_area"):
        # Date chip (self-contained HTML)
        st.markdown('<div style="width:fit-content;margin:0 auto 12px;padding:4px 10px;border-radius:999px;background:#edf0f5;color:#8f959e;font-size:11px;">今天 09:30</div>', unsafe_allow_html=True)

        # Intro message
        with st.container(key="chat_intro_row"):
            av1, bb1 = st.columns([32, 318], gap="small")
            with av1:
                st.markdown('<div style="width:32px;height:32px;border-radius:16px;background:#1677ff;color:white;display:flex;align-items:center;justify-content:center;font-size:15px;box-shadow:0 4px 10px rgba(22,119,255,.2);">🤖</div>', unsafe_allow_html=True)
            with bb1:
                st.markdown('<div style="background:white;border-radius:13px;padding:12px;font-size:13px;color:#1f2329;line-height:1.5;box-shadow:0 2px 8px rgba(15,23,42,.04);box-sizing:border-box;">你好！我是你的AI差旅助手<br/>我可以帮你智能校验报销、识别发票、提醒补充材料。</div>', unsafe_allow_html=True)

        # Pending ticket card
        with st.container(key="chat_ticket_row"):
            av2, cd2 = st.columns([32, 318], gap="small")
            with av2:
                st.markdown('<div style="width:32px;height:32px;border-radius:16px;background:#1677ff;color:white;display:flex;align-items:center;justify-content:center;font-size:15px;box-shadow:0 4px 10px rgba(22,119,255,.2);">🤖</div>', unsafe_allow_html=True)
            with cd2:
                with st.container(key="ticket_card"):
                    st.markdown('<div style="font-size:13px;font-weight:700;color:#1f2329;margin-bottom:10px;">🔔 检测到一笔酒店消费待补票</div><div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:10px;"><div><div style="font-size:14px;font-weight:700;color:#1f2329;">浦东机场希尔顿酒店</div><div style="margin-top:4px;font-size:12px;color:#646a73;">2026-06-12 · 入住酒店</div></div><div style="font-size:17px;font-weight:800;color:#111827;">¥560</div></div>', unsafe_allow_html=True)

                    with st.container(key="ticket_card_actions"):
                        tc1, tc2 = st.columns([1, 1], gap="small")
                        with tc1:
                            if st.button("查看详情", key="chat_view_detail"):
                                st.session_state.selected_record_id = "record_004"
                                st.session_state.current_phone_page = "reimbursement_detail"
                                st.rerun()
                        with tc2:
                            if st.button("上传票据", key="chat_upload_ticket"):
                                st.session_state.selected_record_id = "record_004"
                                st.session_state.current_phone_page = "supplement_material"
                                st.rerun()

        # Dynamic messages
        for idx, msg in enumerate(st.session_state.get("messages", [])):
            _render_msg(msg, idx)

    # Bottom bar - real st.container, NOT an HTML div
    with st.container(key="chat_bottom_bar"):
        st.markdown('<div style="font-size:12px;color:#646a73;font-weight:500;margin-bottom:6px;">快捷入口</div>', unsafe_allow_html=True)

        with st.container(key="quick_entry_row"):
            q1, q2, q3 = st.columns([1, 1, 1], gap="small")
            with q1:
                if st.button("▤ 报销记录", key="quick_records"):
                    handle_demo_action("open_reimbursement_records"); st.rerun()
            with q2:
                if st.button("▥ 差旅规则", key="quick_rules"):
                    st.session_state.active_modal = "travel_rules"; st.rerun()
            with q3:
                if st.button("📎 附件", key="quick_files"):
                    st.session_state.active_modal = "attachment_menu"; st.rerun()

        with st.container(key="chat_input_row"):
            i1, i2, i3, i4 = st.columns([32, 238, 32, 32], gap="small")
            with i1:
                st.button("+", key="chat_plus")
            with i2:
                st.text_input("msg", placeholder="发消息", key="chat_message_input", label_visibility="collapsed")
            with i3:
                st.button("☺", key="chat_emoji")
            with i4:
                st.button("🎙", key="chat_voice")

        st.markdown('<div style="width:120px;height:4px;border-radius:99px;background:#111827;margin:9px auto 0;opacity:.9;"></div>', unsafe_allow_html=True)


def _render_msg(msg, idx):
    """Render dynamic chat messages as self-contained HTML (no cross-component wrapping)."""
    role = msg.get("role", "assistant")
    t = msg.get("type", "generic")
    if t == "time_chip":
        st.markdown(f'<div style="text-align:center;margin:12px 0;"><span style="background:#edf0f5;color:#8f959e;font-size:11px;padding:3px 10px;border-radius:99px;">{msg.get("time","")}</span></div>', unsafe_allow_html=True)
    elif role == "user":
        if t == "receipt_upload":
            fn = msg.get("filename", "file")
            st.markdown(f'<div style="max-width:260px;margin:8px 0 8px auto;padding:8px 12px;border-radius:12px;background:#d6efff;color:#1f2329;font-size:13px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;box-sizing:border-box;">{fn}</div>', unsafe_allow_html=True)
        else:
            c = msg.get("content", "")
            st.markdown(f'<div style="display:flex;justify-content:flex-end;margin-bottom:8px;"><div style="background:#95d4FF;color:#1f2329;border-radius:14px 2px 14px 14px;padding:9px 12px;max-width:240px;font-size:13px;line-height:1.45;">{c}</div></div>', unsafe_allow_html=True)
    elif t == "text":
        c = msg.get("content", "")
        st.markdown(f'<div style="display:flex;gap:8px;margin-bottom:8px;"><div style="width:32px;height:32px;border-radius:16px;background:#1677ff;color:white;display:flex;align-items:center;justify-content:center;font-size:15px;flex-shrink:0;">🤖</div><div style="max-width:300px;background:white;border-radius:12px;padding:10px 12px;font-size:13px;color:#1f2329;line-height:1.45;box-shadow:0 2px 8px rgba(15,23,42,.04);">{c}</div></div>', unsafe_allow_html=True)
    else:
        # Card-type messages (self-contained HTML)
        title = msg.get("title", ""); status = msg.get("status", ""); fields = msg.get("fields", [])
        hint = msg.get("hint", "")
        fhtml = ""
        if fields:
            rows = "".join(f'<div style="display:flex;justify-content:space-between;padding:4px 0;font-size:12px;border-bottom:1px solid #f5f5f5;"><span style="color:#8f959e;">{f[0]}</span><span style="color:#1f2329;font-weight:500;">{f[1]}</span></div>' for f in fields)
            fhtml = f'<div style="margin:6px 0;">{rows}</div>'
        shtml = f'<span style="display:inline-block;font-size:11px;font-weight:600;padding:2px 8px;border-radius:99px;background:#edf0f5;color:#646a73;margin-top:4px;">{status}</span>' if status else ''
        hhtml = f'<div style="font-size:11px;color:#8f959e;margin-top:6px;">{hint}</div>' if hint else ''
        st.markdown(f'<div style="display:flex;gap:8px;margin-bottom:8px;"><div style="width:32px;height:32px;border-radius:16px;background:#1677ff;color:white;display:flex;align-items:center;justify-content:center;font-size:15px;flex-shrink:0;">🤖</div><div style="max-width:300px;background:white;border:1px solid #e5e8ef;border-radius:14px;padding:12px;box-shadow:0 2px 8px rgba(15,23,42,.04);"><div style="font-size:14px;font-weight:700;color:#1f2329;margin-bottom:4px;">{title}</div>{fhtml}{shtml}{hhtml}</div></div>', unsafe_allow_html=True)
        # Dynamic card action buttons (rendered as real Streamlit buttons, no HTML wrapping)
        actions = msg.get("actions", [])
        if actions:
            _MAP = {"上传票据":"upload_receipt","查看/编辑详情":"open_edit_detail","确认并同步":"confirm_and_sync","更新详情信息":"save_detail_update","确认差异合理":"confirm_diff","重新上传":"reupload_receipt","申请临时调额":"apply_temp_limit","查看差旅规则":"open_travel_rule"}
            act_cols = st.columns(len(actions) if len(actions) <= 2 else 2)
            for i, (col, label) in enumerate(zip(act_cols, actions)):
                with col:
                    if st.button(label, key=f"dyn_{idx}_{i}_{label}"):
                        handle_demo_action(_MAP.get(label, label)); st.rerun()
