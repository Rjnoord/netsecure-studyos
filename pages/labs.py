from __future__ import annotations

from datetime import datetime

import streamlit as st

from labs import get_home_labs, lab_note_feedback
from storage import load_user_profile, save_user_profile
from utils import render_section_note, render_topic_card


def _save_lab_progress(
    profile: dict,
    exam: str,
    lab_id: str,
    completed_steps: list[int],
    total_steps: int,
    completion_note: str,
) -> dict:
    cleaned_note = completion_note.strip()[:2500]
    note_issues = lab_note_feedback(cleaned_note)
    is_complete = len(completed_steps) == total_steps and not note_issues
    profile.setdefault("lab_progress", {})
    profile["lab_progress"].setdefault(exam, {})
    profile["lab_progress"][exam][lab_id] = {
        "completed_steps": completed_steps,
        "completed": is_complete,
        "completion_note": cleaned_note,
        "note_requirements_met": not note_issues,
        "completed_at": datetime.now().isoformat() if is_complete else None,
    }
    save_user_profile(profile)
    return load_user_profile()


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
    for index, lab in enumerate(labs, start=1):
        progress = profile.get("lab_progress", {}).get(selected_exam, {}).get(lab["id"], {})
        completed_steps = progress.get("completed_steps", [])
        completion_note = progress.get("completion_note", "")
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
                profile = _save_lab_progress(
                    profile,
                    selected_exam,
                    lab["id"],
                    updated_steps,
                    len(lab["steps"]),
                    note_value,
                )
                current_issues = lab_note_feedback(note_value)
                if len(updated_steps) == len(lab["steps"]) and not current_issues:
                    st.success("Lab marked complete. Resume bullets are now unlocked.")
                elif len(updated_steps) == len(lab["steps"]):
                    st.warning("All steps are complete, but the reflection/evidence note still does not meet the unlock rubric.")
                else:
                    st.success("Lab progress saved. Complete every step and add a reflection/evidence note to unlock the resume bullets.")
                st.rerun()
        with action_cols[1]:
            st.progress(len(updated_steps) / max(1, len(lab["steps"])), text=f"{len(updated_steps)}/{len(lab['steps'])} steps complete")

        current_note_issues = lab_note_feedback(note_value)
        if current_note_issues:
            st.caption("Unlock rubric:")
            for issue in current_note_issues:
                st.write(f"- {issue}")
        else:
            st.caption("Reflection/evidence note requirement met.")

        st.markdown("### Resume Bullets")
        if is_complete:
            st.markdown("### Completion Reflection")
            st.write(completion_note)
            for bullet in lab["resume_bullets"]:
                st.write(f"- {bullet}")
        else:
            st.info("Complete and save every step in this lab and satisfy the Built / Verified / Evidence reflection rubric to unlock the resume bullets.")
