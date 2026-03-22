#!/usr/bin/env python3
"""
migrate_to_sqlite.py
--------------------
One-time migration from the legacy per-file JSON layout to netsecure.db.

Layout expected:
  data/user_profile.json          -> users table
  data/results/*.json             -> results table
  data/sessions/*.json            -> sessions table
  data/mobile_sync.json           -> mobile_sync table

Run once from the project root:
    python migrate_to_sqlite.py

Safe to re-run: existing rows are skipped (INSERT OR IGNORE / upsert).
"""

from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "netsecure.db"

PROFILE_PATH = DATA_DIR / "user_profile.json"
RESULTS_DIR = DATA_DIR / "results"
SESSIONS_DIR = DATA_DIR / "sessions"
MOBILE_SYNC_PATH = DATA_DIR / "mobile_sync.json"

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
"""


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def _init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(_CREATE_TABLES_SQL)
    conn.commit()
    print(f"  [db] Schema ensured in {DB_PATH}")


def _load_json(path: Path) -> dict | list | None:
    try:
        with path.open("r", encoding="utf-8") as fh:
            return json.load(fh)
    except (json.JSONDecodeError, OSError) as exc:
        print(f"  [warn] Could not read {path}: {exc}")
        return None


def migrate_profile(conn: sqlite3.Connection) -> None:
    print("\n--- User profile ---")
    if not PROFILE_PATH.exists():
        print(f"  [skip] {PROFILE_PATH} not found")
        return
    profile = _load_json(PROFILE_PATH)
    if profile is None:
        return

    existing = conn.execute("SELECT id FROM users WHERE id = 1").fetchone()
    if existing:
        # Upsert: overwrite with the JSON file's data (it is the source of truth)
        conn.execute(
            "UPDATE users SET profile_json = ? WHERE id = 1",
            (json.dumps(profile),),
        )
        conn.commit()
        print(f"  [updated] user profile from {PROFILE_PATH}")
    else:
        conn.execute(
            "INSERT INTO users (id, profile_json) VALUES (1, ?)",
            (json.dumps(profile),),
        )
        conn.commit()
        print(f"  [inserted] user profile from {PROFILE_PATH}")

    # Migrate embedded lab_progress into the lab_progress table
    lab_progress: dict = profile.get("lab_progress", {})
    if lab_progress:
        inserted = 0
        for lab_id, progress in lab_progress.items():
            progress_data = progress if isinstance(progress, dict) else {"status": progress}
            conn.execute(
                "INSERT OR IGNORE INTO lab_progress (lab_id, user_id, progress_json, updated_at)"
                " VALUES (?, 1, ?, datetime('now'))",
                (lab_id, json.dumps(progress_data)),
            )
            inserted += 1
        conn.commit()
        print(f"  [lab_progress] {inserted} lab(s) migrated")
    else:
        print("  [lab_progress] none found in profile")


def migrate_results(conn: sqlite3.Connection) -> None:
    print("\n--- Quiz results ---")
    if not RESULTS_DIR.exists():
        print(f"  [skip] {RESULTS_DIR} not found")
        return

    json_files = sorted(RESULTS_DIR.glob("*.json"))
    if not json_files:
        print("  [skip] no result JSON files found")
        return

    inserted = skipped = 0
    for file_path in json_files:
        result = _load_json(file_path)
        if result is None:
            skipped += 1
            continue
        # Deduplicate by (submitted_at, exam) – only insert if not already present
        existing = conn.execute(
            "SELECT id FROM results WHERE submitted_at = ? AND exam = ?",
            (result.get("submitted_at"), result.get("exam")),
        ).fetchone()
        if existing:
            skipped += 1
            continue
        conn.execute(
            "INSERT INTO results (submitted_at, exam, result_json) VALUES (?, ?, ?)",
            (result.get("submitted_at"), result.get("exam"), json.dumps(result)),
        )
        inserted += 1

    conn.commit()
    print(f"  [results] {inserted} inserted, {skipped} skipped (already present or unreadable)")


def migrate_sessions(conn: sqlite3.Connection) -> None:
    print("\n--- Active sessions ---")
    if not SESSIONS_DIR.exists():
        print(f"  [skip] {SESSIONS_DIR} not found")
        return

    json_files = sorted(SESSIONS_DIR.glob("*.json"))
    if not json_files:
        print("  [skip] no session JSON files found")
        return

    inserted = skipped = 0
    for file_path in json_files:
        session = _load_json(file_path)
        if session is None or not session.get("session_id"):
            skipped += 1
            continue
        conn.execute(
            "INSERT OR IGNORE INTO sessions (session_id, started_at, session_json)"
            " VALUES (?, ?, ?)",
            (session["session_id"], session.get("started_at"), json.dumps(session)),
        )
        if conn.execute(
            "SELECT changes()"
        ).fetchone()[0]:
            inserted += 1
        else:
            skipped += 1

    conn.commit()
    print(f"  [sessions] {inserted} inserted, {skipped} skipped (already present or invalid)")


def migrate_mobile_sync(conn: sqlite3.Connection) -> None:
    print("\n--- Mobile sync ---")
    if not MOBILE_SYNC_PATH.exists():
        print(f"  [skip] {MOBILE_SYNC_PATH} not found")
        return
    payload = _load_json(MOBILE_SYNC_PATH)
    if payload is None:
        return

    existing = conn.execute("SELECT id FROM mobile_sync WHERE id = 1").fetchone()
    if existing:
        conn.execute(
            "UPDATE mobile_sync SET sync_json = ?, updated_at = datetime('now') WHERE id = 1",
            (json.dumps(payload),),
        )
        print(f"  [updated] mobile_sync from {MOBILE_SYNC_PATH}")
    else:
        conn.execute(
            "INSERT INTO mobile_sync (id, sync_json, updated_at) VALUES (1, ?, datetime('now'))",
            (json.dumps(payload),),
        )
        print(f"  [inserted] mobile_sync from {MOBILE_SYNC_PATH}")
    conn.commit()


def summarise(conn: sqlite3.Connection) -> None:
    print("\n--- Summary ---")
    tables = ["users", "results", "sessions", "lab_progress", "mobile_sync"]
    for table in tables:
        count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"  {table:<15} {count:>5} row(s)")
    print(f"\n  Database: {DB_PATH}")


def main() -> None:
    print("NetSecure StudyOS — JSON → SQLite migration")
    print("=" * 44)

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    conn = _connect()
    try:
        _init_db(conn)
        migrate_profile(conn)
        migrate_results(conn)
        migrate_sessions(conn)
        migrate_mobile_sync(conn)
        summarise(conn)
    except sqlite3.Error as exc:
        print(f"\n[error] SQLite error: {exc}", file=sys.stderr)
        conn.rollback()
        sys.exit(1)
    finally:
        conn.close()

    print("\nMigration complete.")


if __name__ == "__main__":
    main()
