from __future__ import annotations

from datetime import datetime
from html import escape

import plotly.graph_objects as go
import streamlit as st


COLOR_TOKENS = {
    "bg": "#edf3f6",
    "surface": "#ffffff",
    "surface_alt": "#f7fafc",
    "ink": "#102033",
    "muted": "#5d6c7d",
    "line": "rgba(16, 32, 51, 0.10)",
    "accent": "#0c7a6b",
    "accent_2": "#d96b2b",
    "accent_soft": "#d8f4ee",
    "accent_2_soft": "#ffe6d7",
    "danger": "#a64814",
    "danger_soft": "#ffeadf",
    "success": "#0c7a6b",
    "success_soft": "#d5f7ef",
    "hero": "#102033",
}


def inject_app_css() -> None:
    st.markdown(
        f"""
        <style>
        :root {{
            --bg: {COLOR_TOKENS["bg"]};
            --surface: {COLOR_TOKENS["surface"]};
            --surface-alt: {COLOR_TOKENS["surface_alt"]};
            --ink: {COLOR_TOKENS["ink"]};
            --muted: {COLOR_TOKENS["muted"]};
            --line: {COLOR_TOKENS["line"]};
            --accent: {COLOR_TOKENS["accent"]};
            --accent-2: {COLOR_TOKENS["accent_2"]};
            --accent-soft: {COLOR_TOKENS["accent_soft"]};
            --accent-2-soft: {COLOR_TOKENS["accent_2_soft"]};
            --danger: {COLOR_TOKENS["danger"]};
            --danger-soft: {COLOR_TOKENS["danger_soft"]};
        }}
        .stApp {{
            background:
                radial-gradient(circle at 0% 0%, rgba(12, 122, 107, 0.18), transparent 26%),
                radial-gradient(circle at 100% 0%, rgba(217, 107, 43, 0.18), transparent 24%),
                radial-gradient(circle at 50% 18%, rgba(16, 32, 51, 0.06), transparent 32%),
                linear-gradient(180deg, #f8fbfd 0%, #edf3f6 54%, #eef4f1 100%);
            color: var(--ink);
        }}
        .block-container {{
            max-width: 1240px;
            padding-top: 1rem;
            padding-bottom: 3.5rem;
        }}
        section[data-testid="stSidebar"] {{
            background:
                linear-gradient(180deg, rgba(16, 32, 51, 0.98), rgba(12, 122, 107, 0.94));
            border-right: 1px solid rgba(255,255,255,0.08);
        }}
        section[data-testid="stSidebar"] * {{
            color: #f8fafc !important;
        }}
        section[data-testid="stSidebar"] [data-baseweb="select"] > div,
        section[data-testid="stSidebar"] [data-baseweb="input"] > div,
        section[data-testid="stSidebar"] textarea,
        section[data-testid="stSidebar"] input {{
            background: rgba(255,255,255,0.12) !important;
            border-color: rgba(255,255,255,0.12) !important;
        }}
        .brand-ribbon {{
            display: flex;
            flex-wrap: wrap;
            gap: 0.7rem;
            align-items: center;
            margin: 0 0 0.9rem 0;
        }}
        .brand-chip {{
            padding: 0.4rem 0.85rem;
            border-radius: 999px;
            background: rgba(255,255,255,0.72);
            border: 1px solid rgba(16, 32, 51, 0.08);
            color: var(--ink);
            font-size: 0.78rem;
            font-weight: 800;
            letter-spacing: 0.06em;
            text-transform: uppercase;
            box-shadow: 0 10px 24px rgba(16, 32, 51, 0.05);
        }}
        .brand-chip.alt {{
            background: linear-gradient(135deg, rgba(217,107,43,0.16), rgba(255,255,255,0.92));
            color: var(--accent-2);
        }}
        .hero-panel {{
            position: relative;
            overflow: hidden;
            background:
                radial-gradient(circle at top right, rgba(255,255,255,0.12), transparent 24%),
                radial-gradient(circle at bottom left, rgba(217,107,43,0.18), transparent 30%),
                linear-gradient(135deg, rgba(16, 32, 51, 0.99), rgba(12, 122, 107, 0.94));
            color: #f8fafc;
            padding: 1.55rem 1.6rem;
            border-radius: 30px;
            box-shadow: 0 26px 60px rgba(16, 32, 51, 0.16);
            border: 1px solid rgba(255,255,255,0.08);
            margin-bottom: 1.15rem;
        }}
        .hero-panel::after {{
            content: "";
            position: absolute;
            inset: auto -8% -28% auto;
            width: 240px;
            height: 240px;
            border-radius: 50%;
            background: radial-gradient(circle, rgba(255,255,255,0.12), transparent 62%);
            pointer-events: none;
        }}
        .hero-eyebrow {{
            text-transform: uppercase;
            letter-spacing: 0.18em;
            font-size: 0.72rem;
            opacity: 0.76;
            margin-bottom: 0.7rem;
            font-weight: 800;
        }}
        .hero-panel h2 {{
            margin: 0 0 0.5rem 0;
            font-size: 2.2rem;
            line-height: 1.02;
        }}
        .hero-panel p {{
            margin: 0.22rem 0;
            opacity: 0.95;
            max-width: 60rem;
        }}
        .hero-stats {{
            display: flex;
            flex-wrap: wrap;
            gap: 0.75rem;
            margin-top: 1rem;
        }}
        .hero-stat {{
            min-width: 150px;
            padding: 0.7rem 0.85rem;
            border-radius: 18px;
            background: rgba(255,255,255,0.08);
            border: 1px solid rgba(255,255,255,0.09);
            backdrop-filter: blur(6px);
        }}
        .hero-stat strong {{
            display: block;
            font-size: 1.08rem;
            color: #ffffff;
        }}
        .hero-stat span {{
            display: block;
            font-size: 0.78rem;
            opacity: 0.8;
            text-transform: uppercase;
            letter-spacing: 0.08em;
        }}
        .spotlight-grid {{
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 0.95rem;
            margin-bottom: 1.1rem;
        }}
        .spotlight-card {{
            background: linear-gradient(180deg, rgba(255,255,255,0.94), rgba(255,255,255,0.84));
            border: 1px solid rgba(16, 32, 51, 0.08);
            border-radius: 24px;
            padding: 1rem 1.05rem;
            box-shadow: 0 14px 36px rgba(16, 32, 51, 0.06);
        }}
        .spotlight-card small {{
            display: block;
            color: var(--muted);
            text-transform: uppercase;
            letter-spacing: 0.08em;
            font-size: 0.72rem;
            margin-bottom: 0.45rem;
            font-weight: 800;
        }}
        .spotlight-card strong {{
            display: block;
            color: var(--ink);
            font-size: 1.45rem;
            line-height: 1.05;
            margin-bottom: 0.35rem;
        }}
        .spotlight-card span {{
            color: var(--muted);
            font-size: 0.88rem;
        }}
        .metric-card {{
            background:
                linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(247, 250, 252, 0.94));
            border: 1px solid rgba(16, 32, 51, 0.08);
            border-radius: 24px;
            padding: 1rem 1.05rem;
            box-shadow: 0 16px 38px rgba(16, 32, 51, 0.06);
            min-height: 132px;
            position: relative;
            overflow: hidden;
        }}
        .metric-card::before {{
            content: "";
            position: absolute;
            inset: 0 auto 0 0;
            width: 5px;
            background: linear-gradient(180deg, var(--accent), var(--accent-2));
        }}
        .metric-card h4 {{
            margin: 0 0 0.42rem 0;
            color: var(--muted);
            font-size: 0.82rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            font-weight: 800;
        }}
        .metric-card p {{
            margin: 0;
            font-size: 2.1rem;
            font-weight: 800;
            color: var(--ink);
            line-height: 1;
        }}
        .metric-card span {{
            display: block;
            margin-top: 0.5rem;
            color: var(--accent);
            font-size: 0.84rem;
            font-weight: 700;
        }}
        .section-note, .insight-card, .topic-card {{
            background: rgba(255,255,255,0.9);
            border: 1px solid rgba(16, 32, 51, 0.08);
            border-radius: 20px;
            padding: 1rem 1.05rem;
            color: var(--ink);
            box-shadow: 0 12px 28px rgba(16, 32, 51, 0.05);
        }}
        .section-note {{
            border-left: 5px solid var(--accent);
            background:
                linear-gradient(90deg, rgba(12,122,107,0.08), rgba(255,255,255,0.96));
            margin-bottom: 1rem;
        }}
        .insight-card h4, .topic-card h4 {{
            margin: 0 0 0.45rem 0;
            font-size: 1rem;
            color: var(--ink);
            font-weight: 800;
        }}
        .insight-card p, .topic-card p {{
            margin: 0.2rem 0;
            color: var(--muted);
            line-height: 1.45;
        }}
        .pill-row {{
            display: flex;
            flex-wrap: wrap;
            gap: 0.45rem;
            margin-top: 0.8rem;
        }}
        .pill {{
            display: inline-flex;
            align-items: center;
            border-radius: 999px;
            padding: 0.38rem 0.76rem;
            background: linear-gradient(135deg, var(--accent-soft), rgba(255,255,255,0.9));
            color: var(--accent);
            font-size: 0.78rem;
            font-weight: 800;
            letter-spacing: 0.03em;
        }}
        .warning-pill {{
            background: linear-gradient(135deg, var(--danger-soft), rgba(255,255,255,0.9));
            color: var(--danger);
        }}
        .question-shell {{
            background:
                linear-gradient(180deg, rgba(255,255,255,0.96), rgba(247,250,252,0.9));
            border: 1px solid rgba(16, 32, 51, 0.08);
            border-radius: 22px;
            padding: 1rem 1rem 0.45rem 1rem;
            margin-bottom: 0.95rem;
            box-shadow: 0 14px 28px rgba(16, 32, 51, 0.05);
        }}
        .question-shell h4 {{
            margin: 0 0 0.35rem 0;
            color: var(--ink);
            font-size: 1rem;
            line-height: 1.35;
        }}
        .question-meta {{
            color: var(--muted);
            font-size: 0.83rem;
            margin-bottom: 0.8rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}
        .stTabs [data-baseweb="tab-list"] {{
            gap: 0.45rem;
            flex-wrap: wrap;
            margin-bottom: 0.8rem;
        }}
        .stTabs [data-baseweb="tab"] {{
            background: rgba(255,255,255,0.76);
            border: 1px solid rgba(16, 32, 51, 0.08);
            border-radius: 999px;
            min-height: 42px;
            padding: 0 0.95rem;
            color: var(--muted);
            font-weight: 800;
        }}
        .stTabs [aria-selected="true"] {{
            background: linear-gradient(135deg, rgba(16,32,51,0.96), rgba(12,122,107,0.92)) !important;
            color: #ffffff !important;
            border-color: rgba(12,122,107,0.3) !important;
            box-shadow: 0 10px 24px rgba(16, 32, 51, 0.12);
        }}
        .stButton > button, .stDownloadButton > button {{
            border-radius: 16px;
            border: 1px solid rgba(16, 32, 51, 0.08);
            box-shadow: 0 10px 24px rgba(16, 32, 51, 0.06);
            font-weight: 800;
            letter-spacing: 0.02em;
        }}
        .stButton > button[kind="primary"] {{
            background: linear-gradient(135deg, var(--hero), var(--accent));
            color: #ffffff;
            border: none;
        }}
        [data-testid="stDataFrame"], .stPlotlyChart, .stAlert {{
            background: rgba(255,255,255,0.74);
            border-radius: 20px;
            padding: 0.35rem;
        }}
        [data-testid="stMetric"] {{
            background: transparent;
        }}
        @media (max-width: 980px) {{
            .block-container {{
                padding-top: 0.8rem;
                padding-left: 1rem;
                padding-right: 1rem;
            }}
            .hero-panel {{
                border-radius: 24px;
                padding: 1.15rem;
            }}
            .hero-panel h2 {{
                font-size: 1.72rem;
            }}
            .metric-card {{
                min-height: 110px;
            }}
            .metric-card p {{
                font-size: 1.65rem;
            }}
            .spotlight-grid {{
                grid-template-columns: 1fr;
            }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_metric_card(label: str, value: str, detail: str | None = None) -> None:
    safe_label = escape(label)
    safe_value = escape(value)
    detail_html = f"<span>{escape(detail)}</span>" if detail else ""
    st.markdown(
        f"<div class='metric-card'><h4>{safe_label}</h4><p>{safe_value}</p>{detail_html}</div>",
        unsafe_allow_html=True,
    )


def render_brand_ribbon(items: list[tuple[str, bool]]) -> None:
    chips = "".join(
        f"<span class='brand-chip{' alt' if is_alt else ''}'>{escape(label)}</span>"
        for label, is_alt in items
    )
    st.markdown(f"<div class='brand-ribbon'>{chips}</div>", unsafe_allow_html=True)


def render_showcase_strip(items: list[dict]) -> None:
    cards = []
    for item in items:
        cards.append(
            "<div class='spotlight-card'>"
            f"<small>{escape(item['label'])}</small>"
            f"<strong>{escape(item['value'])}</strong>"
            f"<span>{escape(item['detail'])}</span>"
            "</div>"
        )
    st.markdown(f"<div class='spotlight-grid'>{''.join(cards)}</div>", unsafe_allow_html=True)


def render_hero_panel(exam: str, mode: str, readiness: float, latest_score: float, attempts: int) -> None:
    safe_exam = escape(exam)
    safe_mode = escape(mode)
    st.markdown(
        (
            "<div class='hero-panel'>"
            "<div class='hero-eyebrow'>NetSecure StudyOS</div>"
            f"<h2>{safe_exam} Mission Control</h2>"
            "<p>Turn certification prep into something that actually feels sharp: local analytics, adaptive review pressure, full-exam endurance tracking, and portfolio-ready homelabs.</p>"
            "<div class='hero-stats'>"
            f"<div class='hero-stat'><span>Mode</span><strong>{safe_mode}</strong></div>"
            f"<div class='hero-stat'><span>Readiness</span><strong>{readiness:.1f}/100</strong></div>"
            f"<div class='hero-stat'><span>Latest Score</span><strong>{latest_score:.1f}%</strong></div>"
            f"<div class='hero-stat'><span>Attempts Saved</span><strong>{attempts}</strong></div>"
            "</div>"
            "</div>"
        ),
        unsafe_allow_html=True,
    )


def render_section_note(text: str) -> None:
    st.markdown(f"<div class='section-note'>{escape(text)}</div>", unsafe_allow_html=True)


def render_insight_card(title: str, body: str, pills: list[str] | None = None, warning: bool = False) -> None:
    safe_title = escape(title)
    safe_body = escape(body)
    pill_html = ""
    if pills:
        pill_class = "warning-pill" if warning else "pill"
        pill_html = "<div class='pill-row'>" + "".join(
            f"<span class='pill {pill_class}'>{escape(pill)}</span>" for pill in pills
        ) + "</div>"
    st.markdown(
        f"<div class='insight-card'><h4>{safe_title}</h4><p>{safe_body}</p>{pill_html}</div>",
        unsafe_allow_html=True,
    )


def render_topic_card(title: str, lines: list[str], pills: list[str] | None = None) -> None:
    safe_title = escape(title)
    content = "".join(f"<p>{escape(line)}</p>" for line in lines)
    pill_html = ""
    if pills:
        pill_html = "<div class='pill-row'>" + "".join(f"<span class='pill'>{escape(pill)}</span>" for pill in pills) + "</div>"
    st.markdown(
        f"<div class='topic-card'><h4>{safe_title}</h4>{content}{pill_html}</div>",
        unsafe_allow_html=True,
    )


def countdown_html(end_time_iso: str) -> str:
    return f"""
    <div id="timer" style="font-family: sans-serif; padding: 0.75rem 1rem; border-radius: 16px;
    background: linear-gradient(135deg, #102033, #0c7a6b); color: white; font-weight: 700; box-shadow: 0 12px 28px rgba(16,32,51,0.16);">Time remaining: calculating...</div>
    <script>
    const endTime = new Date("{end_time_iso}").getTime();
    const el = document.getElementById("timer");
    const tick = () => {{
      const now = new Date().getTime();
      const diff = Math.max(0, endTime - now);
      const mins = Math.floor(diff / 60000);
      const secs = Math.floor((diff % 60000) / 1000);
      el.innerText = `Time remaining: ${{String(mins).padStart(2, "0")}}:${{String(secs).padStart(2, "0")}}`;
      if (diff <= 0) {{
        el.innerText = "Time remaining: 00:00";
      }}
    }};
    tick();
    setInterval(tick, 1000);
    </script>
    """


def apply_chart_style(fig: go.Figure, title: str | None = None, height: int = 360) -> go.Figure:
    fig.update_layout(
        title=title,
        height=height,
        margin=dict(l=18, r=18, t=56 if title else 28, b=18),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(255,255,255,0.92)",
        font=dict(color=COLOR_TOKENS["ink"]),
        coloraxis_colorbar=dict(outlinewidth=0),
        legend=dict(bgcolor="rgba(255,255,255,0.65)", borderwidth=0),
    )
    fig.update_xaxes(showgrid=False, linecolor="rgba(16, 32, 51, 0.10)")
    fig.update_yaxes(
        gridcolor="rgba(16, 32, 51, 0.08)",
        zeroline=False,
        linecolor="rgba(16, 32, 51, 0.10)",
        rangemode="tozero",
    )
    return fig


def default_minutes_for_exam(question_count: int) -> int:
    if question_count >= 100:
        return 120
    if question_count >= 90:
        return 105
    if question_count >= 50:
        return 60
    if question_count >= 25:
        return 35
    return 15


def format_timestamp(value: str | None) -> str:
    if not value:
        return "-"
    return datetime.fromisoformat(value).strftime("%b %d, %Y %I:%M %p")
