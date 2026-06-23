"""
Auth Gate – lightweight password gate for Streamlit Community Cloud demo.
=========================================================================
Reads DEMO_PASSWORD from st.secrets. If not configured, skips auth entirely
so local development is unaffected.

Usage (in app.py, before any UI):
    from auth_gate import check_auth
    check_auth()
"""

import streamlit as st
from query_params import get_query_param, mark_demo_authed, is_demo_authed_in_query


def check_auth() -> None:
    """If DEMO_PASSWORD is configured in secrets, require it before showing the app.

    Supports URL query param demo_authed=1 so that a page refresh does not
    re-prompt for the password within the same browser session.
    """
    try:
        expected = st.secrets["DEMO_PASSWORD"]
    except (KeyError, FileNotFoundError):
        # No password configured – skip auth
        return

    if not expected:
        # Empty password – skip auth
        return

    if st.session_state.get("demo_authed") or is_demo_authed_in_query():
        st.session_state["demo_authed"] = True
        return

    st.markdown(
        """
        <div style="display:flex;align-items:center;justify-content:center;
                    min-height:60vh;flex-direction:column;">
            <div style="font-size:28px;font-weight:700;margin-bottom:6px;">✈️ AI 差旅支出助手</div>
            <div style="font-size:14px;color:#646a73;margin-bottom:24px;">请输入演示口令</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    pwd = st.text_input("口令", type="password", label_visibility="collapsed")

    if st.button("进入", type="primary", use_container_width=True):
        if pwd == expected:
            st.session_state["demo_authed"] = True
            mark_demo_authed()
            st.rerun()
        else:
            st.error("口令不正确，请重试")

    st.stop()
