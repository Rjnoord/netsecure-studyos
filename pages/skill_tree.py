from __future__ import annotations

from collections import defaultdict

import plotly.graph_objects as go
import streamlit as st

from exams import EXAM_DOMAINS
from storage import get_level_info
from utils import render_section_note

# ---------------------------------------------------------------------------
# Static layout — computed once, never recalculated
# ---------------------------------------------------------------------------

# Node keys that appear in multiple paths are shared (single position).
# Each node: id, label, exam_id (None = external / untracked), x, y, paths
_NODES: list[dict] = [
    # ── IT FOUNDATION (y = 10) ──────────────────────────────────────────────
    {"id": "tech_plus",        "label": "Tech+\n(ITF+)",              "exam_id": "Tech+",                            "x": 0,    "y": 10,   "paths": ["IT Foundation"]},
    {"id": "a_plus",           "label": "A+",                         "exam_id": "A+",                               "x": 2,    "y": 10,   "paths": ["IT Foundation"]},
    {"id": "network_plus",     "label": "Network+",                   "exam_id": "Network+",                         "x": 4,    "y": 10,   "paths": ["IT Foundation", "Network Engineering"]},
    {"id": "security_plus",    "label": "Security+",                  "exam_id": "Security+",                        "x": 6,    "y": 10,   "paths": ["IT Foundation", "Security"]},
    # ── NETWORK ENGINEERING (y = 7.5) ────────────────────────────────────────
    {"id": "ccna",             "label": "CCNA",                       "exam_id": "CCNA",                             "x": 5,    "y": 7.5,  "paths": ["Network Engineering", "DevOps"]},
    {"id": "ccnp_enterprise",  "label": "CCNP\nEnterprise",           "exam_id": "CCNP Enterprise",                  "x": 7,    "y": 7.5,  "paths": ["Network Engineering"]},
    {"id": "ccie_enterprise",  "label": "CCIE\nEnterprise",           "exam_id": "CCIE Enterprise Infrastructure",   "x": 9,    "y": 7.5,  "paths": ["Network Engineering"]},
    # ── SECURITY — main branch (y = 6.5) ─────────────────────────────────────
    {"id": "cysa_plus",        "label": "CySA+",                      "exam_id": "CySA+",                            "x": 7.5,  "y": 6.5,  "paths": ["Security"]},
    {"id": "pentest_plus",     "label": "PenTest+",                   "exam_id": "PenTest+",                         "x": 9,    "y": 6.5,  "paths": ["Security"]},
    {"id": "securityx",        "label": "SecurityX",                  "exam_id": "SecurityX",                        "x": 10.5, "y": 6.5,  "paths": ["Security"]},
    # ── SECURITY — CEH / OSCP branch (y = 5.5) ───────────────────────────────
    {"id": "ceh",              "label": "CEH",                        "exam_id": None,                               "x": 7.5,  "y": 5.5,  "paths": ["Security"]},
    {"id": "oscp",             "label": "OSCP",                       "exam_id": None,                               "x": 9,    "y": 5.5,  "paths": ["Security"]},
    # ── SECURITY — CISSP / CISM branch (y = 7.5) ─────────────────────────────
    {"id": "cissp",            "label": "CISSP",                      "exam_id": None,                               "x": 8,    "y": 7.4,  "paths": ["Security"]},
    {"id": "cism",             "label": "CISM",                       "exam_id": None,                               "x": 9.5,  "y": 7.4,  "paths": ["Security"]},
    # ── CLOUD — AWS (y = 4 / 3) ──────────────────────────────────────────────
    {"id": "aws_ccp",          "label": "AWS Cloud\nPractitioner",    "exam_id": "AWS Cloud Practitioner",           "x": 0,    "y": 3.5,  "paths": ["Cloud"]},
    {"id": "aws_saa",          "label": "AWS SAA",                    "exam_id": "AWS Solutions Architect Associate", "x": 2,    "y": 4,    "paths": ["Cloud"]},
    {"id": "aws_sap",          "label": "AWS SAP",                    "exam_id": "AWS Solutions Architect Professional", "x": 4, "y": 4,   "paths": ["Cloud"]},
    {"id": "aws_dev",          "label": "AWS\nDeveloper",             "exam_id": "AWS Developer Associate",          "x": 2,    "y": 3,    "paths": ["Cloud", "DevOps"]},
    {"id": "aws_devops",       "label": "AWS\nDevOps",                "exam_id": "AWS DevOps Engineer Professional", "x": 4,    "y": 3,    "paths": ["Cloud", "DevOps"]},
    # ── CLOUD — Azure (y = 2 / 1) ────────────────────────────────────────────
    {"id": "az900",            "label": "AZ-900",                     "exam_id": "AZ-900",                           "x": 0,    "y": 2,    "paths": ["Cloud"]},
    {"id": "az104",            "label": "AZ-104",                     "exam_id": "AZ-104",                           "x": 2,    "y": 2.5,  "paths": ["Cloud", "DevOps"]},
    {"id": "az305",            "label": "AZ-305",                     "exam_id": "AZ-305",                           "x": 4,    "y": 2.5,  "paths": ["Cloud"]},
    {"id": "az500",            "label": "AZ-500",                     "exam_id": "AZ-500",                           "x": 2,    "y": 1.5,  "paths": ["Cloud"]},
    {"id": "sc100",            "label": "SC-100",                     "exam_id": None,                               "x": 4,    "y": 1.5,  "paths": ["Cloud"]},
    # ── CLOUD — GCP (y = 0.5) ────────────────────────────────────────────────
    {"id": "gcdl",             "label": "Google Cloud\nDigital Leader", "exam_id": None,                             "x": 0,    "y": 0.5,  "paths": ["Cloud"]},
    {"id": "gcp_ace",          "label": "GCP ACE",                    "exam_id": None,                               "x": 2,    "y": 0.5,  "paths": ["Cloud"]},
    {"id": "gcp_pca",          "label": "GCP PCA",                    "exam_id": None,                               "x": 4,    "y": 0.5,  "paths": ["Cloud"]},
    # ── DEVOPS (y = -1) ───────────────────────────────────────────────────────
    {"id": "devnet_assoc",     "label": "Cisco DevNet\nAssociate",    "exam_id": "CCNA Automation",                  "x": 6.5,  "y": -1,   "paths": ["DevOps"]},
    {"id": "devnet_pro",       "label": "Cisco DevNet\nPro",          "exam_id": "CCNP Automation",                  "x": 8.5,  "y": -1,   "paths": ["DevOps"]},
    {"id": "az400",            "label": "AZ-400",                     "exam_id": "AZ-400",                           "x": 3,    "y": -1,   "paths": ["DevOps"]},
    # ── LINUX (y = -3) ────────────────────────────────────────────────────────
    {"id": "linux_plus",       "label": "Linux+",                     "exam_id": "Linux+",                           "x": 0,    "y": -3,   "paths": ["Linux"]},
    {"id": "lfcs",             "label": "LFCS",                       "exam_id": None,                               "x": 2,    "y": -3,   "paths": ["Linux"]},
    {"id": "rhcsa",            "label": "RHCSA",                      "exam_id": None,                               "x": 4,    "y": -3,   "paths": ["Linux"]},
    {"id": "rhce",             "label": "RHCE",                       "exam_id": None,                               "x": 6,    "y": -3,   "paths": ["Linux"]},
    {"id": "cka",              "label": "CKA",                        "exam_id": None,                               "x": 8,    "y": -3,   "paths": ["Linux"]},
    {"id": "cks",              "label": "CKS",                        "exam_id": None,                               "x": 10,   "y": -3,   "paths": ["Linux"]},
    # ── DATA (y = -5) ─────────────────────────────────────────────────────────
    {"id": "data_plus",        "label": "Data+",                      "exam_id": "Data+",                            "x": 0,    "y": -5,   "paths": ["Data"]},
    {"id": "aws_data_eng",     "label": "AWS Data\nEngineer",         "exam_id": "AWS Data Engineer Associate",      "x": 2.5,  "y": -5,   "paths": ["Data"]},
    {"id": "dp900",            "label": "DP-900",                     "exam_id": "DP-900",                           "x": 5,    "y": -5,   "paths": ["Data"]},
    {"id": "gcp_data_eng",     "label": "Google\nData Engineer",      "exam_id": None,                               "x": 7.5,  "y": -5,   "paths": ["Data"]},
]

# Build id→node index for edge resolution
_NODE_INDEX: dict[str, int] = {n["id"]: i for i, n in enumerate(_NODES)}

# Edges: source id, target id, owning path (for color)
_EDGES: list[dict] = [
    # IT Foundation
    {"s": "tech_plus",       "t": "a_plus",          "path": "IT Foundation"},
    {"s": "a_plus",          "t": "network_plus",     "path": "IT Foundation"},
    {"s": "network_plus",    "t": "security_plus",    "path": "IT Foundation"},
    # Network Engineering
    {"s": "network_plus",    "t": "ccna",             "path": "Network Engineering"},
    {"s": "ccna",            "t": "ccnp_enterprise",  "path": "Network Engineering"},
    {"s": "ccnp_enterprise", "t": "ccie_enterprise",  "path": "Network Engineering"},
    # Security — main
    {"s": "security_plus",   "t": "cysa_plus",        "path": "Security"},
    {"s": "cysa_plus",       "t": "pentest_plus",     "path": "Security"},
    {"s": "pentest_plus",    "t": "securityx",        "path": "Security"},
    # Security — CEH/OSCP
    {"s": "security_plus",   "t": "ceh",              "path": "Security"},
    {"s": "ceh",             "t": "oscp",             "path": "Security"},
    # Security — CISSP/CISM
    {"s": "security_plus",   "t": "cissp",            "path": "Security"},
    {"s": "cysa_plus",       "t": "cism",             "path": "Security"},
    # Cloud — AWS main
    {"s": "aws_ccp",         "t": "aws_saa",          "path": "Cloud"},
    {"s": "aws_saa",         "t": "aws_sap",          "path": "Cloud"},
    # Cloud — AWS dev
    {"s": "aws_ccp",         "t": "aws_dev",          "path": "Cloud"},
    {"s": "aws_dev",         "t": "aws_devops",       "path": "Cloud"},
    # Cloud — Azure main
    {"s": "az900",           "t": "az104",            "path": "Cloud"},
    {"s": "az104",           "t": "az305",            "path": "Cloud"},
    # Cloud — Azure security
    {"s": "az900",           "t": "az500",            "path": "Cloud"},
    {"s": "az500",           "t": "sc100",            "path": "Cloud"},
    # Cloud — GCP
    {"s": "gcdl",            "t": "gcp_ace",          "path": "Cloud"},
    {"s": "gcp_ace",         "t": "gcp_pca",          "path": "Cloud"},
    # DevOps
    {"s": "ccna",            "t": "devnet_assoc",     "path": "DevOps"},
    {"s": "devnet_assoc",    "t": "devnet_pro",       "path": "DevOps"},
    {"s": "az104",           "t": "az400",            "path": "DevOps"},
    {"s": "aws_dev",         "t": "aws_devops",       "path": "DevOps"},
    # Linux
    {"s": "linux_plus",      "t": "lfcs",             "path": "Linux"},
    {"s": "lfcs",            "t": "rhcsa",            "path": "Linux"},
    {"s": "rhcsa",           "t": "rhce",             "path": "Linux"},
    {"s": "rhce",            "t": "cka",              "path": "Linux"},
    {"s": "cka",             "t": "cks",              "path": "Linux"},
    # Data
    {"s": "data_plus",       "t": "aws_data_eng",     "path": "Data"},
    {"s": "aws_data_eng",    "t": "dp900",            "path": "Data"},
    {"s": "dp900",           "t": "gcp_data_eng",     "path": "Data"},
]

# Path display config
_PATH_COLORS: dict[str, str] = {
    "IT Foundation":       "#60a5fa",   # blue
    "Network Engineering": "#34d399",   # green
    "Security":            "#f87171",   # red
    "Cloud":               "#a78bfa",   # purple
    "DevOps":              "#fbbf24",   # amber
    "Linux":               "#fb923c",   # orange
    "Data":                "#94a3b8",   # slate
}

# Path label positions (x, y) for annotation markers on left side
_PATH_LABELS: list[dict] = [
    {"path": "IT Foundation",       "y": 10,   "x": -1.5},
    {"path": "Network Engineering", "y": 7.5,  "x": -1.5},
    {"path": "Security",            "y": 6.5,  "x": -1.5},
    {"path": "Cloud",               "y": 2.5,  "x": -1.5},
    {"path": "DevOps",              "y": -1,   "x": -1.5},
    {"path": "Linux",               "y": -3,   "x": -1.5},
    {"path": "Data",                "y": -5,   "x": -1.5},
]

# Progression chains used for "suggested next cert"
_CHAINS: list[list[str]] = [
    ["tech_plus", "a_plus", "network_plus", "security_plus"],
    ["network_plus", "ccna", "ccnp_enterprise", "ccie_enterprise"],
    ["security_plus", "cysa_plus", "pentest_plus", "securityx"],
    ["security_plus", "ceh", "oscp"],
    ["aws_ccp", "aws_saa", "aws_sap"],
    ["aws_ccp", "aws_dev", "aws_devops"],
    ["az900", "az104", "az305"],
    ["az900", "az500", "sc100"],
    ["ccna", "devnet_assoc", "devnet_pro"],
    ["az104", "az400"],
    ["linux_plus", "lfcs", "rhcsa", "rhce", "cka", "cks"],
    ["data_plus", "aws_data_eng", "dp900", "gcp_data_eng"],
]

ALL_PATHS = ["All Paths"] + sorted(_PATH_COLORS.keys())


# ---------------------------------------------------------------------------
# Node appearance helpers
# ---------------------------------------------------------------------------

def _node_color(readiness: float | None) -> str:
    if readiness is None or readiness < 5:
        return "#6b7280"   # gray — not started
    if readiness >= 95:
        return "#f59e0b"   # gold — near-perfect
    if readiness >= 80:
        return "#22c55e"   # green — mastered / ready
    if readiness >= 40:
        return "#eab308"   # yellow — in progress
    return "#6b7280"       # gray — barely started


def _node_symbol(readiness: float | None) -> str:
    if readiness is not None and readiness >= 95:
        return "star"
    return "circle"


def _node_size(sessions: int) -> int:
    return min(22 + sessions * 2, 42)


def _node_border_color(readiness: float | None) -> str:
    if readiness is None or readiness < 5:
        return "#9ca3af"
    if readiness >= 95:
        return "#d97706"
    if readiness >= 80:
        return "#16a34a"
    if readiness >= 40:
        return "#ca8a04"
    return "#9ca3af"


# ---------------------------------------------------------------------------
# Figure builder
# ---------------------------------------------------------------------------

def _build_figure(
    visible_node_ids: set[str],
    readiness_map: dict[str, float],
    sessions_map: dict[str, int],
    selected_path: str,
) -> go.Figure:
    fig = go.Figure()

    # ── Edge traces, grouped by path ────────────────────────────────────────
    edges_by_path: dict[str, list] = defaultdict(list)
    for edge in _EDGES:
        s, t = edge["s"], edge["t"]
        if s not in visible_node_ids or t not in visible_node_ids:
            continue
        sn = _NODES[_NODE_INDEX[s]]
        tn = _NODES[_NODE_INDEX[t]]
        edges_by_path[edge["path"]].append((sn["x"], sn["y"], tn["x"], tn["y"]))

    for path, segs in edges_by_path.items():
        xs, ys = [], []
        for sx, sy, tx, ty in segs:
            xs += [sx, tx, None]
            ys += [sy, ty, None]
        fig.add_trace(go.Scatter(
            x=xs, y=ys,
            mode="lines",
            line=dict(color=_PATH_COLORS[path], width=2),
            hoverinfo="none",
            showlegend=False,
        ))

    # ── Node trace ───────────────────────────────────────────────────────────
    vis_nodes = [n for n in _NODES if n["id"] in visible_node_ids]
    xs = [n["x"] for n in vis_nodes]
    ys = [n["y"] for n in vis_nodes]
    colors = [_node_color(readiness_map.get(n["exam_id"])) for n in vis_nodes]
    symbols = [_node_symbol(readiness_map.get(n["exam_id"])) for n in vis_nodes]
    sizes = [_node_size(sessions_map.get(n["exam_id"] or "", 0)) for n in vis_nodes]
    border_colors = [_node_border_color(readiness_map.get(n["exam_id"])) for n in vis_nodes]
    labels = [n["label"] for n in vis_nodes]
    custom = [n["exam_id"] or "" for n in vis_nodes]

    hover_texts = []
    for n in vis_nodes:
        r = readiness_map.get(n["exam_id"])
        s = sessions_map.get(n["exam_id"] or "", 0)
        tracked = "✓ Tracked" if n["exam_id"] in EXAM_DOMAINS else "○ External"
        r_str = f"{r:.0f}%" if r is not None else "Not started"
        hover_texts.append(
            f"<b>{n['label'].replace(chr(10), ' ')}</b><br>"
            f"Readiness: {r_str}<br>"
            f"Quiz sessions: {s}<br>"
            f"{tracked}"
        )

    fig.add_trace(go.Scatter(
        x=xs, y=ys,
        mode="markers+text",
        marker=dict(
            color=colors,
            size=sizes,
            symbol=symbols,
            line=dict(color=border_colors, width=2),
        ),
        text=labels,
        textposition="bottom center",
        textfont=dict(size=9, color="#e5e7eb"),
        hovertext=hover_texts,
        hoverinfo="text",
        customdata=custom,
        showlegend=False,
        name="certs",
    ))

    # ── Path label annotations (left margin) ─────────────────────────────────
    annotations = []
    for pl in _PATH_LABELS:
        if selected_path != "All Paths" and pl["path"] != selected_path:
            continue
        annotations.append(dict(
            x=pl["x"], y=pl["y"],
            text=f"<b>{pl['path']}</b>",
            showarrow=False,
            font=dict(size=10, color=_PATH_COLORS[pl["path"]]),
            xanchor="right",
        ))

    # ── Legend boxes (color system) ──────────────────────────────────────────
    legend_items = [
        ("⭐ Gold star",    "#f59e0b", "95%+ readiness — Elite"),
        ("● Green",         "#22c55e", "80–94% — Ready"),
        ("● Yellow",        "#eab308", "40–79% — In progress"),
        ("● Gray",          "#6b7280", "< 40% or not started"),
    ]
    legend_x, legend_y = 11.5, 10.5
    annotations.append(dict(
        x=legend_x, y=legend_y,
        text="<b>Legend</b>",
        showarrow=False,
        font=dict(size=11, color="#e5e7eb"),
        xanchor="left",
    ))
    for i, (sym, color, desc) in enumerate(legend_items):
        annotations.append(dict(
            x=legend_x, y=legend_y - 0.8 * (i + 1),
            text=f'<span style="color:{color}">{sym}</span>  {desc}',
            showarrow=False,
            font=dict(size=10, color="#d1d5db"),
            xanchor="left",
        ))
    annotations.append(dict(
        x=legend_x, y=legend_y - 0.8 * 5,
        text="● Larger = more quiz sessions",
        showarrow=False,
        font=dict(size=10, color="#9ca3af"),
        xanchor="left",
    ))

    fig.update_layout(
        plot_bgcolor="#111827",
        paper_bgcolor="#111827",
        xaxis=dict(
            visible=False,
            range=[-2.5, 14],
        ),
        yaxis=dict(
            visible=False,
            range=[-6.5, 12],
        ),
        height=900,
        margin=dict(l=10, r=10, t=30, b=10),
        annotations=annotations,
        hoverlabel=dict(
            bgcolor="#1f2937",
            bordercolor="#4b5563",
            font=dict(color="#f9fafb", size=12),
        ),
        dragmode="pan",
    )

    return fig


# ---------------------------------------------------------------------------
# Progress summary helpers
# ---------------------------------------------------------------------------

def _suggested_next(readiness_map: dict[str, float]) -> str | None:
    """Walk chains; find the first node whose prerequisite is mastered (≥80%)
    but the node itself is below mastery."""
    best_prereq_readiness = -1.0
    best_candidate = None

    for chain in _CHAINS:
        for i, node_id in enumerate(chain):
            node = _NODES[_NODE_INDEX[node_id]]
            exam_id = node["exam_id"]
            if exam_id is None:
                continue
            r = readiness_map.get(exam_id)
            # If this node is already mastered, skip to next
            if r is not None and r >= 80:
                continue
            # Check if previous node in chain is mastered (or this is the first)
            if i == 0:
                prereq_r = 100.0
            else:
                prev_node = _NODES[_NODE_INDEX[chain[i - 1]]]
                prev_exam = prev_node["exam_id"]
                prereq_r = readiness_map.get(prev_exam, 0.0) if prev_exam else 0.0
            if prereq_r >= 80 and prereq_r > best_prereq_readiness:
                best_prereq_readiness = prereq_r
                best_candidate = node["label"].replace("\n", " ")
            break  # Only suggest the *first* unmastered node per chain

    return best_candidate


def _render_progress_summary(
    readiness_map: dict[str, float],
    sessions_map: dict[str, int],
    profile: dict,
) -> None:
    st.markdown("---")
    st.subheader("My Progress")

    in_progress = sum(1 for r in readiness_map.values() if 5 <= r < 80)
    mastered = sum(1 for r in readiness_map.values() if r >= 80)
    elite = sum(1 for r in readiness_map.values() if r >= 95)
    total_sessions = sum(sessions_map.values())

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("In Progress", in_progress, help="Certs with readiness 5–79%")
    col2.metric("Mastered (80%+)", mastered, help="Certs at 80% readiness or above")
    col3.metric("Elite (95%+)", elite, help="Gold-star certs at 95%+ readiness")
    col4.metric("Total Quiz Sessions", total_sessions)

    # Suggested next cert
    suggestion = _suggested_next(readiness_map)
    if suggestion:
        st.info(f"**Suggested next cert:** {suggestion} — prerequisites are met, this is your clearest next step.")
    else:
        target = profile.get("target_exam", "")
        if target:
            st.info(f"**Keep going!** You're working toward {target}. Keep completing quizzes to unlock the next recommendation.")

    # XP level progress
    level_info = get_level_info()
    xp_to_next = level_info["xp_to_next"]
    level_title = level_info["level_title"]
    next_level_title = level_info["next_level_title"]
    progress_pct = level_info["progress_pct"]

    st.markdown(f"**XP Level:** {level_title} → {next_level_title} &nbsp; `{progress_pct:.0f}%`")
    st.progress(int(progress_pct))
    if xp_to_next > 0:
        # Rough estimate: ~100 XP/day from active study (2–3 quizzes + a lab)
        days_est = max(1, round(xp_to_next / 100))
        weeks_est = round(days_est / 7, 1)
        st.caption(
            f"{xp_to_next:,} XP to next level — "
            f"≈ {days_est} days / {weeks_est} weeks at typical pace."
        )
    else:
        st.caption("Max level reached. 🏆")


# ---------------------------------------------------------------------------
# Main render
# ---------------------------------------------------------------------------

def render(ctx: dict) -> None:
    profile = ctx["profile"]
    all_results = ctx["all_results"]

    st.subheader("Certification Skill Tree")
    render_section_note(
        "Every cert is plotted by career path and difficulty. "
        "Color shows your readiness; size shows quiz engagement. "
        "Click any tracked cert node to jump directly to that exam in the sidebar."
    )

    # ── Build live data maps ─────────────────────────────────────────────────
    readiness_map: dict[str, float] = profile.get("exam_readiness", {})

    sessions_map: dict[str, int] = defaultdict(int)
    for result in all_results:
        exam = result.get("exam", "")
        if exam:
            sessions_map[exam] += 1

    # ── Controls ─────────────────────────────────────────────────────────────
    filter_col, _, info_col = st.columns([2, 3, 3])
    with filter_col:
        selected_path = st.selectbox(
            "Career Path Filter",
            ALL_PATHS,
            key="skill_tree_path_filter",
        )
    with info_col:
        tracked_count = sum(1 for n in _NODES if n["exam_id"] in EXAM_DOMAINS)
        st.caption(
            f"{len(_NODES)} certs plotted · {tracked_count} tracked in StudyOS · "
            f"{len(_NODES) - tracked_count} external (gray border)"
        )

    # ── Determine visible nodes ───────────────────────────────────────────────
    if selected_path == "All Paths":
        visible_ids = {n["id"] for n in _NODES}
    else:
        visible_ids = {n["id"] for n in _NODES if selected_path in n["paths"]}

    # ── Render chart ─────────────────────────────────────────────────────────
    fig = _build_figure(visible_ids, readiness_map, sessions_map, selected_path)

    event = st.plotly_chart(
        fig,
        use_container_width=True,
        config={"scrollZoom": True, "displayModeBar": True, "displaylogo": False},
        on_select="rerun",
        key="skill_tree_chart",
    )

    # ── Handle node click → jump to exam ─────────────────────────────────────
    points = (event or {}).get("selection", {}).get("points", [])
    if points:
        clicked_exam_id = points[0].get("customdata", "")
        if clicked_exam_id and clicked_exam_id in EXAM_DOMAINS:
            st.session_state["sidebar_exam_select"] = clicked_exam_id
            st.success(
                f"✅ Exam set to **{clicked_exam_id}** — switch to the "
                "**Quiz Generator** tab to start practicing."
            )
        elif clicked_exam_id:
            # Node exists but exam not in EXAM_DOMAINS (external cert)
            node = next((n for n in _NODES if n["exam_id"] == clicked_exam_id), None)
            label = node["label"].replace("\n", " ") if node else clicked_exam_id
            st.info(f"**{label}** is an external certification not tracked in StudyOS yet.")

    # ── My Progress summary ───────────────────────────────────────────────────
    _render_progress_summary(readiness_map, dict(sessions_map), profile)
