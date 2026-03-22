from __future__ import annotations

import re

import streamlit as st

from storage import add_waitlist_email, add_xp, award_badge, get_waitlist_count
from utils import render_section_note


_EMAIL_RE = re.compile(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$")

_FREE_FEATURES = [
    "3 certs (A+, Network+, Security+)",
    "10 questions / day",
    "1 lab per cert",
    "Basic analytics & readiness score",
    "Cheat Sheets",
    "Study Plan",
    "Spaced Repetition Queue",
]

_PRO_FEATURES = [
    "All 50+ certs (CompTIA, Cisco, AWS, Azure)",
    "Unlimited questions per day",
    "All labs + AI grader with resume bullets",
    "AI Tutor Mode — step-by-step wrong-answer explanations",
    "Resume Builder — streaming Claude generation",
    "LinkedIn Auto-Poster with peak-time suggestions",
    "Career & Salary Dashboard — live market data",
    "Full Certification Skill Tree",
    "Boss Battle Mode — hiring manager simulation",
    "Debate Mode — Claude-graded written rebuttals",
    "Daily Challenge Leaderboard",
    "Misconception Detector",
    "Power BI / CSV / Markdown exports",
]

_OFFICIAL_LINKS = [
    {
        "vendor": "CompTIA",
        "exams": "A+, Network+, Security+, CySA+, PenTest+, SecurityX, Linux+",
        "url": "https://www.comptia.org/certifications",
    },
    {
        "vendor": "Cisco",
        "exams": "CCNA, CCNP, CCIE, CyberOps, DevNet",
        "url": "https://www.cisco.com/c/en/us/training-events/training-certifications/certifications.html",
    },
    {
        "vendor": "AWS",
        "exams": "Cloud Practitioner, Solutions Architect, Developer, DevOps, Specialties",
        "url": "https://aws.amazon.com/certification/",
    },
    {
        "vendor": "Microsoft Azure",
        "exams": "AZ-900, AZ-104, AZ-305, AZ-500, AZ-400, DP-900",
        "url": "https://learn.microsoft.com/en-us/certifications/",
    },
]


def render(ctx: dict) -> None:
    # ── Hero ──────────────────────────────────────────────────────────────────
    st.markdown(
        "<h1 style='text-align:center;margin-bottom:0'>StudyOS Pro</h1>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<p style='text-align:center;font-size:1.2rem;color:#9ca3af;margin-top:0'>"
        "Coming Soon</p>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<p style='text-align:center;font-size:1.05rem;max-width:640px;margin:0 auto 1.5rem'>"
        "Join the waitlist. Be first to access unlimited certs, AI tutoring, "
        "and the resume builder that gets you hired."
        "</p>",
        unsafe_allow_html=True,
    )

    # ── Pricing preview ───────────────────────────────────────────────────────
    pc1, pc2 = st.columns(2)
    with pc1:
        st.markdown(
            "<div style='text-align:center;padding:1rem;background:#1f2937;"
            "border-radius:12px;border:1px solid #374151'>"
            "<h3 style='margin:0 0 .25rem'>Pro</h3>"
            "<p style='font-size:2rem;font-weight:700;margin:0;color:#f59e0b'>$9.99<span style='font-size:1rem;color:#9ca3af'>/month</span></p>"
            "<p style='color:#6b7280;font-size:.85rem;margin:.5rem 0 0'>Regular price at launch</p>"
            "</div>",
            unsafe_allow_html=True,
        )
    with pc2:
        st.markdown(
            "<div style='text-align:center;padding:1rem;background:#14532d;"
            "border-radius:12px;border:2px solid #22c55e'>"
            "<h3 style='margin:0 0 .25rem;color:#86efac'>Early Adopter</h3>"
            "<p style='font-size:2rem;font-weight:700;margin:0;color:#22c55e'>$6.99<span style='font-size:1rem;color:#86efac'>/month</span></p>"
            "<p style='color:#86efac;font-size:.85rem;margin:.5rem 0 0'>30% off for life — waitlist members only</p>"
            "</div>",
            unsafe_allow_html=True,
        )

    st.markdown("")

    # ── Comparison table ──────────────────────────────────────────────────────
    st.markdown("### Free vs Pro")
    col_free, col_pro = st.columns(2)
    with col_free:
        st.markdown("#### Free — Always Available")
        for f in _FREE_FEATURES:
            st.markdown(f"- {f}")
    with col_pro:
        st.markdown("#### Pro — Everything Unlocked")
        for f in _PRO_FEATURES:
            st.markdown(f"- ✅ {f}")

    st.divider()

    # ── Waitlist form ─────────────────────────────────────────────────────────
    st.markdown("### Join the Waitlist")
    render_section_note(
        "No credit card required. We'll email you the moment Pro launches "
        "with your early-adopter discount locked in."
    )

    count = get_waitlist_count()
    if count > 0:
        st.info(f"**{count} {'person' if count == 1 else 'people'} already on the waitlist** — join them!")

    with st.form("waitlist_form", clear_on_submit=True):
        email = st.text_input(
            "Your email address",
            placeholder="you@example.com",
            label_visibility="collapsed",
        )
        joined = st.form_submit_button(
            "Join Waitlist — Lock In 30% Off For Life",
            type="primary",
            use_container_width=True,
        )

    if joined:
        email = email.strip()
        if not email:
            st.error("Please enter an email address.")
        elif not _EMAIL_RE.match(email):
            st.error("That doesn't look like a valid email address. Please check and try again.")
        else:
            is_new = add_waitlist_email(email)
            if is_new:
                add_xp(50, "Joined Pro waitlist")
                award_badge(
                    "early_adopter",
                    "Early Adopter",
                    "Joined the StudyOS Pro waitlist before launch",
                )
                st.success(
                    "You're on the list! We'll email you when Pro launches "
                    "with your 30% lifetime discount ready to apply."
                )
                st.info("+50 XP earned! Badge unlocked: **Early Adopter**")
                st.balloons()
            else:
                st.info("You're already on the waitlist. We haven't forgotten you!")

    st.divider()

    # ── Affiliate / official exam links ───────────────────────────────────────
    st.markdown("### Ready to Take the Real Exam?")
    render_section_note(
        "These are official vendor links to certification pages. "
        "StudyOS is not affiliated with any of these vendors — "
        "these are provided as a convenience for students ready to register."
    )
    for vendor in _OFFICIAL_LINKS:
        col_v, col_e, col_l = st.columns([1, 2.5, 1])
        col_v.markdown(f"**{vendor['vendor']}**")
        col_e.caption(vendor["exams"])
        col_l.markdown(f"[Official exam page →]({vendor['url']})")
