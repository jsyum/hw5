"""Database access for the Campus Customs MCP server.

Every tool goes through this module so the server only ever works on the
working copy of the database (data/campus_customs_new.db). The original
data/campus_customs.db is only ever opened read-only, as the source for
reset_working_db().

The working copy also carries a few board tables that are not in the source
schema (payment_requests, board_posts) plus guard triggers. They are created
by ensure_board_schema() after every reset. See output/harness.md.
"""

from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Iterator

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ORIGINAL_DB = PROJECT_ROOT / "data" / "campus_customs.db"
DEFAULT_WORKING_DB = PROJECT_ROOT / "data" / "campus_customs_new.db"

# The MCP configuration (.mcp.json) sets CAMPUS_CUSTOMS_DB explicitly to the
# working copy. Without it, the same working copy is used by default. Either
# way the original data/campus_customs.db is never written.
WORKING_DB = Path(os.environ.get("CAMPUS_CUSTOMS_DB", DEFAULT_WORKING_DB)).resolve()
if WORKING_DB == ORIGINAL_DB.resolve():
    raise RuntimeError("CAMPUS_CUSTOMS_DB points at the original database; it must point at the working copy.")

# Only human approval paths may approve a payment request. No MCP tool uses these.
HUMAN_DECISION_SOURCES = ("human_cli", "human_dashboard")

BOARD_SCHEMA = f"""
CREATE TABLE IF NOT EXISTS payment_requests (
    id INTEGER PRIMARY KEY,
    kind TEXT NOT NULL CHECK (kind IN ('invoice', 'rent', 'purchase_order')),
    ref_id INTEGER,
    ticket_id INTEGER REFERENCES tickets(id),
    vendor_id INTEGER REFERENCES vendors(id),
    sku TEXT,
    size TEXT,
    qty INTEGER,
    amount REAL NOT NULL CHECK (amount > 0),
    account TEXT NOT NULL REFERENCES cash_accounts(name),
    requested_by TEXT NOT NULL,
    reason TEXT,
    status TEXT NOT NULL CHECK (status IN ('pending_approval', 'approved', 'paid', 'rejected')),
    decided_by TEXT,
    decision_source TEXT,
    decision_note TEXT,
    decided_at TEXT,
    payment_id INTEGER REFERENCES payments(id),
    expected_arrival TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS board_posts (
    id INTEGER PRIMARY KEY,
    ticket_id INTEGER NOT NULL REFERENCES tickets(id),
    kind TEXT NOT NULL CHECK (kind IN ('draft', 'note', 'status_change')),
    author_agent TEXT NOT NULL,
    recipient TEXT,
    recipient_type TEXT,
    subject TEXT,
    body TEXT NOT NULL,
    status TEXT,
    created_at TEXT NOT NULL
);

-- Guard triggers are dropped and recreated on every ensure, so rule updates apply to existing copies.
DROP TRIGGER IF EXISTS guard_request_starts_pending;
DROP TRIGGER IF EXISTS guard_request_approval_is_human;
DROP TRIGGER IF EXISTS guard_request_paid_after_approval;
DROP TRIGGER IF EXISTS guard_payment_requires_human_approval;
DROP TRIGGER IF EXISTS guard_cash_non_negative;

-- New payment requests always start pending. Nothing can insert an approved one.
CREATE TRIGGER guard_request_starts_pending
BEFORE INSERT ON payment_requests
WHEN NEW.status <> 'pending_approval' OR NEW.decided_by IS NOT NULL
BEGIN
    SELECT RAISE(ABORT, 'payment requests must be created as pending_approval');
END;

-- A request can only become approved from pending, with a named human approver.
CREATE TRIGGER guard_request_approval_is_human
BEFORE UPDATE OF status ON payment_requests
WHEN NEW.status = 'approved' AND (
    OLD.status <> 'pending_approval'
    OR NEW.decided_by IS NULL OR trim(NEW.decided_by) = ''
    OR NEW.decision_source NOT IN ({", ".join(f"'{s}'" for s in HUMAN_DECISION_SOURCES)})
)
BEGIN
    SELECT RAISE(ABORT, 'payment approval must come from a human approver');
END;

-- A paid request must have been approved first.
CREATE TRIGGER guard_request_paid_after_approval
BEFORE UPDATE OF status ON payment_requests
WHEN NEW.status = 'paid' AND OLD.status <> 'approved'
BEGIN
    SELECT RAISE(ABORT, 'a payment request must be approved before it is paid');
END;

-- No row may enter payments unless a matching request was approved by a human.
CREATE TRIGGER guard_payment_requires_human_approval
BEFORE INSERT ON payments
WHEN NOT EXISTS (
    SELECT 1 FROM payment_requests r
    WHERE r.status = 'approved'
      AND r.kind = NEW.kind
      AND r.ref_id IS NEW.ref_id
      AND r.amount = NEW.amount
      AND r.account = NEW.account
      AND r.decided_by = NEW.approved_by
)
BEGIN
    SELECT RAISE(ABORT, 'payment rejected: no matching human-approved payment request');
END;

-- Cash balances can never go below zero.
CREATE TRIGGER guard_cash_non_negative
BEFORE UPDATE OF balance ON cash_accounts
WHEN NEW.balance < 0
BEGIN
    SELECT RAISE(ABORT, 'cash balance cannot fall below zero');
END;
"""

BOARD_TABLES = ("payment_requests", "board_posts")


def _require_working_db() -> None:
    if not WORKING_DB.exists():
        raise FileNotFoundError(
            f"Working database not found at {WORKING_DB}. Run reset_working_database "
            "or copy data/campus_customs.db to data/campus_customs_new.db first."
        )


def _open(read_only: bool) -> sqlite3.Connection:
    mode = "ro" if read_only else "rw"
    conn = sqlite3.connect(f"{WORKING_DB.as_uri()}?mode={mode}", uri=True, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def ensure_board_schema() -> None:
    """Create the board tables and guard triggers in the working copy if missing."""
    _require_working_db()
    conn = _open(read_only=False)
    try:
        conn.executescript(BOARD_SCHEMA)
        conn.commit()
    finally:
        conn.close()


def _board_schema_present(conn: sqlite3.Connection) -> bool:
    names = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type IN ('table','trigger')")}
    return set(BOARD_TABLES) <= names and "guard_payment_requires_human_approval" in names


@contextmanager
def connect(read_only: bool = True) -> Iterator[sqlite3.Connection]:
    """Open the working database. Read-only by default.

    Write connections start an IMMEDIATE transaction, commit on success,
    and roll back on any error. Connections are always closed.
    """
    _require_working_db()
    conn = _open(read_only=True)
    try:
        present = _board_schema_present(conn)
    finally:
        conn.close()
    if not present:
        ensure_board_schema()

    conn = _open(read_only)
    try:
        if not read_only:
            conn.execute("BEGIN IMMEDIATE")
        yield conn
        if not read_only:
            conn.commit()
    except Exception:
        if not read_only:
            conn.rollback()
        raise
    finally:
        conn.close()


def reset_working_db() -> dict[str, Any]:
    """Restore the working copy from the original database, then add board tables.

    The original is opened read-only and copied with SQLite's backup API.
    """
    if not ORIGINAL_DB.exists():
        raise FileNotFoundError(f"Original database not found at {ORIGINAL_DB}")
    src = sqlite3.connect(f"{ORIGINAL_DB.resolve().as_uri()}?mode=ro", uri=True)
    dst = sqlite3.connect(WORKING_DB)
    try:
        src.backup(dst)
    finally:
        src.close()
        dst.close()
    ensure_board_schema()
    return {"reset": True, "working_db": WORKING_DB.name, "restored_from": ORIGINAL_DB.name}


def fetch_one(conn: sqlite3.Connection, sql: str, params: tuple = ()) -> dict[str, Any] | None:
    row = conn.execute(sql, params).fetchone()
    return dict(row) if row is not None else None


def fetch_all(conn: sqlite3.Connection, sql: str, params: tuple = ()) -> list[dict[str, Any]]:
    return [dict(r) for r in conn.execute(sql, params).fetchall()]


def shop_today(conn: sqlite3.Connection) -> date:
    """The shop's current date from desk.date_today (not the real clock)."""
    row = fetch_one(conn, "SELECT date_today FROM desk LIMIT 1")
    if row is None:
        raise RuntimeError("desk table has no row; cannot determine date_today")
    return date.fromisoformat(row["date_today"])


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
