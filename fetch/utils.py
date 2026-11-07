"""Small shared helpers: session state, fragments, per-session memoization, fingerprints."""
import hashlib

import pandas
import streamlit as st

# Fragments rerun only the decorated function on widget interaction instead of the whole script.
fragment = getattr(st, "fragment", None) or getattr(st, "experimental_fragment", None) or (lambda f: f)


# Using st.session_state before Streamlit initializes can raise in some reload/timing
# scenarios; these wrappers fall back quietly.
def safe_session_get(key, default=None):
    try:
        return st.session_state.get(key, default)
    except Exception:
        return default


def safe_session_set(key, value):
    try:
        st.session_state[key] = value
    except Exception:
        pass


def nav_selector(label: str, options: list, key: str):
    """Single-choice navigation that only runs the selected section (unlike st.tabs, which runs all)."""
    if hasattr(st, "segmented_control"):
        choice = st.segmented_control(label, options, default=options[0], key=key, label_visibility="collapsed")
    else:
        choice = st.radio(label, options, horizontal=True, key=key, label_visibility="collapsed")
    return choice if choice in options else options[0]


def fingerprint(*parts) -> str:
    """Stable short hash of the given parts (used to key derived datasets)."""
    return hashlib.sha1("\x1f".join(map(repr, parts)).encode()).hexdigest()[:20]


def session_memo(step: str, key, compute):
    """Return compute() for `key`, reusing the last result of `step` in this session if the key matches.

    Only one result per step is retained per session, so memory stays bounded and is
    released with the session (unlike global st.cache_data entries). Results are shared
    by reference: callers must not mutate them in place.
    """
    memo = st.session_state.setdefault("_fetch_step_memo", {})
    hit = memo.get(step)
    if hit is not None and hit[0] == key:
        return hit[1]
    value = compute()
    memo[step] = (key, value)
    return value


def csv_bytes(df: pandas.DataFrame, index: bool = True):
    """Callable producing CSV bytes on demand, for st.download_button(data=...) deferred downloads."""
    return lambda: df.to_csv(index=index).encode("utf-8")
