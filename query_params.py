import streamlit as st


AUTH_QUERY_KEY = "demo_authed"


def get_query_param(name: str, default: str = "") -> str:
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


def current_query_params() -> dict[str, str]:
    result = {}
    try:
        for key in st.query_params.keys():
            value = st.query_params.get(key)
            if isinstance(value, list):
                result[key] = value[0] if value else ""
            else:
                result[key] = value or ""
        return result
    except Exception:
        try:
            raw = st.experimental_get_query_params()
            for key, values in raw.items():
                result[key] = values[0] if values else ""
            return result
        except Exception:
            return {}


def set_query_params_preserving_auth(**updates: str | None) -> None:
    """
    Update URL query params while preserving demo_authed=1 if it is present.

    Pass value=None to remove a key.
    """
    params = current_query_params()

    auth_value = params.get(AUTH_QUERY_KEY)
    if auth_value == "1":
        params[AUTH_QUERY_KEY] = "1"

    for key, value in updates.items():
        if value is None:
            params.pop(key, None)
        else:
            params[key] = str(value)

    if auth_value == "1":
        params[AUTH_QUERY_KEY] = "1"

    try:
        st.query_params.clear()
        for key, value in params.items():
            st.query_params[key] = value
        return
    except Exception:
        pass

    try:
        st.experimental_set_query_params(**params)
    except Exception:
        return


def mark_demo_authed() -> None:
    set_query_params_preserving_auth(**{AUTH_QUERY_KEY: "1"})


def is_demo_authed_in_query() -> bool:
    return get_query_param(AUTH_QUERY_KEY) == "1"
