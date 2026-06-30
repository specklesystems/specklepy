"""Dense per-namespace ``str -> int`` interner for the bundle identity scheme.

Each identity namespace (object / geometry / node) owns one interner; ids are ``0..N-1``
in first-seen order. The same key always maps to the same id — how a value referenced
from many edges (a shared material, a reused geometry) collapses to one ``K``.

``get_or_add`` returns ``(id, is_new)``; ``is_new`` is True only when the key was just
minted, so callers write the backing row (dictionary entry, node, geometry blob) exactly
once. Not thread-safe: the converter loop is sequential. Port of the .NET ``IdInterner``.
"""

from __future__ import annotations


class IdInterner:
    def __init__(self) -> None:
        self._map: dict[str, int] = {}

    @property
    def count(self) -> int:
        """Number of distinct keys interned so far (also the next id to be minted)."""
        return len(self._map)

    def get_or_add(self, key: str) -> tuple[int, bool]:
        """Resolve ``key`` to its dense id, minting on first sight.

        Returns ``(id, is_new)``; ``is_new`` is True iff the key was newly added — the
        caller should then write its backing row.
        """
        existing = self._map.get(key)
        if existing is not None:
            return existing, False
        idx = len(self._map)
        self._map[key] = idx
        return idx, True

    def intern(self, key: str) -> int:
        """Convenience when the caller doesn't need the newly-added flag."""
        idx, _ = self.get_or_add(key)
        return idx
