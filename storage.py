from __future__ import annotations

import json
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
_MEMORY_STATE_KEY = "_netsecure_storage_memory"
_PERSISTENCE_WARNING: str | None = None
_CLOUD_ENVIRONMENT_KEYS = {
    "STREAMLIT_RUNTIME_ENVIRONMENT": "community_cloud",
    "STREAMLIT_SHARING_MODE": "streamlit_app",
}


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
    return state


def _set_persistence_warning(message: str) -> None:
    global _PERSISTENCE_WARNING
    _PERSISTENCE_WARNING = message


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
            "Running in Streamlit Community Cloud demo mode. JSON files are not written; data stays in memory for the current session.",
        )
    if _PERSISTENCE_WARNING:
        return ("memory-fallback", _PERSISTENCE_WARNING)
    return ("local-files", None)


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


def ensure_storage() -> None:
    state = _ensure_memory_defaults()
    if is_cloud_mode() or _PERSISTENCE_WARNING:
        return
    try:
        RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
        SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
        MOBILE_APP_SYNC_PATH.parent.mkdir(parents=True, exist_ok=True)
        if not PROFILE_PATH.exists():
            _atomic_write_json(PROFILE_PATH, state["profile"])
    except OSError as exc:
        _set_persistence_warning(
            f"Local persistence is unavailable ({exc}). Falling back to in-memory session storage."
        )


def load_user_profile() -> dict:
    ensure_storage()
    state = _ensure_memory_defaults()
    profile = state["profile"]
    if is_file_persistence_enabled() and PROFILE_PATH.exists():
        try:
            with PROFILE_PATH.open("r", encoding="utf-8") as handle:
                profile = json.load(handle)
        except (json.JSONDecodeError, OSError):
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
        _atomic_write_json(PROFILE_PATH, normalized)
    except OSError as exc:
        _set_persistence_warning(
            f"Profile changes could not be written to disk ({exc}). The app will keep them in memory for this session."
        )


def load_results(exam: str | None = None) -> list[dict]:
    ensure_storage()
    state = _ensure_memory_defaults()
    if is_file_persistence_enabled():
        results = []
        for file_path in sorted(RESULTS_DIR.glob("*.json")):
            try:
                with file_path.open("r", encoding="utf-8") as handle:
                    payload = json.load(handle)
                if exam and payload.get("exam") != exam:
                    continue
                results.append(payload)
            except (json.JSONDecodeError, OSError):
                continue
        state["results"] = deepcopy(results)
    else:
        results = deepcopy(state["results"])
        if exam:
            results = [payload for payload in results if payload.get("exam") == exam]
    results.sort(key=lambda item: item.get("submitted_at", ""))
    return results


def save_quiz_result(result: dict) -> Path | None:
    ensure_storage()
    state = _ensure_memory_defaults()
    state["results"].append(deepcopy(result))
    stamp = result.get("submitted_at", "").replace(":", "-")
    filename = f"{stamp}_{uuid4().hex[:8]}.json"
    destination = RESULTS_DIR / filename
    if not is_file_persistence_enabled():
        return None
    try:
        _atomic_write_json(destination, result)
    except OSError as exc:
        _set_persistence_warning(
            f"Quiz results could not be written to disk ({exc}). They remain available in memory for this session."
        )
        return None
    return destination


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


def save_active_session(session: dict) -> Path | None:
    ensure_storage()
    state = _ensure_memory_defaults()
    state["sessions"][session["session_id"]] = deepcopy(session)
    destination = SESSIONS_DIR / f"{session['session_id']}.json"
    if not is_file_persistence_enabled():
        return None
    try:
        _atomic_write_json(destination, session)
    except OSError as exc:
        _set_persistence_warning(
            f"Session progress could not be written to disk ({exc}). Resume state will stay in memory for this session."
        )
        return None
    return destination


def load_active_sessions() -> list[dict]:
    ensure_storage()
    state = _ensure_memory_defaults()
    if is_file_persistence_enabled():
        sessions = []
        for file_path in sorted(SESSIONS_DIR.glob("*.json")):
            try:
                with file_path.open("r", encoding="utf-8") as handle:
                    sessions.append(json.load(handle))
            except (json.JSONDecodeError, OSError):
                continue
        state["sessions"] = {session["session_id"]: deepcopy(session) for session in sessions if session.get("session_id")}
    else:
        sessions = [deepcopy(session) for session in state["sessions"].values()]
    sessions.sort(key=lambda item: item.get("started_at", ""))
    return sessions


def delete_active_session(session_id: str) -> None:
    state = _ensure_memory_defaults()
    state["sessions"].pop(session_id, None)
    destination = SESSIONS_DIR / f"{session_id}.json"
    if is_file_persistence_enabled() and destination.exists():
        try:
            destination.unlink()
        except OSError as exc:
            _set_persistence_warning(
                f"Saved session cleanup failed ({exc}). The current session will continue in memory."
            )


def save_mobile_sync(payload: dict) -> None:
    ensure_storage()
    state = _ensure_memory_defaults()
    state["mobile_sync"] = deepcopy(payload)
    if not is_file_persistence_enabled():
        return
    for destination in [MOBILE_SYNC_PATH, MOBILE_APP_SYNC_PATH]:
        try:
            _atomic_write_json(destination, payload)
        except OSError as exc:
            _set_persistence_warning(
                f"Mobile sync data could not be written to disk ({exc}). The current session will continue without file sync."
            )
            return


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
