import pytest

from tinyagentos.board_audit import BoardAuditLog


async def _log(tmp_path):
    s = BoardAuditLog(tmp_path / "audit.db")
    await s.init()
    return s


@pytest.mark.asyncio
async def test_record_and_history_ordered(tmp_path):
    s = await _log(tmp_path)
    e1 = await s.record("tsk-1", "claimed", actor="@kilo", from_status="open", to_status="claimed", ts="2026-01-01T00:00:00+00:00")
    e2 = await s.record("tsk-1", "merged", actor="@taOS-dev", from_status="claimed", to_status="done", ts="2026-01-01T00:00:00+00:00")
    hist = await s.history("tsk-1")
    assert [h["id"] for h in hist] == [e1, e2]  # insertion order, stable even on equal ts
    assert hist[0]["event"] == "claimed" and hist[0]["actor"] == "@kilo"
    assert hist[1]["to_status"] == "done"
    await s.close()


@pytest.mark.asyncio
async def test_append_only_no_mutate_or_delete(tmp_path):
    s = await _log(tmp_path)
    await s.record("tsk-1", "open")
    # The store exposes no update/delete API: recording the same task again keeps both.
    await s.record("tsk-1", "open")
    assert len(await s.history("tsk-1")) == 2
    assert not hasattr(s, "delete")
    assert not hasattr(s, "update")
    await s.close()


@pytest.mark.asyncio
async def test_history_scoped_per_task(tmp_path):
    s = await _log(tmp_path)
    await s.record("tsk-1", "open")
    await s.record("tsk-2", "open")
    assert len(await s.history("tsk-1")) == 1
    assert await s.history("tsk-missing") == []
    await s.close()


@pytest.mark.asyncio
async def test_all_since_filters_by_ts(tmp_path):
    s = await _log(tmp_path)
    await s.record("tsk-1", "old", ts="2026-01-01T00:00:00+00:00")
    await s.record("tsk-1", "new", ts="2026-06-01T00:00:00+00:00")
    recent = await s.all_since("2026-03-01T00:00:00+00:00")
    assert [r["event"] for r in recent] == ["new"]
    await s.close()


@pytest.mark.asyncio
async def test_record_requires_task_and_event(tmp_path):
    s = await _log(tmp_path)
    with pytest.raises(ValueError):
        await s.record("", "open")
    with pytest.raises(ValueError):
        await s.record("tsk-1", "")
    await s.close()


@pytest.mark.asyncio
async def test_get_returns_event_or_none(tmp_path):
    s = await _log(tmp_path)
    eid = await s.record("tsk-1", "open")
    assert (await s.get(eid))["event"] == "open"
    assert await s.get("ba-missing") is None
    await s.close()
