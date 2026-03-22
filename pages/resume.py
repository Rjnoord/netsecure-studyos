from __future__ import annotations

from datetime import datetime

import streamlit as st

from labs import HOME_LABS, get_home_labs
from linkedin import TRIGGER_LABELS, generate_linkedin_post, get_next_peak_time
from storage import (
    add_xp,
    award_badge,
    export_markdown,
    get_badges,
    get_linkedin_post_for_milestone,
    get_linkedin_total_copies,
    load_linkedin_posts,
    load_resume,
    record_linkedin_copy,
    save_linkedin_post,
    save_resume,
)
from gates import require_feature
from utils import render_section_note


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_JOB_TITLES = [
    "Network Engineer",
    "Security Analyst",
    "Cloud Engineer",
    "SOC Analyst",
    "IT Administrator",
    "DevOps Engineer",
    "Other",
]

_YEARS_OPTIONS = ["0-1", "1-3", "3-5", "5+"]


# ---------------------------------------------------------------------------
# Data helpers
# ---------------------------------------------------------------------------

def _get_lab_def(exam: str, lab_id: str) -> dict | None:
    for lab in HOME_LABS.get(exam, []):
        if lab["id"] == lab_id:
            return lab
    return None


def _collect_completed_labs(profile: dict) -> list[dict]:
    completed = []
    for exam, labs in profile.get("lab_progress", {}).items():
        for lab_id, lab_data in labs.items():
            if not lab_data.get("completed"):
                continue
            lab_def = _get_lab_def(exam, lab_id)
            ai_grade = lab_data.get("ai_grade") or {}
            ai_bullets = ai_grade.get("personalized_bullets") or []
            static_bullets = lab_def.get("resume_bullets", []) if lab_def else []
            bullets = ai_bullets if ai_bullets else static_bullets
            completed.append(
                {
                    "exam": exam,
                    "lab_id": lab_id,
                    "title": lab_def["title"] if lab_def else lab_id,
                    "why": lab_def.get("why", "") if lab_def else "",
                    "bullets": bullets,
                    "completion_note": lab_data.get("completion_note", ""),
                    "completed_at": lab_data.get("completed_at", ""),
                    "ai_score": ai_grade.get("score"),
                }
            )
    completed.sort(key=lambda x: x.get("completed_at") or "", reverse=True)
    return completed


def _collect_qualifying_certs(profile: dict, threshold: float = 40.0) -> dict[str, float]:
    readiness = profile.get("exam_readiness", {})
    qualifying = {cert: score for cert, score in readiness.items() if score > threshold}
    return dict(sorted(qualifying.items(), key=lambda x: x[1], reverse=True))


def _count_completed_labs(profile: dict) -> int:
    total = 0
    for labs in profile.get("lab_progress", {}).values():
        total += sum(1 for lab in labs.values() if lab.get("completed"))
    return total


# ---------------------------------------------------------------------------
# Resume generation (Claude API, streaming)
# ---------------------------------------------------------------------------

def _generate_resume(
    user_name: str,
    job_title: str,
    years_experience: str,
    current_job: str,
    current_company: str,
    linkedin_url: str,
    city_state: str,
    completed_labs: list[dict],
    qualifying_certs: dict[str, float],
    profile: dict,
) -> str | None:
    try:
        import anthropic

        client = anthropic.Anthropic()

        if completed_labs:
            labs_lines = []
            for lab in completed_labs:
                labs_lines.append(f"Lab: {lab['title']} (Exam: {lab['exam']})")
                if lab.get("ai_score"):
                    labs_lines.append(f"  AI grade: {lab['ai_score']}/10")
                for bullet in lab["bullets"]:
                    labs_lines.append(f"  - {bullet}")
                if lab.get("completion_note"):
                    note_preview = lab["completion_note"][:300].replace("\n", " ")
                    labs_lines.append(f"  Student note excerpt: {note_preview}")
                labs_lines.append("")
            labs_text = "\n".join(labs_lines)
        else:
            labs_text = "No completed labs yet."

        if qualifying_certs:
            certs_lines = [
                f"- {cert}: {score:.0f}% readiness"
                for cert, score in qualifying_certs.items()
            ]
            certs_text = "\n".join(certs_lines)
        else:
            certs_text = "No certifications tracked yet."

        domain_ratings = profile.get("domain_self_ratings", {})
        all_domains: set[str] = set()
        for exam_domains in domain_ratings.values():
            all_domains.update(exam_domains.keys())
        domains_text = ", ".join(sorted(all_domains)) if all_domains else "Networking, Security, Cloud"

        linkedin_line = f"LinkedIn: {linkedin_url}" if linkedin_url.strip() else ""
        current_role_line = (
            f"{current_job} at {current_company}"
            if current_job.strip() and current_company.strip()
            else (current_job.strip() or current_company.strip() or "N/A")
        )

        prompt = f"""Generate a complete, ATS-optimized resume in Markdown format for the following candidate.

CANDIDATE INFORMATION:
- Name: {user_name}
- Target Job Title: {job_title}
- Years of Experience: {years_experience} years
- Current/Previous Role: {current_role_line}
- Location: {city_state}
{linkedin_line}

COMPLETED HANDS-ON LABS (use these as Project Experience):
{labs_text}

CERTIFICATIONS IN PROGRESS (readiness scores from practice system):
{certs_text}

TECHNICAL DOMAINS STUDIED:
{domains_text}

INSTRUCTIONS:
Generate the resume with EXACTLY these sections in this order:

1. **Header** — Candidate name (as H1), then location and LinkedIn URL on separate lines
2. **Professional Summary** — Exactly 3 compelling sentences tailored to the {job_title} role and the candidate's cert/lab background. Make it specific, not generic.
3. **Technical Skills** — Organized into 3–5 logical categories (e.g. Networking, Security, Cloud, Tools, Protocols). Pull skills from the domains studied and certs in progress.
4. **Certifications In Progress** — Table or bullet list showing cert name and readiness percentage. Only include certs provided above.
5. **Project Experience** — Each completed lab becomes a project entry. Format: Project title as H3, a one-line context sentence, then 2–3 impact-focused bullet points using the resume bullets provided. Use strong action verbs. Frame lab work as real professional project experience.
6. **Education** — A placeholder section with: Degree: [Your Degree], Institution: [Institution Name], Graduation: [Year]. Add a note to fill in actual details.

REQUIREMENTS:
- Output ONLY the Markdown resume — no preamble, no commentary, no code fences
- Use ATS-friendly formatting (no tables for skills, no graphics references)
- Every bullet point must start with a strong action verb
- Quantify impact wherever the lab bullets or notes provide specific details
- The tone should be confident and professional
"""

        result_text = ""
        with client.messages.stream(
            model="claude-sonnet-4-6",
            max_tokens=4000,
            system=(
                "You are an expert technical resume writer specializing in IT, networking, "
                "cloud, and cybersecurity roles. Generate professional ATS-optimized resumes "
                "in clean Markdown. Output only the resume — no commentary, no code fences."
            ),
            messages=[{"role": "user", "content": prompt}],
        ) as stream:
            preview_placeholder = st.empty()
            for text in stream.text_stream:
                result_text += text
                preview_placeholder.markdown(result_text + "\n\n*Generating...*")
            preview_placeholder.empty()

        return result_text.strip()

    except Exception as exc:
        st.error(
            f"Resume generation failed: {exc}. "
            "Make sure ANTHROPIC_API_KEY is set in your environment."
        )
        return None


# ---------------------------------------------------------------------------
# LinkedIn helpers
# ---------------------------------------------------------------------------

def _render_linkedin_copy_controls(post_id: int | None, session_key: str) -> None:
    """Shared copy-button + XP logic for a LinkedIn post."""
    copy_xp_key = f"li_copy_xp_{session_key}"
    col_btn, col_prog = st.columns([2, 1])
    with col_btn:
        if not st.session_state.get(copy_xp_key):
            if st.button(
                "✅ Mark as Copied (+50 XP)",
                key=f"li_copy_btn_{session_key}",
                use_container_width=True,
                type="primary",
            ):
                if post_id is not None:
                    total_copies = record_linkedin_copy(post_id)
                else:
                    total_copies = get_linkedin_total_copies()
                add_xp(50, "LinkedIn post copied")
                st.session_state[copy_xp_key] = True
                st.success("+ 50 XP! Go paste it on LinkedIn 🚀")
                if total_copies >= 10:
                    if award_badge(
                        "linkedin_legend",
                        "LinkedIn Legend",
                        "Shared 10 posts about your learning journey on LinkedIn",
                    ):
                        st.success("🏅 Badge unlocked: **LinkedIn Legend**")
                st.rerun()
        else:
            st.success("Copied! Go post it 🚀")
    with col_prog:
        total = get_linkedin_total_copies()
        st.caption(f"LinkedIn Legend: {min(total, 10)}/10 posts")


def _render_linkedin_announce(
    profile: dict,
    completed_labs: list[dict],
    qualifying_certs: dict[str, float],
    saved_inputs: dict,
) -> None:
    """📣 Announce Your Progress — LinkedIn post for resume generation trigger."""
    milestone_key = "resume_first_gen"
    saved_post = get_linkedin_post_for_milestone(milestone_key)

    if saved_post is None:
        user_data = {
            "user_name": saved_inputs.get("user_name") or profile.get("name", "I"),
            "cert": profile.get("target_exam", "my certification"),
            "labs_count": len(completed_labs),
            "certs_count": len(qualifying_certs),
            "job_title": saved_inputs.get("job_title", "a tech role"),
        }
        with st.spinner("Drafting your LinkedIn announcement..."):
            post_text = generate_linkedin_post("resume_generated", user_data)
        if post_text:
            post_id = save_linkedin_post("resume_generated", milestone_key, post_text, user_data)
            saved_post = {
                "id": post_id,
                "post_text": post_text,
                "trigger": "resume_generated",
                "generated_at": datetime.now().isoformat(),
                "copy_count": 0,
            }

    if not saved_post:
        return

    post_id = saved_post.get("id")

    st.divider()
    st.markdown("### 📣 Announce Your Progress on LinkedIn")

    peak = get_next_peak_time()
    if peak["is_now"]:
        st.success(f"🕐 **Best time to post: Right now!** ({peak['day']} {peak['time_range']})")
    else:
        st.info(
            f"🕐 **Best time to post:** {peak['label']} · {peak['day']} {peak['time_range']} "
            f"({peak['date']})"
        )

    edited = st.text_area(
        "LinkedIn Post (edit before copying)",
        value=saved_post["post_text"],
        height=260,
        key="li_resume_post",
        help="Customize before sharing. Changes here are not persisted.",
    )

    _render_linkedin_copy_controls(post_id, "resume_gen")

    with st.expander("Copy raw post text", expanded=False):
        st.code(edited, language=None)


# ---------------------------------------------------------------------------
# Main render
# ---------------------------------------------------------------------------

def render(ctx: dict) -> None:
    profile = ctx["profile"]

    st.subheader("Resume Builder")
    render_section_note(
        "Build an ATS-optimized resume from your completed labs and cert progress. "
        "AI-personalized bullets from graded labs are used automatically; "
        "static fallback bullets are used for ungraded labs."
    )

    if not require_feature("resume_builder"):
        return

    # ── Detect new labs completed since last generation ───────────────────
    current_lab_count = _count_completed_labs(profile)
    last_gen_lab_count = st.session_state.get("resume_last_lab_count")
    if last_gen_lab_count is not None and current_lab_count > last_gen_lab_count:
        st.info(
            f"You completed {current_lab_count - last_gen_lab_count} new lab(s) since "
            "the last resume was generated. Regenerate to include them."
        )

    # ── Pull source data ──────────────────────────────────────────────────
    completed_labs = _collect_completed_labs(profile)
    qualifying_certs = _collect_qualifying_certs(profile)

    # ── Source data summary ───────────────────────────────────────────────
    col_a, col_b = st.columns(2)
    with col_a:
        st.metric("Completed Labs", len(completed_labs), help="Labs with all steps done and note rubric met")
    with col_b:
        st.metric(
            "Qualifying Certs",
            len(qualifying_certs),
            help="Certifications with readiness above 40%",
        )

    if completed_labs:
        with st.expander(f"Labs included ({len(completed_labs)})", expanded=False):
            for lab in completed_labs:
                bullet_source = "AI-personalized" if lab.get("ai_score") else "Static"
                st.write(f"**{lab['title']}** ({lab['exam']}) — {bullet_source} bullets")
    else:
        st.warning(
            "No completed labs found. Complete at least one lab in the Home Labs tab "
            "to unlock Project Experience bullets."
        )

    st.divider()

    # ── User input form ───────────────────────────────────────────────────
    st.markdown("### Your Information")

    saved = load_resume()
    saved_inputs = saved.get("user_inputs", {}) if saved else {}

    with st.form("resume_inputs_form", clear_on_submit=False):
        col1, col2 = st.columns(2)
        with col1:
            user_name = st.text_input(
                "Full Name",
                value=saved_inputs.get("user_name") or profile.get("name", ""),
                placeholder="Jane Smith",
            )
            job_title = st.selectbox(
                "Target Job Title",
                _JOB_TITLES,
                index=_JOB_TITLES.index(saved_inputs.get("job_title", _JOB_TITLES[0]))
                if saved_inputs.get("job_title") in _JOB_TITLES
                else 0,
            )
            years_experience = st.selectbox(
                "Years of Experience",
                _YEARS_OPTIONS,
                index=_YEARS_OPTIONS.index(saved_inputs.get("years_experience", _YEARS_OPTIONS[0]))
                if saved_inputs.get("years_experience") in _YEARS_OPTIONS
                else 0,
            )
        with col2:
            current_job = st.text_input(
                "Current or Previous Job Title",
                value=saved_inputs.get("current_job", ""),
                placeholder="Help Desk Technician",
            )
            current_company = st.text_input(
                "Company",
                value=saved_inputs.get("current_company", ""),
                placeholder="Acme Corp",
            )
            city_state = st.text_input(
                "City, State",
                value=saved_inputs.get("city_state", ""),
                placeholder="Austin, TX",
            )

        linkedin_url = st.text_input(
            "LinkedIn URL (optional)",
            value=saved_inputs.get("linkedin_url", ""),
            placeholder="linkedin.com/in/yourprofile",
        )

        generate_btn = st.form_submit_button(
            "Generate Resume",
            type="primary",
            use_container_width=True,
        )

    # ── Handle generation ─────────────────────────────────────────────────
    if generate_btn:
        if not user_name.strip():
            st.error("Enter your full name before generating.")
        else:
            user_inputs = {
                "user_name": user_name,
                "job_title": job_title,
                "years_experience": years_experience,
                "current_job": current_job,
                "current_company": current_company,
                "linkedin_url": linkedin_url,
                "city_state": city_state,
            }

            with st.spinner("Generating your resume with Claude AI..."):
                resume_md = _generate_resume(
                    user_name=user_name,
                    job_title=job_title,
                    years_experience=years_experience,
                    current_job=current_job,
                    current_company=current_company,
                    linkedin_url=linkedin_url,
                    city_state=city_state,
                    completed_labs=completed_labs,
                    qualifying_certs=qualifying_certs,
                    profile=profile,
                )

            if resume_md:
                save_resume(resume_md, user_inputs)
                st.session_state["resume_md"] = resume_md
                st.session_state["resume_last_lab_count"] = current_lab_count
                st.success("Resume generated successfully!")

                # ── XP and badge rewards ──────────────────────────────────
                existing_badge_ids = {b["badge_id"] for b in get_badges()}

                if "resume_first_gen" not in existing_badge_ids:
                    if award_badge(
                        "resume_first_gen",
                        "Resume Ready",
                        "Generated your first AI-powered resume",
                    ):
                        add_xp(200, "First resume generated")
                        st.success("🏅 Badge unlocked: **Resume Ready** (+200 XP)")

                if "resume_ready" not in existing_badge_ids:
                    if award_badge(
                        "resume_ready",
                        "Resume Ready",
                        "Resume generated from completed lab work",
                    ):
                        st.success("🏅 Badge unlocked: **Resume Ready**")

                st.rerun()

    # ── Display last generated resume ─────────────────────────────────────
    resume_md = st.session_state.get("resume_md")
    if not resume_md and saved:
        resume_md = saved.get("resume_md")
        if resume_md:
            st.session_state["resume_md"] = resume_md

    if resume_md:
        st.divider()

        if saved and saved.get("generated_at"):
            try:
                gen_dt = datetime.fromisoformat(saved["generated_at"])
                st.caption(f"Last generated: {gen_dt.strftime('%B %d, %Y %I:%M %p')}")
            except ValueError:
                pass

        # ── Action buttons ────────────────────────────────────────────────
        btn_col1, btn_col2 = st.columns(2)
        with btn_col1:
            safe_name = (
                saved_inputs.get("user_name")
                or (saved or {}).get("user_inputs", {}).get("user_name", "resume")
            ).replace(" ", "")
            today_str = datetime.now().strftime("%Y-%m-%d")
            filename = f"resume_{safe_name}_{today_str}.md"
            export_markdown(resume_md, filename)
            st.download_button(
                label="Download Resume (.md)",
                data=resume_md,
                file_name=filename,
                mime="text/markdown",
                use_container_width=True,
            )
        with btn_col2:
            st.info("Use the **Copy** button in the raw text panel below to paste into job portals.", icon="📋")

        # ── Live markdown preview ─────────────────────────────────────────
        st.markdown("### Resume Preview")
        st.markdown(
            "<div style='background:white;border:1px solid rgba(16,32,51,0.1);border-radius:16px;"
            "padding:2rem 2.4rem;box-shadow:0 14px 36px rgba(16,32,51,0.06);max-width:800px;margin:auto'>",
            unsafe_allow_html=True,
        )
        st.markdown(resume_md)
        st.markdown("</div>", unsafe_allow_html=True)

        # ── Copy-ready raw text ───────────────────────────────────────────
        with st.expander("Copy Resume Text (for job application portals)", expanded=False):
            st.caption(
                "Click the copy icon in the top-right corner of the code block below "
                "to copy the full resume text."
            )
            st.code(resume_md, language=None)

        # ── LinkedIn announcement section ─────────────────────────────────
        current_saved_inputs = saved_inputs or (saved or {}).get("user_inputs", {})
        if not st.session_state.get("linkedin_suggestions_disabled"):
            _render_linkedin_announce(
                profile=profile,
                completed_labs=completed_labs,
                qualifying_certs=qualifying_certs,
                saved_inputs=current_saved_inputs,
            )

    elif not generate_btn:
        st.info("Fill in your information above and click **Generate Resume** to create your AI-powered resume.")

    # ── LinkedIn Posts history ────────────────────────────────────────────
    all_posts = load_linkedin_posts()
    if all_posts:
        st.divider()
        st.markdown("### 📋 LinkedIn Posts History")
        render_section_note(
            "Every LinkedIn post generated across your labs and resume milestones is saved here. "
            "Copy any post and mark it as copied to earn +50 XP per post."
        )

        total_copies = get_linkedin_total_copies()
        st.caption(f"LinkedIn Legend progress: {min(total_copies, 10)}/10 posts copied")

        for post in all_posts:
            trigger_label = TRIGGER_LABELS.get(post["trigger"], post["trigger"])
            try:
                gen_dt = datetime.fromisoformat(post["generated_at"])
                date_str = gen_dt.strftime("%b %d, %Y %I:%M %p")
            except ValueError:
                date_str = post["generated_at"]

            copy_count = post.get("copy_count", 0)
            copy_label = f"Copied {copy_count}×" if copy_count else "Not copied yet"

            with st.expander(
                f"**{trigger_label}** · {date_str} · {copy_label}",
                expanded=False,
            ):
                session_key = f"hist_{post['id']}"
                copy_xp_key = f"li_copy_xp_{session_key}"

                edited = st.text_area(
                    "Post text (editable)",
                    value=post["post_text"],
                    height=220,
                    key=f"li_hist_text_{post['id']}",
                )

                _render_linkedin_copy_controls(post.get("id"), session_key)

                with st.expander("Copy raw text", expanded=False):
                    st.code(edited, language=None)
