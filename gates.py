from __future__ import annotations

import streamlit as st

from config import FEATURE_LABELS, TIERS


def get_tier_config() -> dict:
    """Return the config dict for the current user's tier."""
    from storage import get_user_tier
    tier = get_user_tier()
    return TIERS.get(tier, TIERS["free"])


def is_feature_allowed(feature: str) -> bool:
    """Return True if the current tier grants access to this feature."""
    cfg = get_tier_config()
    return bool(cfg.get(feature, False))


def is_exam_allowed(exam: str) -> bool:
    """Return True if the current tier allows this exam."""
    cfg = get_tier_config()
    allowed = cfg.get("allowed_exams", [])
    if allowed == "all":
        return True
    return exam in allowed


def get_daily_question_limit() -> int | None:
    """Return the daily question limit for the current tier (None = unlimited)."""
    return get_tier_config().get("daily_question_limit")


def get_labs_per_cert_limit() -> int | None:
    """Return the lab-per-cert limit for the current tier (None = unlimited)."""
    return get_tier_config().get("labs_per_cert")


def show_upgrade_prompt(feature: str) -> None:
    """Render the standard upgrade call-to-action for a locked feature."""
    label = FEATURE_LABELS.get(feature, feature.replace("_", " ").title())
    st.warning(
        f"**Pro Feature** — Upgrade to unlock **{label}**, "
        "plus unlimited questions across all 50+ certs, "
        "AI tutoring, resume builder, and career tools."
    )
    if st.button("Upgrade to Pro →", key=f"upgrade_btn_{feature}", type="primary"):
        # Navigate to upgrade tab by setting a session flag app.py reads
        st.session_state["open_upgrade_tab"] = True
        st.rerun()


def require_feature(feature: str) -> bool:
    """Check access and show upgrade prompt if blocked. Returns True if allowed."""
    if is_feature_allowed(feature):
        return True
    show_upgrade_prompt(feature)
    return False
