from __future__ import annotations

import re
from collections import defaultdict

import plotly.graph_objects as go
import streamlit as st

from exams import EXAM_DOMAINS
from gates import require_feature
from storage import add_xp, award_badge
from utils import render_section_note


# ---------------------------------------------------------------------------
# Salary data — 2025 market rates, all 69 tracked exams
# ---------------------------------------------------------------------------
# Each entry: low/high salary, experience level, avg bump from adding this cert.
# bump = typical annual salary increase a hiring manager attributes to this cert.

SALARY_DATA: dict[str, dict] = {
    # ── Entry Level (0–2 yrs) ─────────────────────────────────────────────
    "Tech+":                                      {"low":  38_000, "high":  48_000, "level": "Entry",  "bump":  5_000},
    "CCST IT Support":                            {"low":  38_000, "high":  48_000, "level": "Entry",  "bump":  4_000},
    "CCST Networking":                            {"low":  42_000, "high":  52_000, "level": "Entry",  "bump":  5_000},
    "CCST Cybersecurity":                         {"low":  45_000, "high":  55_000, "level": "Entry",  "bump":  7_000},
    "CCT Field Technician":                       {"low":  42_000, "high":  52_000, "level": "Entry",  "bump":  5_000},
    "A+":                                         {"low":  45_000, "high":  55_000, "level": "Entry",  "bump":  8_000},
    "Server+":                                    {"low":  55_000, "high":  68_000, "level": "Entry",  "bump": 10_000},
    "Project+":                                   {"low":  58_000, "high":  72_000, "level": "Entry",  "bump": 10_000},
    "Cloud Essentials+":                          {"low":  58_000, "high":  72_000, "level": "Entry",  "bump": 10_000},
    "Linux+":                                     {"low":  58_000, "high":  72_000, "level": "Entry",  "bump": 12_000},
    "Network+":                                   {"low":  52_000, "high":  65_000, "level": "Entry",  "bump": 12_000},
    "Cloud+":                                     {"low":  60_000, "high":  75_000, "level": "Entry",  "bump": 13_000},
    "AZ-900":                                     {"low":  58_000, "high":  72_000, "level": "Entry",  "bump": 13_000},
    "AI-900":                                     {"low":  65_000, "high":  80_000, "level": "Entry",  "bump": 14_000},
    "DP-900":                                     {"low":  65_000, "high":  80_000, "level": "Entry",  "bump": 14_000},
    "SC-900":                                     {"low":  62_000, "high":  75_000, "level": "Entry",  "bump": 12_000},
    "Data+":                                      {"low":  62_000, "high":  78_000, "level": "Entry",  "bump": 14_000},
    "AWS Cloud Practitioner":                     {"low":  60_000, "high":  75_000, "level": "Entry",  "bump": 15_000},
    "AWS AI Practitioner":                        {"low":  75_000, "high":  95_000, "level": "Entry",  "bump": 18_000},
    "Security+":                                  {"low":  65_000, "high":  80_000, "level": "Entry",  "bump": 18_000},
    "CyberOps Associate":                         {"low":  68_000, "high":  82_000, "level": "Entry",  "bump": 16_000},
    "CCNA":                                       {"low":  70_000, "high":  85_000, "level": "Entry",  "bump": 22_000},
    "CCNA Automation":                            {"low":  75_000, "high":  92_000, "level": "Entry",  "bump": 20_000},
    # ── Mid Level (2–5 yrs) ───────────────────────────────────────────────
    "DataSys+":                                   {"low":  78_000, "high":  95_000, "level": "Mid",    "bump": 20_000},
    "CySA+":                                      {"low":  80_000, "high": 100_000, "level": "Mid",    "bump": 25_000},
    "DataX":                                      {"low":  85_000, "high": 105_000, "level": "Mid",    "bump": 28_000},
    "PenTest+":                                   {"low":  88_000, "high": 110_000, "level": "Mid",    "bump": 30_000},
    "CloudNetX":                                  {"low":  90_000, "high": 112_000, "level": "Mid",    "bump": 30_000},
    "CCNP Collaboration":                         {"low":  90_000, "high": 112_000, "level": "Mid",    "bump": 28_000},
    "Windows Server Hybrid Administrator Associate": {"low": 85_000, "high": 105_000, "level": "Mid",  "bump": 22_000},
    "Azure Virtual Desktop Specialty":            {"low":  90_000, "high": 112_000, "level": "Mid",    "bump": 25_000},
    "CCNP Service Provider":                      {"low":  92_000, "high": 115_000, "level": "Mid",    "bump": 30_000},
    "AZ-104":                                     {"low":  95_000, "high": 115_000, "level": "Mid",    "bump": 32_000},
    "AZ-800":                                     {"low":  95_000, "high": 118_000, "level": "Mid",    "bump": 28_000},
    "CCNP Enterprise":                            {"low":  95_000, "high": 120_000, "level": "Mid",    "bump": 35_000},
    "CCNP Data Center":                           {"low":  95_000, "high": 118_000, "level": "Mid",    "bump": 33_000},
    "SecurityX":                                  {"low":  95_000, "high": 120_000, "level": "Mid",    "bump": 35_000},
    "AWS CloudOps Engineer Associate":            {"low":  98_000, "high": 122_000, "level": "Mid",    "bump": 30_000},
    "CCNP Security":                              {"low":  98_000, "high": 125_000, "level": "Mid",    "bump": 38_000},
    "AZ-204":                                     {"low": 100_000, "high": 125_000, "level": "Mid",    "bump": 35_000},
    "Azure Network Engineer Associate":           {"low":  98_000, "high": 122_000, "level": "Mid",    "bump": 30_000},
    "CCNP Automation":                            {"low": 100_000, "high": 125_000, "level": "Mid",    "bump": 38_000},
    "AWS Developer Associate":                    {"low": 100_000, "high": 125_000, "level": "Mid",    "bump": 32_000},
    "AZ-400":                                     {"low": 105_000, "high": 130_000, "level": "Mid",    "bump": 38_000},
    "AZ-500":                                     {"low": 105_000, "high": 130_000, "level": "Mid",    "bump": 38_000},
    "AZ-700":                                     {"low": 100_000, "high": 125_000, "level": "Mid",    "bump": 32_000},
    "Azure Database Administrator Associate":     {"low": 100_000, "high": 125_000, "level": "Mid",    "bump": 32_000},
    "Azure Security Engineer Associate":          {"low": 108_000, "high": 135_000, "level": "Mid",    "bump": 38_000},
    "AWS Data Engineer Associate":                {"low": 105_000, "high": 130_000, "level": "Mid",    "bump": 35_000},
    "Azure Data Engineer Associate":              {"low": 108_000, "high": 135_000, "level": "Mid",    "bump": 38_000},
    "AWS Solutions Architect Associate":          {"low": 110_000, "high": 135_000, "level": "Mid",    "bump": 40_000},
    "Azure Data Scientist Associate":             {"low": 115_000, "high": 145_000, "level": "Mid",    "bump": 45_000},
    "Azure AI Engineer Associate":                {"low": 115_000, "high": 145_000, "level": "Mid",    "bump": 45_000},
    "AWS Machine Learning Engineer Associate":    {"low": 115_000, "high": 145_000, "level": "Mid",    "bump": 45_000},
    # ── Senior Level (5+ yrs) ─────────────────────────────────────────────
    "AZ-305":                                     {"low": 130_000, "high": 160_000, "level": "Senior", "bump": 50_000},
    "AWS DevOps Engineer Professional":           {"low": 135_000, "high": 168_000, "level": "Senior", "bump": 52_000},
    "AWS Security Specialty":                     {"low": 135_000, "high": 165_000, "level": "Senior", "bump": 50_000},
    "AWS Advanced Networking Specialty":          {"low": 138_000, "high": 168_000, "level": "Senior", "bump": 52_000},
    "AWS Solutions Architect Professional":       {"low": 140_000, "high": 170_000, "level": "Senior", "bump": 55_000},
    "AWS Machine Learning Specialty":             {"low": 140_000, "high": 175_000, "level": "Senior", "bump": 58_000},
    "AWS Generative AI Developer Professional":   {"low": 145_000, "high": 180_000, "level": "Senior", "bump": 58_000},
    "CCIE Enterprise Wireless":                   {"low": 145_000, "high": 175_000, "level": "Senior", "bump": 60_000},
    "CCIE Collaboration":                         {"low": 145_000, "high": 172_000, "level": "Senior", "bump": 58_000},
    "CCIE Data Center":                           {"low": 148_000, "high": 178_000, "level": "Senior", "bump": 62_000},
    "CCIE Service Provider":                      {"low": 148_000, "high": 178_000, "level": "Senior", "bump": 62_000},
    "CCIE Enterprise Infrastructure":             {"low": 150_000, "high": 180_000, "level": "Senior", "bump": 65_000},
    "CCIE Automation":                            {"low": 152_000, "high": 182_000, "level": "Senior", "bump": 65_000},
    "CCIE Security":                              {"low": 155_000, "high": 185_000, "level": "Senior", "bump": 70_000},
    "CCDE":                                       {"low": 155_000, "high": 190_000, "level": "Senior", "bump": 72_000},
}

# ---------------------------------------------------------------------------
# Hardcoded market trends data (2025)
# ---------------------------------------------------------------------------

MARKET_TRENDS = {
    "most_in_demand": [
        {"cert": "AWS Solutions Architect Associate", "postings": "47,000+", "yoy": "+12%"},
        {"cert": "Security+",                         "postings": "39,000+", "yoy": "+8%"},
        {"cert": "CCNA",                              "postings": "33,000+", "yoy": "+5%"},
        {"cert": "AZ-104",                            "postings": "29,000+", "yoy": "+18%"},
        {"cert": "CySA+",                             "postings": "23,000+", "yoy": "+22%"},
        {"cert": "AWS DevOps Engineer Professional",  "postings": "21,000+", "yoy": "+16%"},
        {"cert": "AZ-500",                            "postings": "18,000+", "yoy": "+24%"},
    ],
    "fastest_salary_growth": [
        {"cert": "SecurityX",                         "growth": "+22%", "note": "New CompTIA elite tier, surging demand"},
        {"cert": "AWS Generative AI Developer Professional", "growth": "+28%", "note": "AI/ML roles exploding in 2025"},
        {"cert": "AZ-500",                            "growth": "+24%", "note": "Cloud security shortage driving premium"},
        {"cert": "CySA+",                             "growth": "+22%", "note": "SOC analyst roles outpacing supply"},
        {"cert": "CCNP Automation",                   "growth": "+19%", "note": "NetDevOps replacing manual ops"},
        {"cert": "AWS Security Specialty",            "growth": "+18%", "note": "Cloud-native security roles"},
        {"cert": "CCIE Enterprise Infrastructure",    "growth": "+15%", "note": "CCIE scarcity premium holding strong"},
    ],
    "remote_availability": [
        {"category": "Cloud (AWS / Azure / GCP)", "pct": 85, "note": "Highly remote-friendly"},
        {"category": "Security & SOC",            "pct": 68, "note": "Mix of remote and on-site clearance roles"},
        {"category": "DevOps & Automation",       "pct": 78, "note": "Mostly remote, some hybrid"},
        {"category": "Linux & SRE",               "pct": 72, "note": "Strong remote presence"},
        {"category": "Data & AI/ML",              "pct": 80, "note": "Predominantly remote"},
        {"category": "Networking (CCNA/CCNP)",    "pct": 35, "note": "Mostly on-site / hybrid"},
        {"category": "Field Tech (A+ / CCT)",     "pct": 10, "note": "Hands-on required"},
    ],
    "top_hiring_companies": {
        "Security": ["CrowdStrike", "Palo Alto Networks", "Mandiant", "Deloitte Cyber", "Booz Allen Hamilton"],
        "Cloud AWS": ["Amazon / AWS", "Accenture", "Capgemini", "SAIC", "Leidos"],
        "Cloud Azure": ["Microsoft", "Accenture", "Avanade", "Cognizant", "Leidos"],
        "Networking": ["Cisco", "AT&T", "Comcast", "Rackspace", "Juniper Networks"],
        "DevOps": ["HashiCorp", "Elastic", "Datadog", "Red Hat", "GitLab"],
        "Data / AI": ["Databricks", "Snowflake", "Google", "Microsoft", "Palantir"],
    },
}

_GOAL_OPTIONS = [
    "Maximize salary",
    "Break into cloud",
    "Break into security",
    "Break into networking",
    "Get hired fastest",
    "Advance to senior / architect",
    "Transition to DevOps",
    "Enter AI / ML engineering",
]

_LEVEL_ORDER = {"Entry": 0, "Mid": 1, "Senior": 2}


# ---------------------------------------------------------------------------
# Salary helpers
# ---------------------------------------------------------------------------

def _avg(cert: str) -> float:
    d = SALARY_DATA.get(cert)
    if not d:
        return 0.0
    return (d["low"] + d["high"]) / 2


def _current_value(readiness_map: dict[str, float]) -> tuple[str, int, int]:
    """Return (best_cert_name, low, high) based on certs at readiness >= 40%."""
    best_cert, best_avg = "", 0.0
    for exam, r in readiness_map.items():
        if r >= 40 and exam in SALARY_DATA:
            a = _avg(exam)
            if a > best_avg:
                best_avg, best_cert = a, exam
    if not best_cert:
        return ("No tracked certs yet", 38_000, 52_000)
    d = SALARY_DATA[best_cert]
    return (best_cert, d["low"], d["high"])


def _fmt_salary(amount: int) -> str:
    return f"${amount:,.0f}"


# ---------------------------------------------------------------------------
# Section: Current Market Value
# ---------------------------------------------------------------------------

def _render_market_value(readiness_map: dict[str, float]) -> None:
    st.subheader("Your Current Market Value")
    render_section_note(
        "Estimated based on your highest-paying cert with 40%+ readiness. "
        "Market value reflects what employers pay for candidates actively studying toward these certs."
    )

    best_cert, low, high = _current_value(readiness_map)
    mid = (low + high) // 2

    col_val, col_cert, col_level = st.columns(3)
    with col_val:
        st.metric(
            "Estimated Range",
            f"{_fmt_salary(low)} – {_fmt_salary(high)}",
            help="Annual salary range for your strongest cert area",
        )
    with col_cert:
        level = SALARY_DATA.get(best_cert, {}).get("level", "—")
        st.metric("Driven By", best_cert, help="Highest-value cert in your active stack")
    with col_level:
        st.metric("Experience Tier", level, help="Entry / Mid / Senior market tier")

    # Active certs table
    active = [
        (exam, r, SALARY_DATA[exam]["low"], SALARY_DATA[exam]["high"], SALARY_DATA[exam]["level"])
        for exam, r in sorted(readiness_map.items(), key=lambda kv: -kv[1])
        if r >= 40 and exam in SALARY_DATA
    ]
    if active:
        st.markdown("**All active certs contributing to your value:**")
        for exam, r, lo, hi, lvl in active:
            bar_pct = int(r)
            badge = "🟢" if r >= 80 else "🟡"
            st.markdown(
                f"{badge} **{exam}** &nbsp; `{r:.0f}%` readiness &nbsp;·&nbsp; "
                f"{_fmt_salary(lo)}–{_fmt_salary(hi)} &nbsp;·&nbsp; {lvl}"
            )
    else:
        st.info("Complete some quizzes to reach 40% readiness on a cert and unlock your market value estimate.")


# ---------------------------------------------------------------------------
# Section: Salary Unlock Calculator
# ---------------------------------------------------------------------------

def _render_salary_calculator(readiness_map: dict[str, float]) -> None:
    st.subheader("Salary Unlock Calculator")
    render_section_note(
        "Select certs you plan to earn. See the projected salary increase each one unlocks, "
        "and a cumulative growth chart."
    )

    _, baseline_low, baseline_high = _current_value(readiness_map)
    baseline_mid = (baseline_low + baseline_high) / 2

    # Only offer certs not yet in active stack
    available = sorted(
        [
            c for c in SALARY_DATA
            if readiness_map.get(c, 0) < 40 and c in EXAM_DOMAINS
        ],
        key=lambda c: _avg(c),
        reverse=True,
    )

    planned = st.multiselect(
        "Certs you plan to earn",
        available,
        default=[],
        key="salary_calc_certs",
        help="Pick any certs from the full catalog. Ordered by earning potential.",
    )

    if not planned:
        st.caption("Select one or more certs above to see your salary projection.")
        return

    # Sort selected by avg salary descending, then compute cumulative
    planned_sorted = sorted(planned, key=_avg, reverse=True)
    cum_salary = baseline_mid
    stages = [("Current Stack", int(baseline_low), int(baseline_high))]

    for cert in planned_sorted:
        d = SALARY_DATA[cert]
        cert_avg = _avg(cert)
        if cert_avg > cum_salary:
            boost = int(cert_avg - cum_salary)
            cum_salary = cert_avg
            stages.append((cert, d["low"], d["high"]))
            st.success(f"Adding **{cert}** unlocks **+{_fmt_salary(boost)}/year** average")
        else:
            stages.append((cert, d["low"], d["high"]))
            st.info(f"**{cert}** broadens your profile but overlaps with a higher-paying cert you already have")

    # Bar chart
    labels = [s[0] for s in stages]
    lows = [s[1] for s in stages]
    highs = [s[2] for s in stages]
    mids = [(lo + hi) // 2 for lo, hi in zip(lows, highs)]
    spreads = [hi - lo for lo, hi in zip(lows, highs)]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=labels,
        y=mids,
        base=[lo for lo in lows],
        marker_color=["#6b7280"] + ["#a78bfa"] * (len(stages) - 1),
        text=[f"{_fmt_salary(lo)}–{_fmt_salary(hi)}" for lo, hi in zip(lows, highs)],
        textposition="outside",
        hovertemplate="<b>%{x}</b><br>Range: %{text}<extra></extra>",
        name="Salary Range",
    ))
    fig.update_layout(
        plot_bgcolor="#111827",
        paper_bgcolor="#111827",
        font=dict(color="#e5e7eb"),
        height=360,
        margin=dict(l=10, r=10, t=30, b=10),
        yaxis=dict(title="Annual Salary (USD)", tickprefix="$", tickformat=",", gridcolor="#374151"),
        xaxis=dict(gridcolor="#374151"),
        showlegend=False,
    )
    st.plotly_chart(fig, use_container_width=True)

    total_boost = int(cum_salary - baseline_mid)
    if total_boost > 0:
        st.markdown(
            f"**Total projected increase:** {_fmt_salary(total_boost)}/year &nbsp;·&nbsp; "
            f"New range: {_fmt_salary(int(cum_salary * 0.9))}–{_fmt_salary(int(cum_salary * 1.1))}"
        )


# ---------------------------------------------------------------------------
# Section: Next Best Cert For Your Goals (Claude API)
# ---------------------------------------------------------------------------

def _build_rec_prompt(goal: str, active_certs: list[str], target_exam: str) -> str:
    certs_str = ", ".join(active_certs) if active_certs else "none yet"
    return f"""You are a career advisor for IT professionals pursuing certifications.

Candidate profile:
- Current certs in progress (40%+ readiness): {certs_str}
- Target exam: {target_exam or 'not set'}
- Career goal: {goal}

Recommend the single best NEXT certification to pursue. Structure your answer as:

**Cert:** [exact cert name]
**Why it fits your goal:** [2-3 sentences]
**Salary impact:** [specific dollar range, e.g. +$22,000–$35,000/year]
**Time to earn:** [realistic weeks/months with focused study]
**Roles it unlocks:** [3 specific job titles]
**Pro tip:** [one tactical study or job-search insight]

Be direct, specific, and realistic. Under 200 words total."""


def _render_next_cert(readiness_map: dict[str, float], profile: dict) -> None:
    st.subheader("Next Best Cert For Your Goals")
    render_section_note("Select your primary career goal and get a personalized cert recommendation powered by AI.")

    goal = st.selectbox("My primary goal right now", _GOAL_OPTIONS, key="career_goal_select")
    target_exam = profile.get("target_exam", "")
    active_certs = [e for e, r in readiness_map.items() if r >= 40]

    cache_key = f"career_rec_{goal}_{sorted(active_certs)}"
    if st.button("Get Recommendation", key="get_rec_btn", type="primary"):
        st.session_state["career_rec_cache_key"] = cache_key
        st.session_state["career_rec_text"] = None

    # Show cached result or fetch new
    if st.session_state.get("career_rec_cache_key") == cache_key and st.session_state.get("career_rec_text"):
        st.markdown(st.session_state["career_rec_text"])
    elif st.session_state.get("career_rec_cache_key") == cache_key and st.session_state.get("career_rec_text") is None:
        prompt = _build_rec_prompt(goal, active_certs, target_exam)
        placeholder = st.empty()
        try:
            import anthropic
            client = anthropic.Anthropic()
            with placeholder.container():
                with st.spinner("Getting personalized recommendation..."):
                    response = client.messages.create(
                        model="claude-sonnet-4-6",
                        max_tokens=400,
                        system="You are a direct, practical IT career advisor. Give specific, actionable advice.",
                        messages=[{"role": "user", "content": prompt}],
                    )
            text = next((b.text for b in response.content if b.type == "text"), "")
            st.session_state["career_rec_text"] = text
            placeholder.empty()
            st.markdown(text)
        except Exception as exc:
            st.error(f"Could not reach AI: {exc}")


# ---------------------------------------------------------------------------
# Section: Resume Gap Analyzer (Claude API)
# ---------------------------------------------------------------------------

def _build_gap_prompt(jd: str, active_certs: list[str]) -> str:
    certs_str = "\n".join(f"- {c}" for c in active_certs) if active_certs else "- None yet"
    return f"""Analyze this job description against the candidate's certification profile. Be specific and direct.

CANDIDATE CERTS (readiness ≥40%):
{certs_str}

JOB DESCRIPTION:
{jd[:3000]}

Return your analysis in EXACTLY this format — use the exact section headers:

MATCH_SCORE: [0-100 integer]

SKILLS_YOU_HAVE:
- [specific skill the candidate demonstrates via their certs]
(list 3-6 items)

SKILLS_MISSING:
- [specific skill gap for this role]
(list 3-6 items)

CLOSING_CERTS:
- [cert name]: [one sentence on why it closes a gap]
(list 2-4 certs)

STUDY_TIME: [e.g. "8-12 weeks of focused study"]

RESUME_BULLETS:
- [ATS-optimized bullet using candidate's existing certs, tailored to this JD]
(write 2-3 bullets)"""


def _parse_gap_response(text: str) -> dict:
    """Extract structured sections from the gap analysis response."""
    def _extract_list(section: str) -> list[str]:
        m = re.search(rf"{section}:\s*\n((?:\s*-[^\n]+\n?)+)", text, re.IGNORECASE)
        if not m:
            return []
        return [line.strip().lstrip("- ").strip() for line in m.group(1).strip().splitlines() if line.strip().startswith("-")]

    def _extract_inline(section: str) -> str:
        m = re.search(rf"{section}:\s*(.+)", text, re.IGNORECASE)
        return m.group(1).strip() if m else ""

    score_raw = _extract_inline("MATCH_SCORE")
    try:
        score = max(0, min(100, int(re.sub(r"[^\d]", "", score_raw))))
    except (ValueError, TypeError):
        score = 0

    return {
        "score": score,
        "have": _extract_list("SKILLS_YOU_HAVE"),
        "missing": _extract_list("SKILLS_MISSING"),
        "certs": _extract_list("CLOSING_CERTS"),
        "time": _extract_inline("STUDY_TIME"),
        "bullets": _extract_list("RESUME_BULLETS"),
    }


def _render_gap_analyzer(readiness_map: dict[str, float]) -> None:
    st.subheader("Resume Gap Analyzer")
    render_section_note(
        "Paste any job description. AI scores your match, identifies skill gaps, "
        "recommends closing certs, and writes ATS-tuned resume bullets. "
        "Earn +25 XP per analysis. Hit 80%+ match to unlock the **Job Ready** badge."
    )

    jd_text = st.text_area(
        "Paste a job description",
        height=220,
        key="gap_jd_input",
        placeholder=(
            "Example: We are looking for a Cloud Security Engineer with experience in AWS IAM, "
            "VPC security groups, and cloud-native threat detection. CompTIA Security+ or AWS "
            "Security Specialty preferred. 3+ years experience required..."
        ),
    )

    if not st.button("Analyze Gap", key="gap_analyze_btn", type="primary", use_container_width=True):
        # Show previous result if it exists
        if st.session_state.get("gap_result"):
            _display_gap_result(st.session_state["gap_result"])
        return

    if not jd_text.strip():
        st.warning("Paste a job description first.")
        return

    active_certs = [e for e, r in readiness_map.items() if r >= 40]
    prompt = _build_gap_prompt(jd_text, active_certs)

    with st.spinner("Analyzing your match against the job description..."):
        try:
            import anthropic
            client = anthropic.Anthropic()
            response = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=800,
                system="You are a precise hiring manager and career coach. Follow the output format exactly.",
                messages=[{"role": "user", "content": prompt}],
            )
            raw = next((b.text for b in response.content if b.type == "text"), "")
        except Exception as exc:
            st.error(f"Analysis failed: {exc}")
            return

    result = _parse_gap_response(raw)
    st.session_state["gap_result"] = result

    # XP reward — once per session using session state guard
    if not st.session_state.get("gap_xp_awarded"):
        add_xp(25, "Resume Gap Analyzer used")
        st.session_state["gap_xp_awarded"] = True
        st.toast("+25 XP — Gap analysis complete!")

    # Badge for high match
    if result["score"] >= 80:
        if award_badge("job_ready", "Job Ready", "Achieved 80%+ match score on a job description analysis"):
            st.success("🏅 Badge unlocked: **Job Ready** — you're qualified for this role!")

    _display_gap_result(result)


def _display_gap_result(result: dict) -> None:
    score = result["score"]
    if score >= 80:
        color, label = "#22c55e", "Strong Match"
    elif score >= 60:
        color, label = "#eab308", "Partial Match"
    else:
        color, label = "#ef4444", "Gap to Close"

    st.markdown(
        f'<div style="background:#1f2937;border-left:4px solid {color};padding:12px 16px;'
        f'border-radius:6px;margin:8px 0">'
        f'<span style="font-size:2rem;font-weight:700;color:{color}">{score}%</span>'
        f'<span style="color:#9ca3af;margin-left:12px">{label}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    col_have, col_miss = st.columns(2)
    with col_have:
        if result["have"]:
            st.markdown("**✅ Skills You Have**")
            for item in result["have"]:
                st.markdown(f"- {item}")
    with col_miss:
        if result["missing"]:
            st.markdown("**⚠️ Skills to Build**")
            for item in result["missing"]:
                st.markdown(f"- {item}")

    if result["certs"]:
        st.markdown("**🎯 Certs That Close the Gap**")
        for item in result["certs"]:
            st.markdown(f"- {item}")

    if result["time"]:
        st.info(f"**Estimated path to qualified:** {result['time']}")

    if result["bullets"]:
        st.markdown("**📄 ATS-Optimized Resume Bullets**")
        st.code("\n".join(f"• {b}" for b in result["bullets"]), language=None)


# ---------------------------------------------------------------------------
# Section: Job Market Trends
# ---------------------------------------------------------------------------

def _render_market_trends() -> None:
    st.subheader("Job Market Trends — 2025")

    tab_demand, tab_salary, tab_remote, tab_companies = st.tabs(
        ["Most In Demand", "Fastest Growing Salaries", "Remote Availability", "Top Hiring Companies"]
    )

    with tab_demand:
        st.caption("Estimated active job postings requiring each cert (US market, Q1 2025)")
        for item in MARKET_TRENDS["most_in_demand"]:
            col_c, col_p, col_y = st.columns([4, 2, 1])
            col_c.write(f"**{item['cert']}**")
            col_p.write(item["postings"])
            col_y.write(f"`{item['yoy']}`")

    with tab_salary:
        st.caption("Year-over-year salary growth rate for certified professionals (2024→2025)")
        for item in MARKET_TRENDS["fastest_salary_growth"]:
            st.markdown(f"**{item['cert']}** &nbsp; `{item['growth']}` &nbsp;·&nbsp; *{item['note']}*")

    with tab_remote:
        st.caption("Percentage of job postings offering full remote or hybrid remote options")
        for item in MARKET_TRENDS["remote_availability"]:
            pct = item["pct"]
            color = "#22c55e" if pct >= 70 else "#eab308" if pct >= 40 else "#ef4444"
            st.markdown(
                f'<div style="display:flex;align-items:center;gap:12px;margin:4px 0">'
                f'<span style="width:180px;color:#e5e7eb">{item["category"]}</span>'
                f'<div style="background:#374151;border-radius:4px;height:12px;width:200px">'
                f'<div style="background:{color};width:{pct}%;height:12px;border-radius:4px"></div></div>'
                f'<span style="color:{color};font-weight:600">{pct}%</span>'
                f'<span style="color:#9ca3af;font-size:0.85em">{item["note"]}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )

    with tab_companies:
        st.caption("Top employers actively hiring for each cert category (2025)")
        for category, companies in MARKET_TRENDS["top_hiring_companies"].items():
            st.markdown(f"**{category}:** " + " · ".join(companies))


# ---------------------------------------------------------------------------
# Section: Salary Timeline
# ---------------------------------------------------------------------------

def _render_salary_timeline(readiness_map: dict[str, float], profile: dict) -> None:
    st.subheader("Your Salary Timeline")
    render_section_note(
        "Projected salary growth as you complete certs in your active stack. "
        "Assumes ~3 months per cert at a focused study pace."
    )

    _, baseline_low, baseline_high = _current_value(readiness_map)
    baseline_mid = (baseline_low + baseline_high) / 2

    # Collect milestones: certs in progress (10–79%) sorted by how close to done
    milestones = []
    for exam, r in sorted(readiness_map.items(), key=lambda kv: -kv[1]):
        if 10 <= r < 80 and exam in SALARY_DATA:
            months = max(1, round((80 - r) / 12))
            milestones.append((months, exam, SALARY_DATA[exam]))

    # Add target exam if not already tracked
    target = profile.get("target_exam", "")
    if target and target in SALARY_DATA and readiness_map.get(target, 0) < 10:
        milestones.append((4, target, SALARY_DATA[target]))

    if not milestones:
        st.info("Start quizzing on a cert to see your salary timeline.")
        return

    # Sort by months ascending, deduplicate
    milestones.sort(key=lambda m: m[0])
    seen = set()
    unique_milestones = []
    for mo, exam, d in milestones:
        if exam not in seen:
            seen.add(exam)
            unique_milestones.append((mo, exam, d))

    # Build step-function timeline
    months_x = [0]
    salary_low_y = [baseline_low]
    salary_high_y = [baseline_high]
    salary_mid_y = [int(baseline_mid)]
    annotations = []
    cur_low, cur_high, cur_mid = baseline_low, baseline_high, int(baseline_mid)

    for mo, exam, d in unique_milestones:
        new_mid = (d["low"] + d["high"]) // 2
        if new_mid > cur_mid:
            # Step up just before milestone and at milestone
            months_x += [mo - 0.01, mo]
            salary_low_y += [cur_low, d["low"]]
            salary_high_y += [cur_high, d["high"]]
            salary_mid_y += [cur_mid, new_mid]
            annotations.append(dict(
                x=mo, y=new_mid,
                text=f"<b>{exam}</b><br>{_fmt_salary(d['low'])}–{_fmt_salary(d['high'])}",
                showarrow=True, arrowhead=2, arrowcolor="#a78bfa",
                font=dict(size=10, color="#e5e7eb"),
                bgcolor="#1f2937", bordercolor="#a78bfa", borderwidth=1,
                ax=0, ay=-40,
            ))
            cur_low, cur_high, cur_mid = d["low"], d["high"], new_mid

    # Extend to month 24
    if months_x[-1] < 24:
        months_x.append(24)
        salary_low_y.append(cur_low)
        salary_high_y.append(cur_high)
        salary_mid_y.append(cur_mid)

    fig = go.Figure()

    # Shaded range band
    fig.add_trace(go.Scatter(
        x=months_x + months_x[::-1],
        y=salary_high_y + salary_low_y[::-1],
        fill="toself",
        fillcolor="rgba(167,139,250,0.15)",
        line=dict(color="rgba(0,0,0,0)"),
        hoverinfo="none",
        showlegend=False,
    ))

    # Mid salary line
    fig.add_trace(go.Scatter(
        x=months_x, y=salary_mid_y,
        mode="lines",
        line=dict(color="#a78bfa", width=3),
        name="Projected Salary",
        hovertemplate="Month %{x}: %{y:$,.0f}/yr<extra></extra>",
    ))

    fig.update_layout(
        plot_bgcolor="#111827",
        paper_bgcolor="#111827",
        font=dict(color="#e5e7eb"),
        height=400,
        margin=dict(l=10, r=10, t=20, b=10),
        xaxis=dict(title="Months from Now", gridcolor="#374151", dtick=3),
        yaxis=dict(title="Annual Salary (USD)", tickprefix="$", tickformat=",", gridcolor="#374151"),
        annotations=annotations,
        legend=dict(bgcolor="#1f2937"),
    )
    st.plotly_chart(fig, use_container_width=True)

    if unique_milestones:
        final_cert = unique_milestones[-1]
        total_boost = cur_mid - int(baseline_mid)
        if total_boost > 0:
            st.caption(
                f"Completing {len(unique_milestones)} cert{'s' if len(unique_milestones) > 1 else ''} "
                f"projects a **+{_fmt_salary(total_boost)}/year** increase over your current baseline."
            )


# ---------------------------------------------------------------------------
# Main render
# ---------------------------------------------------------------------------

def render(ctx: dict) -> None:
    profile = ctx["profile"]
    readiness_map: dict[str, float] = profile.get("exam_readiness", {})

    st.subheader("Career & Salary Intelligence")
    render_section_note(
        "Live market data, AI-powered gap analysis, and salary projections "
        "built around your actual cert progress."
    )

    if not require_feature("career_dashboard"):
        return

    _render_market_value(readiness_map)

    st.markdown("---")
    _render_salary_calculator(readiness_map)

    st.markdown("---")
    _render_next_cert(readiness_map, profile)

    st.markdown("---")
    _render_gap_analyzer(readiness_map)

    st.markdown("---")
    _render_market_trends()

    st.markdown("---")
    _render_salary_timeline(readiness_map, profile)
