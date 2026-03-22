from __future__ import annotations

from datetime import datetime

import streamlit as st

from gates import get_labs_per_cert_limit, is_feature_allowed, require_feature
from labs import get_home_labs, grade_lab_with_ai, lab_note_feedback
from linkedin import TRIGGER_LABELS, generate_linkedin_post, get_next_peak_time
from storage import (
    add_xp,
    award_badge,
    get_badges,
    get_linkedin_post_for_milestone,
    get_linkedin_total_copies,
    load_user_profile,
    record_linkedin_copy,
    save_linkedin_post,
    save_user_profile,
)
from utils import render_section_note, render_topic_card


def _save_lab_progress(
    profile: dict,
    exam: str,
    lab_id: str,
    completed_steps: list[int],
    total_steps: int,
    completion_note: str,
    ai_grade: dict | None = None,
) -> dict:
    cleaned_note = completion_note.strip()[:2500]
    note_issues = lab_note_feedback(cleaned_note)
    is_complete = len(completed_steps) == total_steps and not note_issues
    profile.setdefault("lab_progress", {})
    profile["lab_progress"].setdefault(exam, {})
    existing = profile["lab_progress"][exam].get(lab_id, {})
    # Preserve existing AI grade when no new one is provided
    grade_to_save = ai_grade if ai_grade is not None else existing.get("ai_grade")
    grade_ts = (
        datetime.now().isoformat()
        if ai_grade is not None
        else existing.get("ai_graded_at")
    )
    profile["lab_progress"][exam][lab_id] = {
        "completed_steps": completed_steps,
        "completed": is_complete,
        "completion_note": cleaned_note,
        "note_requirements_met": not note_issues,
        "completed_at": datetime.now().isoformat() if is_complete else None,
        "ai_grade": grade_to_save,
        "ai_graded_at": grade_ts,
    }
    save_user_profile(profile)
    return load_user_profile()


def _score_bar(score: int) -> None:
    """Render a colored progress bar for the AI grade score."""
    pct = int(score * 10)
    if score >= 8:
        color = "#22c55e"
        label = f"🟢 Score: {score}/10 — Excellent"
    elif score >= 6:
        color = "#f59e0b"
        label = f"🟡 Score: {score}/10 — Good"
    else:
        color = "#ef4444"
        label = f"🔴 Score: {score}/10 — Needs Improvement"
    st.markdown(
        f'<div style="background:#374151;border-radius:8px;height:18px;margin:6px 0 2px">'
        f'<div style="background:{color};width:{pct}%;height:18px;border-radius:8px;'
        f'transition:width 0.4s ease"></div></div>',
        unsafe_allow_html=True,
    )
    st.markdown(f"**{label}**")


def _render_ai_grade(grade: dict) -> None:
    """Display the full AI grade panel."""
    st.markdown("### AI Lab Grade")
    score = int(grade.get("score", 0))
    _score_bar(score)

    strengths = grade.get("strengths", [])
    improvements = grade.get("improvements", [])

    col_l, col_r = st.columns(2)
    with col_l:
        if strengths:
            st.markdown("**Strengths**")
            for item in strengths:
                st.markdown(f"✅ {item}")
    with col_r:
        if improvements:
            st.markdown("**To Improve**")
            for item in improvements:
                st.markdown(f"⚠️ {item}")

    if grade.get("understanding_verified"):
        st.success("🎓 Understanding Verified — This note demonstrates genuine hands-on work.")

    bullets = grade.get("personalized_bullets", [])
    if bullets:
        st.markdown("**AI-Personalized Resume Bullets** *(copy-paste ready)*")
        st.code("\n".join(f"• {b}" for b in bullets), language=None)


def _render_linkedin_section(
    lab: dict,
    existing_grade: dict,
    selected_exam: str,
    profile: dict,
) -> None:
    """Render the 📣 Share Your Win LinkedIn section after a graded lab."""
    if not is_feature_allowed("linkedin_poster"):
        return  # silently hidden for free tier
    score = int(existing_grade.get("score", 0))
    if score < 7:
        return

    # Respect opt-out preference
    if st.session_state.get("linkedin_suggestions_disabled"):
        return

    milestone_key = f"lab_{lab['id']}"

    # Auto-generate post once and cache in SQLite
    saved_post = get_linkedin_post_for_milestone(milestone_key)
    if saved_post is None:
        ai_bullets = existing_grade.get("personalized_bullets") or lab.get("resume_bullets", [])
        user_data = {
            "user_name": profile.get("name", "I"),
            "cert": selected_exam,
            "lab_title": lab["title"],
            "grade_score": score,
            "bullets": ai_bullets[:2],
        }
        with st.spinner("Drafting your LinkedIn post..."):
            post_text = generate_linkedin_post("lab_completed", user_data)
        if post_text:
            post_id = save_linkedin_post("lab_completed", milestone_key, post_text, user_data)
            saved_post = {
                "id": post_id,
                "post_text": post_text,
                "trigger": "lab_completed",
                "generated_at": datetime.now().isoformat(),
                "copy_count": 0,
            }

    if not saved_post:
        return

    post_id = saved_post.get("id")

    st.markdown("---")
    st.markdown("### 📣 Share Your Win")

    # Peak time info
    peak = get_next_peak_time()
    if peak["is_now"]:
        st.success(f"🕐 **Best time to post: Right now!** ({peak['day']} {peak['time_range']})")
    else:
        st.info(
            f"🕐 **Best time to post:** {peak['label']} · {peak['day']} {peak['time_range']} "
            f"({peak['date']})"
        )

    # Editable post text
    edited_post = st.text_area(
        "LinkedIn Post (edit before copying)",
        value=saved_post["post_text"],
        height=260,
        key=f"li_post_{lab['id']}",
        help="Customize this post before sharing. Changes here are not saved.",
    )

    copy_col, opt_col = st.columns([2, 1])
    with copy_col:
        copy_xp_key = f"li_copy_xp_{lab['id']}"
        if not st.session_state.get(copy_xp_key):
            if st.button(
                "✅ Mark as Copied (+50 XP)",
                key=f"li_copy_btn_{lab['id']}",
                use_container_width=True,
                type="primary",
            ):
                if post_id is not None:
                    total_copies = record_linkedin_copy(post_id)
                else:
                    total_copies = get_linkedin_total_copies()
                add_xp(50, "LinkedIn post copied")
                st.session_state[copy_xp_key] = True
                st.success("+ 50 XP! Open LinkedIn, paste, and post 🚀")
                if total_copies >= 10:
                    if award_badge(
                        "linkedin_legend",
                        "LinkedIn Legend",
                        "Shared 10 posts about your learning journey on LinkedIn",
                    ):
                        st.success("🏅 Badge unlocked: **LinkedIn Legend**")
                st.rerun()
        else:
            st.success("Copied! Go post on LinkedIn 🚀")
            copy_count = saved_post.get("copy_count", 0) + (
                1 if st.session_state.get(copy_xp_key) else 0
            )
            total = get_linkedin_total_copies()
            st.caption(f"LinkedIn Legend progress: {min(total, 10)}/10 posts")

    with opt_col:
        if st.checkbox(
            "Don't show LinkedIn suggestions",
            key="linkedin_suggestions_disabled",
            value=st.session_state.get("linkedin_suggestions_disabled", False),
        ):
            st.rerun()

    # Raw text for manual copy-paste
    with st.expander("Copy raw post text", expanded=False):
        st.code(edited_post, language=None)


def render(ctx: dict) -> None:
    selected_exam = ctx["selected_exam"]
    profile = ctx["profile"]

    st.subheader("Hands-On Home Labs")
    render_section_note(
        "Use these guided labs to turn certification concepts into practical experience. Resume bullets stay locked until every step in a lab is marked complete and saved."
    )
    labs = get_home_labs(selected_exam)
    if not labs:
        st.info("No home labs are defined for this exam yet.")

    # Apply labs-per-cert limit for free tier
    lab_limit = get_labs_per_cert_limit()
    if lab_limit is not None and len(labs) > lab_limit:
        st.info(
            f"Free tier: showing {lab_limit} of {len(labs)} labs. "
            "Upgrade to Pro to unlock all labs with AI grading."
        )
        labs = labs[:lab_limit]

    for index, lab in enumerate(labs, start=1):
        progress = profile.get("lab_progress", {}).get(selected_exam, {}).get(lab["id"], {})
        completed_steps = progress.get("completed_steps", [])
        completion_note = progress.get("completion_note", "")
        existing_grade = progress.get("ai_grade")
        is_complete = (
            bool(progress.get("completed"))
            and len(completed_steps) == len(lab["steps"])
            and not lab_note_feedback(completion_note)
        )
        render_topic_card(
            f"Lab {index} • {lab['title']}",
            [f"Why this lab matters: {lab['why']}"],
            pills=[selected_exam, "Hands-on", "Completed" if is_complete else "In progress"],
        )
        st.markdown("### Step-By-Step Directions")
        updated_steps: list[int] = []
        for step_number, step in enumerate(lab["steps"], start=1):
            checked = st.checkbox(
                f"{step_number}. {step}",
                value=step_number in completed_steps,
                key=f"{lab['id']}_step_{step_number}",
            )
            if checked:
                updated_steps.append(step_number)

        action_cols = st.columns(2)
        note_value = st.text_area(
            "Completion Reflection / Evidence Note",
            value=completion_note,
            key=f"{lab['id']}_note",
            help="Use this exact rubric: `Built:`, `Verified:`, and `Evidence:`. The bullets unlock only after all sections are present and the note is substantive.",
            placeholder=(
                "Built: Created the VLAN and routing lab in Packet Tracer.\n"
                "Verified: Tested inter-VLAN routing with ping and show commands.\n"
                "Evidence: Saved screenshots of trunks, ACL denies, and DHCP leases."
            ),
        )
        with action_cols[0]:
            if st.button("Save Lab Progress", key=f"save_lab_{lab['id']}", use_container_width=True):
                was_complete_before = bool(progress.get("completed"))
                current_issues = lab_note_feedback(note_value)
                all_steps_done = len(updated_steps) == len(lab["steps"])
                newly_passing = all_steps_done and not current_issues

                # Call the AI grader when transitioning to complete or when a
                # previous grade attempt failed (existing_grade is None).
                # Gated to Pro tier — free users still save progress without AI grade.
                ai_grade = None
                if newly_passing and (not was_complete_before or existing_grade is None):
                    if is_feature_allowed("ai_lab_grader"):
                        with st.spinner("Grading your lab with AI..."):
                            ai_grade = grade_lab_with_ai(lab, selected_exam, note_value)
                    else:
                        st.info("AI Lab Grading is a Pro feature. Upgrade to get personalized resume bullets and scores.")

                profile = _save_lab_progress(
                    profile,
                    selected_exam,
                    lab["id"],
                    updated_steps,
                    len(lab["steps"]),
                    note_value,
                    ai_grade=ai_grade,
                )

                newly_complete = newly_passing and not was_complete_before
                if newly_complete:
                    st.success("Lab marked complete. Resume bullets are now unlocked.")
                    add_xp(150, "Lab completed")
                    st.info("+ 150 XP earned!")

                    # AI grade XP bonus — only on first completion with a high score
                    if ai_grade and ai_grade.get("badge_earned"):
                        add_xp(100, "AI Lab Grade bonus (score 8+)")
                        st.info("+ 100 XP bonus — AI grade 8 or higher!")

                    existing_badge_ids = {b["badge_id"] for b in get_badges()}
                    if "lab_rat" not in existing_badge_ids:
                        if award_badge("lab_rat", "Lab Rat", "Completed your first lab"):
                            st.success("🏅 Badge unlocked: **Lab Rat**")

                    total_complete = sum(
                        1
                        for ex_labs in profile.get("lab_progress", {}).values()
                        for lab_data in ex_labs.values()
                        if lab_data.get("completed")
                    )
                    if total_complete >= 10:
                        if award_badge("lab_master", "Lab Master", "Completed 10 labs"):
                            st.success("🏅 Badge unlocked: **Lab Master**")

                    # Resume Ready: 5 labs with note requirements met
                    passing_labs = sum(
                        1
                        for ex_labs in profile.get("lab_progress", {}).values()
                        for lab_data in ex_labs.values()
                        if lab_data.get("completed") and lab_data.get("note_requirements_met")
                    )
                    if passing_labs >= 5:
                        if award_badge(
                            "resume_ready",
                            "Resume Ready",
                            "Completed 5 labs with a quality reflection note",
                        ):
                            st.success("🏅 Badge unlocked: **Resume Ready**")

                elif newly_passing and was_complete_before and existing_grade is None and ai_grade:
                    # Re-submitted a complete lab and got a fresh grade
                    if ai_grade.get("badge_earned"):
                        st.info("+ 100 XP bonus — AI grade 8 or higher!")
                        add_xp(100, "AI Lab Grade bonus (score 8+) on re-grade")
                elif all_steps_done:
                    st.warning(
                        "All steps are complete, but the reflection/evidence note still does not meet the unlock rubric."
                    )
                else:
                    st.success(
                        "Lab progress saved. Complete every step and add a reflection/evidence note to unlock the resume bullets."
                    )
                st.rerun()

        with action_cols[1]:
            st.progress(
                len(updated_steps) / max(1, len(lab["steps"])),
                text=f"{len(updated_steps)}/{len(lab['steps'])} steps complete",
            )

        current_note_issues = lab_note_feedback(note_value)
        if current_note_issues:
            st.caption("Unlock rubric:")
            for issue in current_note_issues:
                st.write(f"- {issue}")
        else:
            st.caption("Reflection/evidence note requirement met.")

        # AI grade panel — shown for complete labs that have a stored grade
        if is_complete and existing_grade:
            _render_ai_grade(existing_grade)
            # LinkedIn "Share Your Win" section for grades 7+
            _render_linkedin_section(lab, existing_grade, selected_exam, profile)

        st.markdown("### Resume Bullets")
        if is_complete:
            st.markdown("### Completion Reflection")
            st.write(completion_note)
            # Use AI-personalized bullets when available; fall back to static bullets
            ai_bullets = existing_grade.get("personalized_bullets") if existing_grade else None
            if ai_bullets:
                st.caption("AI-personalized bullets are shown in the grade panel above.")
            else:
                for bullet in lab["resume_bullets"]:
                    st.write(f"- {bullet}")
        else:
            st.info(
                "Complete and save every step in this lab and satisfy the Built / Verified / Evidence reflection rubric to unlock the resume bullets."
            )
