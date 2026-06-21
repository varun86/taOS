from __future__ import annotations

import datetime
import secrets

from tinyagentos.base_store import BaseStore

_ALPHABET = "abcdefghijklmnopqrstuvwxyz234567"

BOARD_AUDIT_SCHEMA = """
CREATE TABLE IF NOT EXISTS board_audit (
    id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL,
    event TEXT NOT NULL,
    actor TEXT NOT NULL DEFAULT '',
    from_status TEXT,
    to_status TEXT,
    ts TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_board_audit_task ON board_audit(task_id);
CREATE INDEX IF NOT EXISTS idx_board_audit_ts ON board_audit(ts);
"""

_COLS = "id, task_id, event, actor, from_status, to_status, ts"


def _now_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def _new_id() -> str:
    return "ba-" + "".join(secrets.choice(_ALPHABET) for _ in range(8))


def _row(r) -> dict:
    return {
        "id": r[0], "task_id": r[1], "event": r[2], "actor": r[3],
        "from_status": r[4], "to_status": r[5], "ts": r[6],
    }


class BoardAuditLog(BaseStore):
    """Append-only audit trail of board task state changes (#105).

    The seed of the nothing-is-ever-deleted / Time Machine story: every status
    change is recorded and never updated or deleted. There is deliberately no
    public mutate or delete method. History is returned in insertion order
    (SQLite rowid) so it is stable even when two events share a timestamp.
    """

    SCHEMA = BOARD_AUDIT_SCHEMA

    async def record(
        self,
        task_id: str,
        event: str,
        actor: str = "",
        from_status: str | None = None,
        to_status: str | None = None,
        ts: str | None = None,
    ) -> str:
        if not task_id:
            raise ValueError("task_id is required")
        if not event:
            raise ValueError("event is required")
        eid = _new_id()
        when = ts or _now_iso()
        await self._db.execute(
            f"INSERT INTO board_audit ({_COLS}) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (eid, task_id, event, actor, from_status, to_status, when),
        )
        await self._db.commit()
        return eid

    async def history(self, task_id: str) -> list[dict]:
        async with self._db.execute(
            f"SELECT {_COLS} FROM board_audit WHERE task_id = ? ORDER BY rowid ASC",
            (task_id,),
        ) as cur:
            rows = await cur.fetchall()
        return [_row(r) for r in rows]

    async def all_since(self, ts: str) -> list[dict]:
        async with self._db.execute(
            f"SELECT {_COLS} FROM board_audit WHERE ts >= ? ORDER BY rowid ASC", (ts,)
        ) as cur:
            rows = await cur.fetchall()
        return [_row(r) for r in rows]

    async def get(self, event_id: str) -> dict | None:
        async with self._db.execute(
            f"SELECT {_COLS} FROM board_audit WHERE id = ?", (event_id,)
        ) as cur:
            r = await cur.fetchone()
        return _row(r) if r else None
