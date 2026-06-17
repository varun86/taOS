"""Unit tests for AgentMessageStore send/list/ordering."""
from __future__ import annotations

from unittest.mock import patch

import pytest

from tinyagentos.agent_messages import AgentMessageStore


async def _store(tmp_path):
    s = AgentMessageStore(tmp_path / "agent_messages.db")
    await s.init()
    return s


@pytest.mark.asyncio
async def test_send_persists_message_and_returns_id(tmp_path):
    store = await _store(tmp_path)
    try:
        msg_id = await store.send("alpha", "beta", "hello there")
        assert isinstance(msg_id, int)
        assert msg_id > 0

        messages = await store.get_messages("alpha")
        assert len(messages) == 1
        assert messages[0]["id"] == msg_id
        assert messages[0]["from"] == "alpha"
        assert messages[0]["to"] == "beta"
        assert messages[0]["message"] == "hello there"
        assert messages[0]["read"] is False
    finally:
        await store.close()


@pytest.mark.asyncio
async def test_get_messages_includes_sent_and_received(tmp_path):
    store = await _store(tmp_path)
    try:
        await store.send("alpha", "beta", "alpha to beta")
        await store.send("beta", "alpha", "beta to alpha")
        await store.send("gamma", "delta", "unrelated")

        alpha_msgs = await store.get_messages("alpha")
        assert len(alpha_msgs) == 2
        bodies = {m["message"] for m in alpha_msgs}
        assert bodies == {"alpha to beta", "beta to alpha"}
    finally:
        await store.close()


@pytest.mark.asyncio
async def test_get_messages_orders_by_timestamp_desc(tmp_path):
    store = await _store(tmp_path)
    try:
        times = iter([100.0, 200.0, 300.0])
        with patch("tinyagentos.agent_messages.time.time", side_effect=lambda: next(times)):
            await store.send("alpha", "beta", "oldest")
            await store.send("alpha", "beta", "middle")
            await store.send("alpha", "beta", "newest")

        messages = await store.get_messages("alpha")
        assert [m["message"] for m in messages] == ["newest", "middle", "oldest"]
    finally:
        await store.close()


@pytest.mark.asyncio
async def test_get_conversation_orders_by_timestamp_asc(tmp_path):
    store = await _store(tmp_path)
    try:
        times = iter([50.0, 150.0, 250.0])
        with patch("tinyagentos.agent_messages.time.time", side_effect=lambda: next(times)):
            await store.send("alpha", "beta", "first")
            await store.send("beta", "alpha", "second")
            await store.send("alpha", "gamma", "other thread")

        convo = await store.get_conversation("alpha", "beta")
        assert [m["message"] for m in convo] == ["first", "second"]
    finally:
        await store.close()


@pytest.mark.asyncio
async def test_get_messages_respects_limit(tmp_path):
    store = await _store(tmp_path)
    try:
        for i in range(5):
            await store.send("alpha", "beta", f"msg-{i}")

        messages = await store.get_messages("alpha", limit=2)
        assert len(messages) == 2
    finally:
        await store.close()