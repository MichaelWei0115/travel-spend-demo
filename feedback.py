"""
Unified Feedback Components
============================
Toast, Loading, Empty State, Confirm, Button feedback for the app.
Encapsulated in one file for easy rollback per Ticket #23 risk mitigation.
"""

import streamlit as st
import time


# =============================================================================
# Global Feedback Styles (injected once per page render)
# =============================================================================

FEEDBACK_CSS = """
<style>
/* ===== Ticket 23: Unified Feedback & Mobile UX ===== */

/* --- Mobile: 44px min touch target --- */
@media (max-width: 519px) {
    .stButton > button {
        min-height: 44px !important;
        font-size: 14px !important;
        padding: 8px 16px !important;
    }
    /* Bottom safe area padding for pages with bottom actions */
    .h5-bottom-actions {
        padding-bottom: env(safe-area-inset-bottom, 16px) !important;
    }
    /* Compact cards on mobile */
    div[data-testid="stVerticalBlock"] > div[data-testid="stExpander"],
    div[data-testid="stVerticalBlock"] > div:has(> .element-container > div[data-testid="stMarkdown"]) {
        margin-bottom: 0.25rem;
    }
}

/* --- Button click/active state --- */
.stButton > button:active {
    transform: scale(0.97) !important;
    opacity: 0.85 !important;
    transition: transform 0.1s ease, opacity 0.1s ease !important;
}
.stButton > button {
    transition: transform 0.1s ease, opacity 0.1s ease, background-color 0.15s ease !important;
}

/* --- Disabled button visual --- */
.stButton > button:disabled {
    opacity: 0.5 !important;
    cursor: not-allowed !important;
    pointer-events: none !important;
}

/* --- Toast: positioned to not block main action buttons --- */
div[data-testid="stToast"] {
    top: auto !important;
    bottom: 72px !important;
    right: 16px !important;
    z-index: 9999 !important;
}
@media (max-width: 519px) {
    div[data-testid="stToast"] {
        bottom: calc(env(safe-area-inset-bottom, 16px) + 56px) !important;
        right: 8px !important;
        left: 8px !important;
        max-width: calc(100% - 16px) !important;
    }
}

/* --- Loading spinner: inline and non-blocking --- */
.stSpinner {
    min-height: 32px !important;
}

/* --- Horizontal scroll for status badges (filter tabs) --- */
.filter-scroll-container {
    overflow-x: auto !important;
    white-space: nowrap !important;
    -webkit-overflow-scrolling: touch;
    scrollbar-width: none;
    padding-bottom: 4px;
}
.filter-scroll-container::-webkit-scrollbar {
    display: none;
}

/* --- Empty state styling --- */
.empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 60px 24px;
    text-align: center;
    color: #bbb;
}
.empty-state-icon {
    font-size: 48px;
    margin-bottom: 12px;
    opacity: 0.6;
}
.empty-state-text {
    font-size: 14px;
    line-height: 1.6;
    color: #999;
}

/* --- Confirm dialog inline --- */
.confirm-box {
    background: #fff8e1;
    border: 1px solid #ffe082;
    border-radius: 8px;
    padding: 12px 16px;
    margin: 8px 0;
    font-size: 13px;
}

/* --- H5 page back button: clear positioning --- */
.h5-back-btn .stButton > button {
    font-size: 20px !important;
    min-width: 36px !important;
    min-height: 36px !important;
    padding: 0 8px !important;
    border: none !important;
    background: transparent !important;
}
@media (max-width: 519px) {
    .h5-back-btn .stButton > button {
        min-height: 44px !important;
        min-width: 44px !important;
    }
}
</style>
"""


def inject_feedback_styles():
    """Inject the unified feedback CSS. Call once per page render."""
    st.html(FEEDBACK_CSS)


# =============================================================================
# Empty State
# =============================================================================

def render_empty_state(icon: str = "\U0001f4ed", text: str = "\u6682\u65e0\u6570\u636e"):
    """Render an empty state placeholder with icon and message."""
    st.markdown(
        f'<div class="empty-state">'
        f'<div class="empty-state-icon">{icon}</div>'
        f'<div class="empty-state-text">{text}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


# =============================================================================
# Loading Simulation
# =============================================================================

def with_loading(label: str = "\u5904\u7406\u4e2d...", duration: float = 0.8):
    """Context-manager-style loading spinner for async-simulated actions."""
    return st.spinner(label)


def simulate_async(label: str = "\u5904\u7406\u4e2d...", duration: float = 0.8):
    """Show a brief loading indicator then continue. For demo mock delays."""
    with st.spinner(label):
        time.sleep(duration)


# =============================================================================
# Confirm Dialog (inline)
# =============================================================================

def render_confirm(message: str, confirm_key: str, cancel_key: str,
                   confirm_label: str = "\u786e\u8ba4",
                   cancel_label: str = "\u53d6\u6d88") -> str:
    """
    Render an inline confirmation box with two buttons.
    Returns: "confirm", "cancel", or "" (no action yet).
    """
    st.markdown(
        f'<div class="confirm-box">{message}</div>',
        unsafe_allow_html=True,
    )
    col1, col2 = st.columns(2)
    with col1:
        if st.button(confirm_label, key=confirm_key, type="primary", use_container_width=True):
            return "confirm"
    with col2:
        if st.button(cancel_label, key=cancel_key, use_container_width=True):
            return "cancel"
    return ""


# =============================================================================
# Toast Helpers (wrapping existing mechanism in demo_actions)
# =============================================================================

def show_success_toast(message: str):
    """Show a success toast via session_state."""
    st.session_state.toast_message = f"\u2705 {message}"


def show_error_toast(message: str):
    """Show an error toast via session_state."""
    st.session_state.toast_message = f"\u274c {message}"


def show_info_toast(message: str):
    """Show an info toast via session_state."""
    st.session_state.toast_message = f"\u2139\ufe0f {message}"
