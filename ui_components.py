"""
UI Components for Travel Spend AI Assistant
============================================
DingTalk-style chat UI with mobile-first responsive layout.

Architecture (post-refactor):
- Chat message body: read-only HTML rendered in components.html iframe
  (NO interactive buttons inside iframe - all actions via Streamlit native)
- Interactive phone shell: see phone_shell.py
- H5 pages: see h5_pages.py (Streamlit native)
"""

import streamlit as st


# =============================================================================
# Phone Shell CSS (used by phone_shell.py)
# =============================================================================

PHONE_SHELL_CSS = """
<style>
/* Hide Streamlit chrome */
#MainMenu, footer, .stAppDeployButton,
div[data-testid="stToolbar"],
div[data-testid="stDecoration"],
header[data-testid="stHeader"] { display: none !important; }

/* Tab styling (desktop) */
.stTabs [data-baseweb="tab-panel"] { padding: 0; }
.stTabs [data-baseweb="tab-list"] {
    gap: 0; background: #f8f8f8; border-bottom: 1px solid #e8e8e8;
}
.stTabs [data-baseweb="tab"] { font-size: 13px; padding: 8px 16px; }

/* Desktop background */
.stApp { background: #f0f2f5 !important; }
.block-container { padding-top: 0.5rem !important; }

/* Buttons - DingTalk style */
.stButton > button {
    font-size: 13px !important;
    min-height: 38px !important;
    border-radius: 8px !important;
    transition: transform 0.1s ease, opacity 0.1s ease !important;
}
.stButton > button:active {
    transform: scale(0.97) !important;
    opacity: 0.85 !important;
}

/* iframe clean */
iframe { border: none !important; }

/* =============================================================
   MOBILE RESPONSIVE LAYOUT
   Mobile (<=768px): hide side panels, tabs, show full H5 page
   Desktop: keep phone simulator + flow panel layout
   ============================================================= */
@media (max-width: 768px) {
    /* Hide tab bar on mobile - auto show demo content */
    .stTabs [data-baseweb="tab-list"] {
        display: none !important;
    }
    /* Full width content */
    .block-container {
        padding: 0 !important;
        max-width: 100% !important;
    }
    /* Touch-friendly buttons */
    .stButton > button {
        min-height: 44px !important;
        font-size: 14px !important;
    }
    /* Mobile background */
    .stApp {
        background: #f5f5f5 !important;
    }
    /* Containers: tighter spacing */
    div[data-testid="stVerticalBlock"] {
        gap: 0.5rem !important;
    }
}

/* Tablet */
@media (min-width: 769px) and (max-width: 1024px) {
    .block-container {
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }
}
</style>
"""


# =============================================================================
# Chat Body CSS (for the read-only message iframe)
# =============================================================================

_CHAT_CSS = """
* { box-sizing: border-box; }
.chat-body {
    background: #f5f5f5; padding: 12px 12px 24px;
    min-height: 100%; overflow-y: auto;
    font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", "Segoe UI", Roboto, sans-serif;
}
.chat-body::-webkit-scrollbar { width: 0; }
.chat-body { scrollbar-width: none; }
.time-chip { text-align: center; margin: 14px 0; }
.time-chip span {
    background: rgba(0,0,0,0.05); color: #999;
    font-size: 11px; padding: 4px 12px; border-radius: 10px;
}
.ai-msg-row { display: flex; align-items: flex-start; gap: 8px; margin-bottom: 16px; }
.ai-avatar {
    width: 36px; height: 36px; border-radius: 6px;
    background: linear-gradient(135deg, #4A90D9, #357ABD);
    display: flex; align-items: center; justify-content: center;
    flex-shrink: 0; font-size: 16px; color: white;
}
.ai-card {
    background: #fff; border-radius: 2px 12px 12px 12px;
    padding: 12px 14px; max-width: 280px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}
.ai-card-title { font-size: 14px; font-weight: 600; color: #1a1a1a; margin-bottom: 6px; line-height: 1.4; }
.ai-card-subtitle { font-size: 12px; color: #666; margin-bottom: 10px; line-height: 1.4; }
.card-fields { width: 100%; margin: 6px 0; border-collapse: collapse; }
.card-fields tr { border-bottom: 1px solid #f5f5f5; }
.card-fields tr:last-child { border-bottom: none; }
.card-fields td { padding: 4px 0; font-size: 12px; word-break: break-word; line-height: 1.4; vertical-align: top; }
.card-fields td:first-child { color: #999; min-width: 58px; max-width: 72px; white-space: nowrap; padding-right: 8px; }
.card-fields td:last-child { color: #333; font-weight: 500; }
.status-badge { display: inline-block; font-size: 11px; font-weight: 500; padding: 2px 8px; border-radius: 4px; margin-top: 8px; }
.status-pending { background: #FFF3E0; color: #E65100; }
.status-success { background: #E8F5E9; color: #2E7D32; }
.status-error { background: #FFEBEE; color: #C62828; }
.status-warning { background: #FFF8E1; color: #F57F17; }
.status-info { background: #E3F2FD; color: #1565C0; }
.card-actions { display: flex; gap: 8px; margin-top: 12px; flex-wrap: wrap; }
.card-btn { font-size: 12px; padding: 6px 12px; border-radius: 6px; border: none; font-weight: 500; display: inline-block; cursor: default; }
.card-btn-primary { background: #1677FF; color: white; }
.card-btn-secondary { background: #f0f0f0; color: #333; }
.card-hint { font-size: 11px; color: #999; margin-top: 8px; line-height: 1.5; }
.suggestion-list { margin: 4px 0; padding-left: 16px; }
.suggestion-list li { font-size: 12px; color: #333; margin-bottom: 4px; }
.evidence-list { margin-top: 6px; padding-left: 12px; border-left: 2px solid #e8e8e8; }
.evidence-list li { font-size: 11px; color: #888; margin-bottom: 2px; list-style: none; }
.confidence-bar-wrapper { margin: 8px 0; }
.confidence-label { font-size: 11px; color: #999; margin-bottom: 3px; }
.confidence-bar { height: 6px; border-radius: 3px; background: #f0f0f0; overflow: hidden; }
.confidence-fill { height: 100%; border-radius: 3px; }
.user-msg-row { display: flex; justify-content: flex-end; margin-bottom: 16px; padding-right: 4px; }
.user-bubble { background: #95d4FF; color: #1a1a1a; border-radius: 12px 2px 12px 12px; padding: 10px 14px; max-width: 260px; font-size: 13px; line-height: 1.5; }
.user-receipt-card { background: #EBF5FF; border-radius: 12px 2px 12px 12px; padding: 10px 12px; max-width: 200px; border: 1px solid #C6E0F5; text-align: center; }
.user-receipt-card .receipt-thumb { width: 100%; height: 80px; border-radius: 6px; background: #D5E8F7; display: flex; align-items: center; justify-content: center; margin-bottom: 6px; font-size: 32px; color: #5B9BD5; overflow: hidden; }
.user-receipt-card .receipt-name { font-size: 12px; color: #333; font-weight: 500; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.user-receipt-card .receipt-meta { font-size: 11px; color: #888; margin-top: 2px; }
.receipt-uploaded-badge { display: inline-block; font-size: 10px; color: #2E7D32; background: #E8F5E9; padding: 2px 6px; border-radius: 3px; margin-top: 4px; }
.ai-card-warning { background: #FFFAF0; border-radius: 2px 12px 12px 12px; padding: 12px 14px; max-width: 280px; box-shadow: 0 1px 3px rgba(0,0,0,0.06); border-left: 3px solid #FF9800; }
.ai-card-error { background: #FFF8F6; border-radius: 2px 12px 12px 12px; padding: 12px 14px; max-width: 280px; box-shadow: 0 1px 3px rgba(0,0,0,0.06); border-left: 3px solid #F44336; }
.ai-card-success { background: #F6FFF6; border-radius: 2px 12px 12px 12px; padding: 12px 14px; max-width: 280px; box-shadow: 0 1px 3px rgba(0,0,0,0.06); border-left: 3px solid #4CAF50; }
.security-card { background: #FFF8F8; border: 1px solid #FFCDD2; border-radius: 12px; padding: 12px 14px; max-width: 280px; }
.security-icon { font-size: 20px; margin-bottom: 6px; }
.empty-state { text-align: center; padding: 80px 24px 60px; color: #bbb; }
.empty-state-icon { font-size: 52px; margin-bottom: 16px; }
.empty-state-text { font-size: 14px; color: #999; line-height: 1.7; }
"""


def get_chat_css() -> str:
    """Return the chat CSS string."""
    return _CHAT_CSS


# =============================================================================
# HTML builders for chat messages (read-only display)
# =============================================================================

def _status_class(status):
    mapping = {
        "\u5f85\u8865\u7968": "status-pending", "\u5f85\u8865\u7968\u636e": "status-pending",
        "\u5df2\u8bc6\u522b": "status-info", "\u5339\u914d\u6210\u529f": "status-success",
        "\u652f\u4ed8\u5931\u8d25": "status-error", "\u9700\u8981\u786e\u8ba4": "status-warning",
        "\u5df2\u62e6\u622a": "status-error", "\u5df2\u540c\u6b65": "status-success",
    }
    return mapping.get(status, "status-info")


def _card_class_for_status(status):
    cls = _status_class(status)
    if cls == "status-warning": return "ai-card-warning"
    elif cls == "status-error": return "ai-card-error"
    elif cls == "status-success": return "ai-card-success"
    return "ai-card"


def _render_fields_html(fields):
    rows = "".join(f'<tr><td>{f[0]}</td><td>{f[1]}</td></tr>' for f in fields)
    return f'<table class="card-fields">{rows}</table>'


def _build_actions_html(actions):
    """Render action labels as DISABLED visual hints (not clickable in iframe)."""
    if not actions:
        return ""
    btns = ""
    for i, action in enumerate(actions):
        cls = "card-btn card-btn-primary" if i == 0 else "card-btn card-btn-secondary"
        btns += f'<span class="{cls}">{action}</span>'
    return f'<div class="card-actions">{btns}</div>'


def _build_evidence_html(evidence):
    if not evidence:
        return ""
    items = "".join(f"<li>{e}</li>" for e in evidence)
    return f'<ul class="evidence-list">{items}</ul>'


def _confidence_color(confidence):
    if confidence >= 0.85: return "#4CAF50"
    elif confidence >= 0.60: return "#FF9800"
    return "#F44336"


def _load_image_as_data_uri(image_path):
    import base64, os
    if not image_path or not os.path.isfile(image_path):
        return ""
    try:
        with open(image_path, "rb") as f:
            data = base64.b64encode(f.read()).decode("ascii")
        ext = os.path.splitext(image_path)[1].lower().lstrip(".")
        mime = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg"}.get(ext, "image/png")
        return f"data:{mime};base64,{data}"
    except Exception:
        return ""


def build_time_chip(time_str):
    return f'<div class="time-chip"><span>{time_str}</span></div>'


def build_empty_state():
    return (
        '<div class="empty-state">'
        '<div class="empty-state-icon">&#9992;</div>'
        '<div class="empty-state-text">'
        '\u6682\u65e0\u5dee\u65c5\u4e8b\u4ef6<br/>'
        '\u70b9\u51fb\u4e0b\u65b9\u300c\u62a5\u9500\u8bb0\u5f55\u300d\u6216\u53f3\u4fa7\u300c\u4f53\u9a8c\u6d41\u7a0b\u300d\u5f00\u59cb'
        '</div></div>'
    )


def build_ai_card(msg):
    title = msg.get("title", "")
    subtitle = msg.get("subtitle", "")
    fields = msg.get("fields", [])
    status = msg.get("status", "")
    actions = msg.get("actions", [])
    hint = msg.get("hint", "")
    evidence = msg.get("evidence", [])

    card_cls = _card_class_for_status(status) if status else "ai-card"
    fields_html = _render_fields_html(fields) if fields else ""
    status_html = f'<span class="status-badge {_status_class(status)}">{status}</span>' if status else ""
    actions_html = _build_actions_html(actions)
    hint_html = f'<div class="card-hint">{hint}</div>' if hint else ""
    evidence_html = _build_evidence_html(evidence) if evidence else ""
    subtitle_html = f'<div class="ai-card-subtitle">{subtitle}</div>' if subtitle else ""

    return (
        '<div class="ai-msg-row">'
        '<div class="ai-avatar">&#129302;</div>'
        f'<div class="{card_cls}">'
        f'<div class="ai-card-title">{title}</div>'
        f'{subtitle_html}{fields_html}{status_html}{actions_html}{hint_html}{evidence_html}'
        '</div></div>'
    )


def build_user_receipt_bubble(filename="hotel_receipt.pdf", size="1.2 MB", image_path=""):
    data_uri = _load_image_as_data_uri(image_path)
    if data_uri:
        thumb_html = f'<div class="receipt-thumb"><img src="{data_uri}" style="width:100%;height:100%;object-fit:cover;border-radius:6px;" /></div>'
    else:
        thumb_html = '<div class="receipt-thumb">&#128196;</div>'
    return (
        '<div class="user-msg-row">'
        '<div class="user-receipt-card">'
        f'{thumb_html}'
        f'<div class="receipt-name">{filename}</div>'
        f'<div class="receipt-meta">{size}</div>'
        '<span class="receipt-uploaded-badge">\u5df2\u4e0a\u4f20</span>'
        '</div></div>'
    )


def build_user_text_bubble(text):
    return f'<div class="user-msg-row"><div class="user-bubble">{text}</div></div>'


def build_ai_text_bubble(text):
    return (
        '<div class="ai-msg-row">'
        '<div class="ai-avatar">&#129302;</div>'
        '<div class="ai-card" style="padding:10px 14px;">'
        f'<span style="font-size:13px;color:#333;line-height:1.5;">{text}</span>'
        '</div></div>'
    )


def build_match_success_card(msg):
    title = msg.get("title", "")
    confidence = msg.get("confidence", 0.0)
    confidence_pct = int(confidence * 100)
    basis = msg.get("basis", "")
    status = msg.get("status", "\u5339\u914d\u6210\u529f")
    evidence = msg.get("evidence", [])
    evidence_html = _build_evidence_html(evidence)
    color = _confidence_color(confidence)
    return (
        '<div class="ai-msg-row"><div class="ai-avatar">&#129302;</div>'
        '<div class="ai-card-success">'
        f'<div class="ai-card-title">{title}</div>'
        f'<div class="confidence-bar-wrapper"><div class="confidence-label">\u5339\u914d\u7f6e\u4fe1\u5ea6 {confidence_pct}%</div>'
        f'<div class="confidence-bar"><div class="confidence-fill" style="width:{confidence_pct}%;background:{color};"></div></div></div>'
        f'<div style="font-size:12px;color:#555;margin:6px 0;">{basis}</div>'
        f'<span class="status-badge {_status_class(status)}">{status}</span>'
        f'{evidence_html}</div></div>'
    )


def build_low_confidence_card(msg):
    title = msg.get("title", "")
    fields = msg.get("fields", [])
    reason = msg.get("reason", "")
    suggestion = msg.get("suggestion", "")
    status = msg.get("status", "\u9700\u8981\u786e\u8ba4")
    confidence = msg.get("confidence", 0.0)
    evidence = msg.get("evidence", [])
    confidence_pct = int(confidence * 100)
    color = _confidence_color(confidence)
    fields_html = _render_fields_html(fields) if fields else ""
    evidence_html = _build_evidence_html(evidence)
    return (
        '<div class="ai-msg-row"><div class="ai-avatar">&#129302;</div>'
        '<div class="ai-card-warning">'
        f'<div class="ai-card-title">{title}</div>{fields_html}'
        f'<div class="confidence-bar-wrapper"><div class="confidence-label">\u5339\u914d\u7f6e\u4fe1\u5ea6 {confidence_pct}%</div>'
        f'<div class="confidence-bar"><div class="confidence-fill" style="width:{confidence_pct}%;background:{color};"></div></div></div>'
        f'<div style="font-size:12px;color:#666;margin:6px 0;"><b>\u53ef\u80fd\u539f\u56e0:</b> {reason}</div>'
        f'<div style="font-size:12px;color:#666;margin:4px 0;"><b>\u5efa\u8bae:</b> {suggestion}</div>'
        f'<span class="status-badge {_status_class(status)}">{status}</span>'
        f'{evidence_html}</div></div>'
    )


def build_payment_failure_card(msg):
    title = msg.get("title", "")
    fields = msg.get("fields", [])
    suggestions = msg.get("suggestions", [])
    status = msg.get("status", "\u652f\u4ed8\u5931\u8d25")
    evidence = msg.get("evidence", [])
    fields_html = _render_fields_html(fields) if fields else ""
    evidence_html = _build_evidence_html(evidence)
    suggestions_html = ""
    if suggestions:
        items = "".join(f"<li>{s}</li>" for s in suggestions)
        suggestions_html = f'<div style="font-size:12px;color:#555;margin-top:6px;"><b>\u5efa\u8bae:</b></div><ul class="suggestion-list">{items}</ul>'
    return (
        '<div class="ai-msg-row"><div class="ai-avatar">&#129302;</div>'
        '<div class="ai-card-error">'
        f'<div class="ai-card-title">{title}</div>'
        f'{fields_html}{suggestions_html}'
        f'<span class="status-badge {_status_class(status)}">{status}</span>'
        f'{evidence_html}</div></div>'
    )


def build_security_warning_card(msg):
    title = msg.get("title", "")
    body = msg.get("body", "")
    status = msg.get("status", "\u5df2\u62e6\u622a")
    evidence = msg.get("evidence", [])
    evidence_html = _build_evidence_html(evidence)
    return (
        '<div class="ai-msg-row"><div class="ai-avatar">&#129302;</div>'
        '<div class="security-card"><div class="security-icon">&#128737;</div>'
        f'<div class="ai-card-title">{title}</div>'
        f'<div style="font-size:12px;color:#555;margin:8px 0;">{body}</div>'
        f'<span class="status-badge {_status_class(status)}">{status}</span>'
        f'{evidence_html}</div></div>'
    )


# =============================================================================
# Main chat body HTML builder (read-only, no interactive elements)
# =============================================================================

def build_chat_body_html(messages):
    """Build complete HTML for the chat message area.
    Rendered inside a components.html iframe for visual fidelity.
    NO interactive buttons - actions handled by Streamlit buttons outside."""
    body_parts = []
    if not messages:
        body_parts.append(build_empty_state())
    else:
        for msg in messages:
            role = msg.get("role", "assistant")
            msg_type = msg.get("type", "generic")

            if msg_type == "time_chip":
                body_parts.append(build_time_chip(msg.get("time", "")))
            elif role == "user" and msg_type == "receipt_upload":
                body_parts.append(build_user_receipt_bubble(
                    msg.get("filename", "receipt.pdf"),
                    msg.get("size", "1.2 MB"),
                    msg.get("image_path", ""),
                ))
            elif role == "user" and msg_type == "text":
                body_parts.append(build_user_text_bubble(msg.get("content", "")))
            elif role == "assistant" and msg_type == "text":
                body_parts.append(build_ai_text_bubble(msg.get("content", "")))
            elif msg_type == "match_success":
                body_parts.append(build_match_success_card(msg))
            elif msg_type == "low_confidence":
                body_parts.append(build_low_confidence_card(msg))
            elif msg_type == "payment_failure":
                body_parts.append(build_payment_failure_card(msg))
            elif msg_type == "security_warning":
                body_parts.append(build_security_warning_card(msg))
            else:
                body_parts.append(build_ai_card(msg))

    body_content = "\n".join(body_parts)

    return (
        '<!DOCTYPE html><html><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        '<style>'
        'html,body{margin:0;padding:0;height:100%;overflow-y:auto;'
        'font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Segoe UI",Roboto,sans-serif;'
        'background:#f5f5f5;}'
        + _CHAT_CSS
        + '</style></head><body>'
        '<div class="chat-body" id="chatBody">' + body_content + '</div>'
        '<script>var cb=document.getElementById("chatBody");if(cb){cb.scrollTop=cb.scrollHeight;}</script>'
        '</body></html>'
    )


# Legacy alias for backwards compat with imports
build_chat_page_html = build_chat_body_html
