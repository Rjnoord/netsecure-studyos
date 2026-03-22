from __future__ import annotations

from datetime import date, datetime, timedelta
import json
import sqlite3
from contextlib import contextmanager
from copy import deepcopy
import os
from pathlib import Path
import re
from uuid import uuid4

import pandas as pd

from exams import EXAM_DOMAINS


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
RESULTS_DIR = DATA_DIR / "results"
EXPORTS_DIR = DATA_DIR / "exports"
SESSIONS_DIR = DATA_DIR / "sessions"
PROFILE_PATH = DATA_DIR / "user_profile.json"
MOBILE_SYNC_PATH = DATA_DIR / "mobile_sync.json"
MOBILE_APP_SYNC_PATH = BASE_DIR / "mobile_app" / "data" / "mobile_sync.json"
DB_PATH = DATA_DIR / "netsecure.db"
_MEMORY_STATE_KEY = "_netsecure_storage_memory"
_PERSISTENCE_WARNING: str | None = None
_CLOUD_ENVIRONMENT_KEYS = {
    "STREAMLIT_RUNTIME_ENVIRONMENT": "community_cloud",
    "STREAMLIT_SHARING_MODE": "streamlit_app",
}

_CREATE_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS users (
    id   INTEGER PRIMARY KEY CHECK (id = 1),
    profile_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS results (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    submitted_at TEXT,
    exam         TEXT,
    result_json  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sessions (
    session_id   TEXT PRIMARY KEY,
    started_at   TEXT,
    session_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS lab_progress (
    lab_id        TEXT PRIMARY KEY,
    user_id       INTEGER NOT NULL DEFAULT 1,
    progress_json TEXT NOT NULL,
    updated_at    TEXT
);

CREATE TABLE IF NOT EXISTS mobile_sync (
    id         INTEGER PRIMARY KEY CHECK (id = 1),
    sync_json  TEXT NOT NULL,
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS xp_log (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id   INTEGER NOT NULL DEFAULT 1,
    amount    INTEGER NOT NULL,
    reason    TEXT NOT NULL,
    logged_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS streaks (
    user_id         INTEGER PRIMARY KEY DEFAULT 1,
    current_streak  INTEGER NOT NULL DEFAULT 0,
    longest_streak  INTEGER NOT NULL DEFAULT 0,
    last_study_date TEXT
);

CREATE TABLE IF NOT EXISTS badges (
    badge_id    TEXT NOT NULL,
    user_id     INTEGER NOT NULL DEFAULT 1,
    badge_name  TEXT NOT NULL,
    description TEXT NOT NULL,
    earned_at   TEXT NOT NULL,
    PRIMARY KEY (badge_id, user_id)
);
"""

LEVEL_THRESHOLDS: list[tuple[int, str]] = [
    (0, "Novice"),
    (500, "Technician"),
    (1500, "Associate"),
    (3000, "Engineer"),
    (6000, "Senior Engineer"),
    (10000, "Architect"),
    (15000, "Senior Architect"),
    (25000, "Expert"),
    (40000, "Elite"),
    (60000, "Legend"),
]


# ---------------------------------------------------------------------------
# In-memory fallback state (cloud mode / write-protected environments)
# ---------------------------------------------------------------------------

def _memory_state() -> dict:
    try:
        import streamlit as st
        from streamlit import runtime

        if runtime.exists() and hasattr(st, "session_state"):
            if _MEMORY_STATE_KEY not in st.session_state:
                st.session_state[_MEMORY_STATE_KEY] = {}
            return st.session_state[_MEMORY_STATE_KEY]
    except Exception:
        pass
    global _FALLBACK_MEMORY_STATE
    try:
        return _FALLBACK_MEMORY_STATE
    except NameError:
        _FALLBACK_MEMORY_STATE = {}
        return _FALLBACK_MEMORY_STATE


def _ensure_memory_defaults() -> dict:
    state = _memory_state()
    state.setdefault("profile", deepcopy(default_profile()))
    state.setdefault("results", [])
    state.setdefault("sessions", {})
    state.setdefault("mobile_sync", None)
    state.setdefault("xp_total", 0)
    state.setdefault("xp_log", [])
    state.setdefault("streak", {"current_streak": 0, "longest_streak": 0, "last_study_date": None})
    state.setdefault("badges", [])
    state.setdefault("_streak_updated_date", None)
    return state


def _set_persistence_warning(message: str) -> None:
    global _PERSISTENCE_WARNING
    _PERSISTENCE_WARNING = message


# ---------------------------------------------------------------------------
# Environment detection
# ---------------------------------------------------------------------------

def is_cloud_mode() -> bool:
    if os.getenv("NETSECURE_STUDYOS_FORCE_LOCAL_PERSISTENCE", "").lower() in {"1", "true", "yes"}:
        return False
    if os.getenv("NETSECURE_STUDYOS_FORCE_CLOUD_MODE", "").lower() in {"1", "true", "yes"}:
        return True
    return any(os.getenv(key) == value for key, value in _CLOUD_ENVIRONMENT_KEYS.items())


def is_file_persistence_enabled() -> bool:
    return not is_cloud_mode() and _PERSISTENCE_WARNING is None


def persistence_status() -> tuple[str, str | None]:
    if is_cloud_mode():
        return (
            "cloud-memory",
            "Running in Streamlit Community Cloud demo mode. Data stays in memory for the current session.",
        )
    if _PERSISTENCE_WARNING:
        return ("memory-fallback", _PERSISTENCE_WARNING)
    return ("local-sqlite", None)


# ---------------------------------------------------------------------------
# SQLite helpers
# ---------------------------------------------------------------------------

@contextmanager
def _db_connection():
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _init_db() -> None:
    with _db_connection() as conn:
        conn.executescript(_CREATE_TABLES_SQL)


# ---------------------------------------------------------------------------
# Export helpers (still write to filesystem — not stored in SQLite)
# ---------------------------------------------------------------------------

def _safe_filename(filename: str, suffix: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9._-]", "_", filename).strip("._")
    if not cleaned:
        cleaned = f"export{suffix}"
    if not cleaned.endswith(suffix):
        cleaned = f"{cleaned}{suffix}"
    return cleaned


def _atomic_write_json(destination: Path, payload: dict) -> None:
    temp_path = destination.with_suffix(destination.suffix + ".tmp")
    with temp_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
    temp_path.replace(destination)


def _atomic_write_text(destination: Path, content: str) -> None:
    temp_path = destination.with_suffix(destination.suffix + ".tmp")
    with temp_path.open("w", encoding="utf-8") as handle:
        handle.write(content)
    temp_path.replace(destination)


# ---------------------------------------------------------------------------
# Profile defaults and merging
# ---------------------------------------------------------------------------

def default_profile() -> dict:
    return {
        "name": "Student",
        "exam_readiness": {},
        "updated_at": None,
        "onboarding_complete": False,
        "target_exam": None,
        "target_date": None,
        "weekly_study_hours": 6,
        "domain_self_ratings": {exam: {domain: 3 for domain in domains} for exam, domains in EXAM_DOMAINS.items()},
        "lab_progress": {},
        "auth": {
            "passcode_hash": None,
            "passcode_salt": None,
            "failed_attempts": 0,
            "lockout_until": None,
            "updated_at": None,
        },
        "links": {
            "public_app_url": None,
            "mobile_app_url": None,
        },
    }


def _deep_merge(base: dict, override: dict) -> dict:
    merged = deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


# ---------------------------------------------------------------------------
# Storage initialisation
# ---------------------------------------------------------------------------

def ensure_storage() -> None:
    state = _ensure_memory_defaults()
    if is_cloud_mode() or _PERSISTENCE_WARNING:
        return
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
        MOBILE_APP_SYNC_PATH.parent.mkdir(parents=True, exist_ok=True)
        _init_db()
    except (OSError, sqlite3.Error) as exc:
        _set_persistence_warning(
            f"Local persistence is unavailable ({exc}). Falling back to in-memory session storage."
        )


# ---------------------------------------------------------------------------
# User profile
# ---------------------------------------------------------------------------

def load_user_profile() -> dict:
    ensure_storage()
    state = _ensure_memory_defaults()
    profile = state["profile"]
    if is_file_persistence_enabled():
        try:
            with _db_connection() as conn:
                row = conn.execute("SELECT profile_json FROM users WHERE id = 1").fetchone()
            if row:
                profile = json.loads(row["profile_json"])
        except (sqlite3.Error, json.JSONDecodeError):
            profile = state["profile"]
    normalized = _deep_merge(default_profile(), profile)
    state["profile"] = deepcopy(normalized)
    if is_file_persistence_enabled() and normalized != profile:
        save_user_profile(normalized)
    return normalized


def save_user_profile(profile: dict) -> None:
    ensure_storage()
    normalized = _deep_merge(default_profile(), profile)
    state = _ensure_memory_defaults()
    state["profile"] = deepcopy(normalized)
    if not is_file_persistence_enabled():
        return
    try:
        payload = json.dumps(normalized)
        with _db_connection() as conn:
            conn.execute(
                "INSERT INTO users (id, profile_json) VALUES (1, ?)"
                " ON CONFLICT(id) DO UPDATE SET profile_json = excluded.profile_json",
                (payload,),
            )
    except (sqlite3.Error, OSError) as exc:
        _set_persistence_warning(
            f"Profile changes could not be written to disk ({exc}). The app will keep them in memory for this session."
        )


# ---------------------------------------------------------------------------
# Quiz results
# ---------------------------------------------------------------------------

def load_results(exam: str | None = None) -> list[dict]:
    ensure_storage()
    state = _ensure_memory_defaults()
    if is_file_persistence_enabled():
        results = []
        try:
            with _db_connection() as conn:
                if exam:
                    rows = conn.execute(
                        "SELECT result_json FROM results WHERE exam = ? ORDER BY submitted_at",
                        (exam,),
                    ).fetchall()
                else:
                    rows = conn.execute(
                        "SELECT result_json FROM results ORDER BY submitted_at"
                    ).fetchall()
            for row in rows:
                try:
                    results.append(json.loads(row["result_json"]))
                except json.JSONDecodeError:
                    continue
        except sqlite3.Error:
            results = []
        state["results"] = deepcopy(results)
    else:
        results = deepcopy(state["results"])
        if exam:
            results = [r for r in results if r.get("exam") == exam]
    results.sort(key=lambda item: item.get("submitted_at", ""))
    return results


def save_quiz_result(result: dict) -> Path | None:
    ensure_storage()
    state = _ensure_memory_defaults()
    state["results"].append(deepcopy(result))
    if not is_file_persistence_enabled():
        return None
    try:
        with _db_connection() as conn:
            conn.execute(
                "INSERT INTO results (submitted_at, exam, result_json) VALUES (?, ?, ?)",
                (result.get("submitted_at"), result.get("exam"), json.dumps(result)),
            )
    except (sqlite3.Error, OSError) as exc:
        _set_persistence_warning(
            f"Quiz results could not be written to disk ({exc}). They remain available in memory for this session."
        )
        return None
    return DB_PATH


# ---------------------------------------------------------------------------
# File-based exports (CSV / Markdown) — unchanged from original
# ---------------------------------------------------------------------------

def export_dataframe(frame: pd.DataFrame, filename: str) -> Path | None:
    ensure_storage()
    if not is_file_persistence_enabled():
        return None
    destination = EXPORTS_DIR / _safe_filename(filename, ".csv")
    try:
        frame.to_csv(destination, index=False)
    except OSError as exc:
        _set_persistence_warning(
            f"Exports could not be written to disk ({exc}). Export files are unavailable in the current session."
        )
        return None
    return destination


def export_markdown(content: str, filename: str) -> Path | None:
    ensure_storage()
    if not is_file_persistence_enabled():
        return None
    destination = EXPORTS_DIR / _safe_filename(filename, ".md")
    try:
        _atomic_write_text(destination, content)
    except OSError as exc:
        _set_persistence_warning(
            f"Markdown export could not be written to disk ({exc}). Export files are unavailable in the current session."
        )
        return None
    return destination


# ---------------------------------------------------------------------------
# Active sessions
# ---------------------------------------------------------------------------

def save_active_session(session: dict) -> Path | None:
    ensure_storage()
    state = _ensure_memory_defaults()
    state["sessions"][session["session_id"]] = deepcopy(session)
    if not is_file_persistence_enabled():
        return None
    try:
        with _db_connection() as conn:
            conn.execute(
                "INSERT INTO sessions (session_id, started_at, session_json) VALUES (?, ?, ?)"
                " ON CONFLICT(session_id) DO UPDATE SET"
                "   started_at = excluded.started_at,"
                "   session_json = excluded.session_json",
                (session["session_id"], session.get("started_at"), json.dumps(session)),
            )
    except (sqlite3.Error, OSError) as exc:
        _set_persistence_warning(
            f"Session progress could not be written to disk ({exc}). Resume state will stay in memory for this session."
        )
        return None
    return DB_PATH


def load_active_sessions() -> list[dict]:
    ensure_storage()
    state = _ensure_memory_defaults()
    if is_file_persistence_enabled():
        sessions = []
        try:
            with _db_connection() as conn:
                rows = conn.execute(
                    "SELECT session_json FROM sessions ORDER BY started_at"
                ).fetchall()
            for row in rows:
                try:
                    session = json.loads(row["session_json"])
                    if session.get("session_id"):
                        sessions.append(session)
                except json.JSONDecodeError:
                    continue
        except sqlite3.Error:
            sessions = []
        state["sessions"] = {s["session_id"]: deepcopy(s) for s in sessions}
    else:
        sessions = [deepcopy(s) for s in state["sessions"].values()]
    sessions.sort(key=lambda item: item.get("started_at", ""))
    return sessions


def delete_active_session(session_id: str) -> None:
    state = _ensure_memory_defaults()
    state["sessions"].pop(session_id, None)
    if not is_file_persistence_enabled():
        return
    try:
        with _db_connection() as conn:
            conn.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
    except (sqlite3.Error, OSError) as exc:
        _set_persistence_warning(
            f"Saved session cleanup failed ({exc}). The current session will continue in memory."
        )


# ---------------------------------------------------------------------------
# Mobile sync
# ---------------------------------------------------------------------------

def save_mobile_sync(payload: dict) -> None:
    ensure_storage()
    state = _ensure_memory_defaults()
    state["mobile_sync"] = deepcopy(payload)
    if not is_file_persistence_enabled():
        return
    sync_json = json.dumps(payload)
    try:
        with _db_connection() as conn:
            conn.execute(
                "INSERT INTO mobile_sync (id, sync_json, updated_at) VALUES (1, ?, datetime('now'))"
                " ON CONFLICT(id) DO UPDATE SET"
                "   sync_json = excluded.sync_json,"
                "   updated_at = excluded.updated_at",
                (sync_json,),
            )
    except (sqlite3.Error, OSError) as exc:
        _set_persistence_warning(
            f"Mobile sync data could not be written to disk ({exc}). The current session will continue without file sync."
        )
        return
    # Also write JSON file for mobile app compatibility
    try:
        _atomic_write_json(MOBILE_APP_SYNC_PATH, payload)
    except OSError:
        pass  # Mobile app JSON is best-effort; SQLite write already succeeded


# ---------------------------------------------------------------------------
# Analytics helper
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# XP system
# ---------------------------------------------------------------------------

def get_xp(user_id: int = 1) -> int:
    """Return the current total XP for the user."""
    state = _ensure_memory_defaults()
    if is_file_persistence_enabled():
        try:
            with _db_connection() as conn:
                row = conn.execute(
                    "SELECT COALESCE(SUM(amount), 0) AS total FROM xp_log WHERE user_id = ?",
                    (user_id,),
                ).fetchone()
            return int(row["total"]) if row else 0
        except sqlite3.Error:
            pass
    return int(state.get("xp_total", 0))


def add_xp(amount: int, reason: str, user_id: int = 1) -> int:
    """Add XP and log the reason. Returns the new running total."""
    state = _ensure_memory_defaults()
    now = datetime.now().isoformat()
    if is_file_persistence_enabled():
        try:
            with _db_connection() as conn:
                conn.execute(
                    "INSERT INTO xp_log (user_id, amount, reason, logged_at) VALUES (?, ?, ?, ?)",
                    (user_id, amount, reason, now),
                )
        except (sqlite3.Error, OSError):
            pass
    state["xp_total"] = state.get("xp_total", 0) + amount
    state["xp_log"].append({"amount": amount, "reason": reason, "logged_at": now})
    return int(state["xp_total"])


# ---------------------------------------------------------------------------
# Streak system
# ---------------------------------------------------------------------------

def get_streak(user_id: int = 1) -> dict:
    """Return current streak data: current_streak, longest_streak, last_study_date."""
    state = _ensure_memory_defaults()
    if is_file_persistence_enabled():
        try:
            with _db_connection() as conn:
                row = conn.execute(
                    "SELECT current_streak, longest_streak, last_study_date"
                    " FROM streaks WHERE user_id = ?",
                    (user_id,),
                ).fetchone()
            if row:
                return {
                    "current_streak": row["current_streak"],
                    "longest_streak": row["longest_streak"],
                    "last_study_date": row["last_study_date"],
                }
        except sqlite3.Error:
            pass
    return dict(state.get("streak", {"current_streak": 0, "longest_streak": 0, "last_study_date": None}))


def update_streak(user_id: int = 1) -> dict:
    """Check if the user studied today, then increment or reset streak and award bonuses.

    Guards against double-awarding within the same session using in-memory state.
    """
    today = date.today().isoformat()
    state = _ensure_memory_defaults()

    if state.get("_streak_updated_date") == today:
        return get_streak(user_id)
    state["_streak_updated_date"] = today

    streak = get_streak(user_id)
    last_study = streak.get("last_study_date")
    current = streak.get("current_streak", 0)
    longest = streak.get("longest_streak", 0)

    if last_study == today:
        return streak

    yesterday = (date.today() - timedelta(days=1)).isoformat()
    current = current + 1 if last_study == yesterday else 1
    longest = max(longest, current)

    add_xp(25, "Daily login", user_id)

    if current == 7:
        add_xp(200, "7-day streak bonus", user_id)
        award_badge("on_fire", "On Fire", "Maintained a 7-day study streak", user_id)
    if current == 30:
        add_xp(500, "30-day streak bonus", user_id)
        award_badge("unstoppable", "Unstoppable", "Maintained a 30-day study streak", user_id)

    if is_file_persistence_enabled():
        try:
            with _db_connection() as conn:
                conn.execute(
                    "INSERT INTO streaks (user_id, current_streak, longest_streak, last_study_date)"
                    " VALUES (?, ?, ?, ?)"
                    " ON CONFLICT(user_id) DO UPDATE SET"
                    "   current_streak = excluded.current_streak,"
                    "   longest_streak = excluded.longest_streak,"
                    "   last_study_date = excluded.last_study_date",
                    (user_id, current, longest, today),
                )
        except (sqlite3.Error, OSError):
            pass

    updated = {"current_streak": current, "longest_streak": longest, "last_study_date": today}
    state["streak"] = updated
    return updated


# ---------------------------------------------------------------------------
# Badge system
# ---------------------------------------------------------------------------

def get_badges(user_id: int = 1) -> list[dict]:
    """Return all earned badges for the user."""
    state = _ensure_memory_defaults()
    if is_file_persistence_enabled():
        try:
            with _db_connection() as conn:
                rows = conn.execute(
                    "SELECT badge_id, badge_name, description, earned_at"
                    " FROM badges WHERE user_id = ? ORDER BY earned_at",
                    (user_id,),
                ).fetchall()
            return [dict(r) for r in rows]
        except sqlite3.Error:
            pass
    return [dict(b) for b in state.get("badges", [])]


def award_badge(badge_id: str, badge_name: str, description: str, user_id: int = 1) -> bool:
    """Save a badge if not already earned. Returns True if newly awarded."""
    existing = {b["badge_id"] for b in get_badges(user_id)}
    if badge_id in existing:
        return False
    state = _ensure_memory_defaults()
    now = datetime.now().isoformat()
    if is_file_persistence_enabled():
        try:
            with _db_connection() as conn:
                conn.execute(
                    "INSERT OR IGNORE INTO badges"
                    " (badge_id, user_id, badge_name, description, earned_at)"
                    " VALUES (?, ?, ?, ?, ?)",
                    (badge_id, user_id, badge_name, description, now),
                )
        except (sqlite3.Error, OSError):
            pass
    state["badges"].append(
        {"badge_id": badge_id, "badge_name": badge_name, "description": description, "earned_at": now}
    )
    return True


# ---------------------------------------------------------------------------
# Level info
# ---------------------------------------------------------------------------

def get_level_info(user_id: int = 1) -> dict:
    """Return current level title, XP progress, and percentage toward next level."""
    xp = get_xp(user_id)
    level_index = 0
    for i, (threshold, _) in enumerate(LEVEL_THRESHOLDS):
        if xp >= threshold:
            level_index = i

    current_threshold, level_title = LEVEL_THRESHOLDS[level_index]

    if level_index + 1 < len(LEVEL_THRESHOLDS):
        next_threshold, next_title = LEVEL_THRESHOLDS[level_index + 1]
        xp_in_level = xp - current_threshold
        xp_for_level = next_threshold - current_threshold
        progress_pct = min(100.0, round((xp_in_level / xp_for_level) * 100, 1))
        xp_to_next = next_threshold - xp
    else:
        next_threshold = LEVEL_THRESHOLDS[-1][0]
        next_title = level_title
        xp_to_next = 0
        progress_pct = 100.0

    return {
        "level_title": level_title,
        "level_index": level_index,
        "current_xp": xp,
        "next_level_xp": next_threshold,
        "next_level_title": next_title,
        "xp_to_next": xp_to_next,
        "progress_pct": progress_pct,
    }


# ---------------------------------------------------------------------------
# Analytics helper
# ---------------------------------------------------------------------------

def build_quiz_history_frame(results: list[dict]) -> pd.DataFrame:
    columns = [
        "submitted_at",
        "exam",
        "mode",
        "question_count",
        "correct_count",
        "score_pct",
        "timed_mode",
        "minutes_allocated",
        "elapsed_seconds",
    ]
    rows = []
    for result in results:
        rows.append(
            {
                "submitted_at": result.get("submitted_at"),
                "exam": result.get("exam"),
                "mode": result.get("mode"),
                "question_count": result.get("question_count"),
                "correct_count": result.get("correct_count"),
                "score_pct": result.get("score_pct"),
                "timed_mode": result.get("timed_mode"),
                "minutes_allocated": result.get("minutes_allocated"),
                "elapsed_seconds": result.get("elapsed_seconds"),
            }
        )
    return pd.DataFrame(rows, columns=columns)
