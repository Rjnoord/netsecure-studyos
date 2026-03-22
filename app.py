from __future__ import annotations

from datetime import date, datetime, timedelta
import socket

import streamlit as st

from auth import hash_passcode, is_locked_until, lockout_expiry_iso, passcode_feedback, verify_passcode
from exams import EXAM_DOMAINS
from storage import (
    delete_active_session,
    ensure_storage,
    is_file_persistence_enabled,
    load_active_sessions,
    load_results,
    load_user_profile,
    persistence_status,
    save_user_profile,
    update_streak,
)
from tracker import (
    calculate_readiness,
    confidence_by_domain,
    predict_exam_score,
    recommended_next_topic,
    review_queue,
    topic_history_frame,
)
from utils import (
    default_minutes_for_exam,
    inject_app_css,
    render_brand_ribbon,
    render_hero_panel,
    render_section_note,
    render_showcase_strip,
)
from pages._shared import _refresh_profile, _save_onboarding, _storage_caption
import pages.dashboard as page_dashboard
import pages.quiz as page_quiz
import pages.simulator as page_simulator
import pages.weak_topics as page_weak_topics
import pages.study_plan as page_study_plan
import pages.cheat_sheets as page_cheat_sheets
import pages.prediction as page_prediction
import pages.review_queue as page_review_queue
import pages.labs as page_labs


st.set_page_config(page_title="NetSecure StudyOS", page_icon="🧠", layout="wide")
inject_app_css()
ensure_storage()
if "streak_checked" not in st.session_state:
    update_streak()
    st.session_state["streak_checked"] = True


def _initialize_state() -> None:
    st.session_state.setdefault("authenticated", False)
    st.session_state.setdefault("practice_quiz", None)
    st.session_state.setdefault("practice_result", None)
    st.session_state.setdefault("sim_quiz", None)
    st.session_state.setdefault("sim_result", None)


def _render_storage_notice() -> None:
    mode, message = persistence_status()
    if not message:
        return
    if mode == "cloud-memory":
        st.info(message)
    else:
        st.warning(message)


def _load_saved_sessions() -> None:
    sessions = load_active_sessions()
    session_by_mode = {
        "practice": "practice_quiz",
        "exam_simulator": "sim_quiz",
    }
    for session in sessions:
        key = session_by_mode.get(session.get("mode"))
        if key and st.session_state.get(key) is None:
            st.session_state[key] = session


def _render_onboarding(profile: dict) -> dict:
    st.title("NetSecure StudyOS")
    st.caption("First-run onboarding personalizes readiness scoring, study plans, and recommendations.")
    render_section_note(
        "Set your target exam, target date, weekly study capacity, and confidence by domain. This tunes the app around your actual plan."
    )

    with st.form("first_run_onboarding", clear_on_submit=False):
        target_exam = st.selectbox("Target exam", list(EXAM_DOMAINS.keys()))
        target_date = st.date_input("Target exam date", value=date.today() + timedelta(days=45))
        weekly_hours = st.slider("Weekly study hours", min_value=1, max_value=30, value=int(profile.get("weekly_study_hours", 6)))
        st.markdown("### Self-Rated Confidence By Domain")
        st.caption("Rate each domain from 1 = very low confidence to 5 = very strong.")
        domain_ratings = {}
        existing = profile.get("domain_self_ratings", {}).get(target_exam, {})
        columns = st.columns(2)
        for index, domain in enumerate(EXAM_DOMAINS[target_exam]):
            with columns[index % 2]:
                domain_ratings[domain] = st.slider(
                    domain,
                    min_value=1,
                    max_value=5,
                    value=int(existing.get(domain, 3)),
                    key=f"onboarding_{target_exam}_{domain}",
                )
        submitted = st.form_submit_button("Save Profile And Start", type="primary", use_container_width=True)

    if submitted:
        if target_date <= date.today():
            st.error("Choose a target date in the future so the study plan can pace correctly.")
            return profile
        profile = _save_onboarding(profile, target_exam, target_date, weekly_hours, domain_ratings)
        st.success("Profile saved. Your dashboard is now personalized.")
        st.rerun()

    st.stop()


def _local_access_urls() -> tuple[str, str]:
    local_url = "http://localhost:8501"
    try:
        lan_ip = socket.gethostbyname(socket.gethostname())
        lan_url = f"http://{lan_ip}:8501"
    except OSError:
        lan_url = "Unavailable"
    return local_url, lan_url


def _render_passcode_setup(profile: dict) -> dict:
    st.title("NetSecure StudyOS")
    st.caption("Set a local passcode before enabling broader access.")
    render_section_note(
        f"This passcode gate protects the app before you share it on your LAN or behind a public URL. The passcode is {_storage_caption().lower()} as a salted hash."
    )
    with st.form("passcode_setup_form", clear_on_submit=False):
        passcode = st.text_input("Create passcode", type="password")
        confirm_passcode = st.text_input("Confirm passcode", type="password")
        submitted = st.form_submit_button("Save Passcode And Continue", type="primary", use_container_width=True)
    if submitted:
        issues = passcode_feedback(passcode)
        if passcode != confirm_passcode:
            issues.append("Passcode confirmation does not match.")
        if issues:
            for issue in issues:
                st.error(issue)
        else:
            passcode_hash, passcode_salt = hash_passcode(passcode)
            profile["auth"]["passcode_hash"] = passcode_hash
            profile["auth"]["passcode_salt"] = passcode_salt
            profile["auth"]["failed_attempts"] = 0
            profile["auth"]["lockout_until"] = None
            profile["auth"]["updated_at"] = datetime.now().isoformat()
            save_user_profile(profile)
            st.session_state["authenticated"] = True
            st.success("Passcode saved.")
            st.rerun()
    st.stop()


def _require_passcode(profile: dict) -> dict:
    auth_state = profile.get("auth", {})
    passcode_hash = auth_state.get("passcode_hash")
    passcode_salt = auth_state.get("passcode_salt")
    if not passcode_hash or not passcode_salt:
        _render_passcode_setup(profile)

    if st.session_state.get("authenticated"):
        return profile

    if is_locked_until(auth_state.get("lockout_until")):
        st.title("NetSecure StudyOS")
        st.error(f"Too many failed attempts. Try again after {auth_state.get('lockout_until')}.")
        st.stop()

    st.title("NetSecure StudyOS")
    st.caption("Enter the local passcode to continue.")
    with st.form("passcode_unlock_form", clear_on_submit=False):
        passcode = st.text_input("Passcode", type="password")
        submitted = st.form_submit_button("Unlock", type="primary", use_container_width=True)
    if submitted:
        if verify_passcode(passcode, passcode_hash, passcode_salt):
            profile["auth"]["failed_attempts"] = 0
            profile["auth"]["lockout_until"] = None
            save_user_profile(profile)
            st.session_state["authenticated"] = True
            st.rerun()
        else:
            failed_attempts = int(auth_state.get("failed_attempts", 0)) + 1
            profile["auth"]["failed_attempts"] = failed_attempts
            if failed_attempts >= 5:
                profile["auth"]["lockout_until"] = lockout_expiry_iso()
                profile["auth"]["failed_attempts"] = 0
            save_user_profile(profile)
            st.error("Incorrect passcode.")
    st.stop()


def _render_profile_editor(profile: dict) -> dict:
    with st.expander("Edit Study Profile"):
        exam_options = list(EXAM_DOMAINS.keys())
        current_target_exam = profile.get("target_exam") if profile.get("target_exam") in EXAM_DOMAINS else exam_options[0]
        current_target_date = profile.get("target_date")
        try:
            parsed_target_date = datetime.fromisoformat(current_target_date).date() if current_target_date else date.today() + timedelta(days=45)
        except ValueError:
            parsed_target_date = date.today() + timedelta(days=45)
        with st.form("edit_profile_form", clear_on_submit=False):
            target_exam = st.selectbox("Target exam", exam_options, index=exam_options.index(current_target_exam))
            target_date = st.date_input("Target exam date", value=parsed_target_date, key="edit_target_date")
            weekly_hours = st.slider(
                "Weekly study hours",
                min_value=1,
                max_value=30,
                value=int(profile.get("weekly_study_hours", 6)),
                key="edit_weekly_hours",
            )
            st.markdown("### Self-Rated Confidence By Domain")
            domain_ratings = {}
            existing = profile.get("domain_self_ratings", {}).get(target_exam, {})
            columns = st.columns(2)
            for index, domain in enumerate(EXAM_DOMAINS[target_exam]):
                with columns[index % 2]:
                    domain_ratings[domain] = st.slider(
                        domain,
                        min_value=1,
                        max_value=5,
                        value=int(existing.get(domain, 3)),
                        key=f"edit_{target_exam}_{domain}",
                    )
            submitted = st.form_submit_button("Update Profile", use_container_width=True)
        if submitted:
            if target_date <= date.today():
                st.error("Choose a target date in the future so the study plan can pace correctly.")
            else:
                profile = _save_onboarding(profile, target_exam, target_date, weekly_hours, domain_ratings)
                st.success("Study profile updated.")
                st.rerun()
    return profile


def _render_share_settings(profile: dict) -> dict:
    with st.expander("Access And Share Settings"):
        local_url, lan_url = _local_access_urls()
        st.write(f"Local URL: {local_url}")
        st.write(f"LAN URL: {lan_url}")
        st.caption("To make the app available to everybody, expose it through a trusted public host or tunnel and paste the resulting URLs below.")
        with st.form("share_links_form", clear_on_submit=False):
            public_app_url = st.text_input("Public app URL", value=profile.get("links", {}).get("public_app_url") or "")
            mobile_app_url = st.text_input("Mobile app URL", value=profile.get("links", {}).get("mobile_app_url") or "")
            submitted = st.form_submit_button("Save Share Links", use_container_width=True)
        if submitted:
            profile.setdefault("links", {})
            profile["links"]["public_app_url"] = public_app_url.strip() or None
            profile["links"]["mobile_app_url"] = mobile_app_url.strip() or None
            save_user_profile(profile)
            st.success("Share links saved.")
            st.rerun()
    return profile


def _render_saved_sessions_sidebar() -> None:
    sessions = load_active_sessions()
    if not sessions:
        return
    st.subheader("Resume Session")
    mode_to_key = {"practice": "practice_quiz", "exam_simulator": "sim_quiz"}
    for session in reversed(sessions):
        answered = sum(1 for value in session.get("answers", {}).values() if value)
        label = f"{session['exam']} • {session['label']}"
        st.caption(f"{label} • {answered}/{len(session.get('questions', []))} answered")
        action_cols = st.columns(2)
        with action_cols[0]:
            if st.button("Resume", key=f"resume_{session['session_id']}", use_container_width=True):
                st.session_state[mode_to_key[session["mode"]]] = session
        with action_cols[1]:
            if st.button("Discard", key=f"discard_{session['session_id']}", use_container_width=True):
                delete_active_session(session["session_id"])
                active_payload = st.session_state.get(mode_to_key[session["mode"]])
                if active_payload and active_payload.get("session_id") == session["session_id"]:
                    st.session_state[mode_to_key[session["mode"]]] = None
                st.rerun()


# ---------------------------------------------------------------------------
# Bootstrap
# ---------------------------------------------------------------------------

_initialize_state()
_load_saved_sessions()
profile = load_user_profile()
profile = _require_passcode(profile)

if not profile.get("onboarding_complete"):
    _render_onboarding(profile)

profile = _refresh_profile()

st.title("NetSecure StudyOS")
st.caption("A local-first study system for networking, cloud, and security certification prep.")
_render_storage_notice()

with st.sidebar:
    st.header("Session Setup")
    exam_options = list(EXAM_DOMAINS.keys())
    default_exam = profile.get("target_exam") if profile.get("target_exam") in EXAM_DOMAINS else exam_options[0]
    selected_exam = st.selectbox("Select exam", exam_options, index=exam_options.index(default_exam))
    selected_mode = st.selectbox("Select mode", ["Practice", "Exam Simulator"])
    selected_count = st.selectbox("Select question count", [10, 25, 50, 90, 100], index=1)
    timed_mode = st.toggle("Timed mode", value=False)
    default_minutes = default_minutes_for_exam(selected_count)
    minutes = st.number_input(
        "Minutes",
        min_value=5,
        max_value=240,
        value=default_minutes,
        step=5,
        disabled=not timed_mode,
    )
    st.divider()
    st.subheader("Target Plan")
    st.write(f"Exam: {profile.get('target_exam') or '-'}")
    st.write(f"Date: {profile.get('target_date') or '-'}")
    st.write(f"Weekly hours: {profile.get('weekly_study_hours', 0)}")
    st.divider()
    st.subheader("Exam Readiness")
    readiness_value = profile.get("exam_readiness", {}).get(selected_exam, 36.0)
    st.progress(min(int(readiness_value), 100))
    st.write(f"{readiness_value:.1f}/100")
    st.caption("Practice mode is better for weak-topic cleanup. Simulator mode is better for pacing, fatigue, and score validation.")
    st.divider()
    _render_profile_editor(profile)
    st.divider()
    _render_share_settings(profile)
    st.divider()
    _render_saved_sessions_sidebar()
    if st.button("Lock App", use_container_width=True):
        st.session_state["authenticated"] = False
        st.rerun()

# ---------------------------------------------------------------------------
# Shared data used by all tabs
# ---------------------------------------------------------------------------

all_results = load_results()
exam_results = load_results(selected_exam)
current_readiness = calculate_readiness(selected_exam, exam_results, profile)
current_latest_score = exam_results[-1]["score_pct"] if exam_results else 0.0
prediction = predict_exam_score(selected_exam, exam_results, profile)
recommended = recommended_next_topic(selected_exam, exam_results, profile)
domain_conf_df = confidence_by_domain(selected_exam, exam_results)
queue_df = review_queue(selected_exam, exam_results)
history_df = topic_history_frame(selected_exam, exam_results)
study_hours = int(profile.get("weekly_study_hours", 8) or 8)

render_brand_ribbon(
    [
        (f"Target: {profile.get('target_exam') or selected_exam}", False),
        (f"Weekly Hours: {study_hours}", False),
        (f"{len(EXAM_DOMAINS)} Certifications", True),
        ("Local-First Analytics", True),
    ]
)
render_hero_panel(selected_exam, selected_mode, current_readiness, current_latest_score, len(exam_results))
render_showcase_strip(
    [
        {
            "label": "Current Momentum",
            "value": f"{current_latest_score:.1f}%",
            "detail": "Latest scored performance snapshot",
        },
        {
            "label": "Next Best Move",
            "value": recommended["topic"],
            "detail": recommended["domain"],
        },
        {
            "label": "Forecast Window",
            "value": f"{prediction['range_low']:.0f}-{prediction['range_high']:.0f}%",
            "detail": prediction["confidence_note"],
        },
    ]
)

# ---------------------------------------------------------------------------
# Shared context passed to every page
# ---------------------------------------------------------------------------

ctx = {
    "profile": profile,
    "selected_exam": selected_exam,
    "selected_mode": selected_mode,
    "selected_count": selected_count,
    "timed_mode": timed_mode,
    "minutes": minutes,
    "all_results": all_results,
    "exam_results": exam_results,
    "current_readiness": current_readiness,
    "current_latest_score": current_latest_score,
    "prediction": prediction,
    "recommended": recommended,
    "domain_conf_df": domain_conf_df,
    "queue_df": queue_df,
    "history_df": history_df,
    "study_hours": study_hours,
}

# ---------------------------------------------------------------------------
# Tab routing
# ---------------------------------------------------------------------------

tabs = st.tabs(
    [
        "Dashboard",
        "Quiz Generator",
        "Exam Simulator",
        "Weak Topics",
        "Study Plan",
        "Cheat Sheets",
        "Predicted Score",
        "Review Queue",
        "Home Labs",
    ]
)
dashboard_tab, quiz_tab, simulator_tab, weak_tab, plan_tab, cheat_tab, prediction_tab, review_tab, labs_tab = tabs

with dashboard_tab:
    page_dashboard.render(ctx)

with quiz_tab:
    page_quiz.render(ctx)

with simulator_tab:
    page_simulator.render(ctx)

with weak_tab:
    page_weak_topics.render(ctx)

with plan_tab:
    page_study_plan.render(ctx)

with cheat_tab:
    page_cheat_sheets.render(ctx)

with prediction_tab:
    page_prediction.render(ctx)

with review_tab:
    page_review_queue.render(ctx)

with labs_tab:
    page_labs.render(ctx)
