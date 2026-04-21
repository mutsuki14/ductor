"""Unit tests for ReactionTracker in telegram.message_dispatch (#63)."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from ductor_bot.messenger.telegram.message_dispatch import (
    _REACTION_DEFAULT,
    _REACTION_SYSTEM,
    _REACTION_THINKING,
    ReactionTracker,
)


def _make_bot() -> MagicMock:
    bot = MagicMock()
    bot.set_message_reaction = AsyncMock()
    return bot


def _emitted_emojis(bot: MagicMock) -> list[str | None]:
    """Extract the emoji arg from each set_message_reaction call.

    Returns None for "clear" calls (empty reaction list) and the emoji
    string otherwise. Assumes every call had exactly one ReactionTypeEmoji.
    """
    out: list[str | None] = []
    for call in bot.set_message_reaction.call_args_list:
        reactions = call.kwargs.get("reaction", [])
        if not reactions:
            out.append(None)
        else:
            out.append(reactions[0].emoji)
    return out


async def test_reaction_tracker_disabled_is_noop() -> None:
    bot = _make_bot()
    tracker = ReactionTracker(bot, chat_id=1, message_id=42, enabled=False)

    await tracker.set_thinking()
    await tracker.set_tool("Read")
    await tracker.set_system()
    await tracker.clear()

    bot.set_message_reaction.assert_not_awaited()


async def test_reaction_tracker_stages_map_to_emoji() -> None:
    bot = _make_bot()
    tracker = ReactionTracker(bot, chat_id=1, message_id=42, enabled=True)

    await tracker.set_thinking()
    await tracker.set_tool("Read")  # 👀
    await tracker.set_tool("Edit")  # ✍️
    await tracker.set_tool("Bash")  # 👨‍💻
    await tracker.set_tool("UnknownTool")  # fallback → default (🤔)
    await tracker.set_system()
    await tracker.clear()

    emitted = _emitted_emojis(bot)
    assert emitted == [
        _REACTION_THINKING,
        "\U0001f440",
        "✍️",
        "\U0001f468‍\U0001f4bb",
        _REACTION_DEFAULT,
        _REACTION_SYSTEM,
        None,  # clear emits empty reaction list
    ]


async def test_reaction_tracker_dedups_consecutive_same_stage() -> None:
    bot = _make_bot()
    tracker = ReactionTracker(bot, chat_id=1, message_id=42, enabled=True)

    await tracker.set_thinking()
    await tracker.set_thinking()  # dedup: no second call
    await tracker.set_thinking()  # dedup: no third call

    assert bot.set_message_reaction.await_count == 1


async def test_reaction_tracker_swallows_errors() -> None:
    bot = _make_bot()
    bot.set_message_reaction.side_effect = RuntimeError("bad request")
    tracker = ReactionTracker(bot, chat_id=1, message_id=42, enabled=True)

    # Must not raise despite the underlying call raising.
    await tracker.set_thinking()
    await tracker.set_tool("Edit")
    await tracker.clear()

    # Every call still attempted the bot API — it just did not propagate.
    assert bot.set_message_reaction.await_count >= 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(pytest.main([__file__, "-v"]))
