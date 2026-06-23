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


def _get_query_param(name: str, default: str = "") -> str:
    try:
        value = st.query_params.get(name, default)
        if isinstance(value, list):
            return value[0] if value else default
        return value or default
    except Exception:
        try:
            params = st.experimental_get_query_params()
            values = params.get(name, [default])
            return values[0] if values else default
        except Exception:
            return default


def _set_query_param(name: str, value: str) -> None:
    try:
        st.query_params[name] = value
        return
    except Exception:
        pass

    try:
        params = st.experimental_get_query_params()
        params[name] = value
        st.experimental_set_query_params(**params)
    except Exception:
        return


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

    if st.session_state.get("demo_authed") or _get_query_param("demo_authed") == "1":
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
            _set_query_param("demo_authed", "1")
            st.rerun()
        else:
            st.error("口令不正确，请重试")

    st.stop()
