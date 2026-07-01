"""Content protection: shield things that must survive verbatim.

Before the text goes to the model we swap fenced code blocks, inline code, and
URLs for opaque placeholders, then restore them afterward. This stops the
humanizer from "improving" (i.e. breaking) code, links, or citations.
"""

from __future__ import annotations

import re

_FENCED_CODE = re.compile(r"```.*?```", re.DOTALL)
_INLINE_CODE = re.compile(r"`[^`\n]+`")
_URL = re.compile(r"https?://[^\s)]+")

_PLACEHOLDER = "\u2063TF{}\u2063"  # invisible separators make accidental edits obvious


class Protector:
    """Reversibly mask protected spans in a piece of text."""

    def __init__(self, protect_code: bool = True, protect_urls: bool = True):
        self.protect_code = protect_code
        self.protect_urls = protect_urls
        self._store: list[str] = []

    def _stash(self, match: re.Match) -> str:
        token = _PLACEHOLDER.format(len(self._store))
        self._store.append(match.group(0))
        return token

    def mask(self, text: str) -> str:
        self._store = []
        if self.protect_code:
            text = _FENCED_CODE.sub(self._stash, text)
            text = _INLINE_CODE.sub(self._stash, text)
        if self.protect_urls:
            text = _URL.sub(self._stash, text)
        return text

    def restore(self, text: str) -> str:
        for i, original in enumerate(self._store):
            text = text.replace(_PLACEHOLDER.format(i), original)
        return text
