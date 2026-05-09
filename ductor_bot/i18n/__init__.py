"""Internationalization module for ductor-bot.

Public API::

    from ductor_bot.i18n import init, t, t_rich, t_cmd, t_plural

    init("de")  # once at startup
    t("session.error", model="opus")  # chat/Markdown string
    t_rich("lifecycle.stopped")  # CLI/Rich string
    t_cmd("new")  # bot command description
    t_plural("tasks.cancelled", 3)  # plural-aware (count is auto-bound)
"""

from __future__ import annotations

import logging

from ductor_bot.i18n.loader import TranslationStore

logger = logging.getLogger(__name__)

_store: TranslationStore | None = None
DEFAULT_LANGUAGE = "en"

# Available languages: directory name -> display name (native).
LANGUAGES: dict[str, str] = {
    "zh-CN": "简体中文",
    "en": "English",
    "de": "Deutsch",
    "nl": "Nederlands",
    "es": "Español",
    "fr": "Français",
    "id": "Bahasa Indonesia",
    "pt": "Português",
    "ru": "Русский",
}

_LANGUAGE_ALIASES: dict[str, str] = {
    "zh": "zh-CN",
    "zh-cn": "zh-CN",
    "zh_cn": "zh-CN",
    "zh-CN": "zh-CN",
    "zh_CN": "zh-CN",
    "zh-hans": "zh-CN",
    "zh-Hans": "zh-CN",
    "zh_Hans": "zh-CN",
    "cn": "zh-CN",
}


def normalize_language(language: str) -> str:
    """Normalize common Simplified Chinese aliases to the packaged locale code."""
    trimmed = language.strip()
    return _LANGUAGE_ALIASES.get(trimmed, trimmed)


def init(language: str = DEFAULT_LANGUAGE) -> None:
    """Initialize the translation store. Call once at startup."""
    global _store  # noqa: PLW0603
    requested = normalize_language(language)
    if requested in LANGUAGES:
        lang = requested
    else:
        lang = DEFAULT_LANGUAGE
        logger.warning("Unknown language '%s', falling back to '%s'", language, lang)
    _store = TranslationStore(lang)
    logger.info("i18n initialized: language=%s", lang)


def _get_store() -> TranslationStore:
    if _store is None:
        # Auto-init with English if nobody called init() yet. Runtime entrypoints
        # re-init with config.language before user-facing bot output.
        init(DEFAULT_LANGUAGE)
        assert _store is not None
    return _store


def t(key: str, **kwargs: object) -> str:
    """Translate a chat/Markdown string with variable substitution."""
    return _get_store().chat(key, **kwargs)


def t_rich(key: str, **kwargs: object) -> str:
    """Translate a CLI/Rich string with variable substitution."""
    return _get_store().cli(key, **kwargs)


def t_cmd(key: str) -> str:
    """Translate a bot command description."""
    return _get_store().cmd(key)


def t_plural(key: str, count: int, **kwargs: object) -> str:
    """Translate with simple plural rules (_one / _other suffix)."""
    suffix = "_one" if count == 1 else "_other"
    return t(f"{key}{suffix}", count=count, **kwargs)


def get_language() -> str:
    """Return the active language code."""
    return _get_store().language


def get_store() -> TranslationStore:
    """Return the active TranslationStore (for validation/testing)."""
    return _get_store()
