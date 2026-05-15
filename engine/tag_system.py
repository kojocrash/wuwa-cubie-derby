from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Optional


@dataclass
class Tag:
    name: str
    context: dict = field(default_factory=dict)


class TagMixin:
    def __init_tags__(self) -> None:
        self._tags: list[Tag] = []

    def add_tag(self, name: str, context: dict | None = None) -> Tag:
        tag = Tag(name=name, context=context or {})
        self._tags.append(tag)
        return tag

    def remove_tags(self, name: str, exact: bool = True) -> None:
        self._tags = [t for t in self._tags if not _name_matches(t.name, name, exact)]

    def has_tag(
        self,
        name: str,
        exact: bool = True,
        predicate: Optional[Callable[[dict], bool]] = None,
    ) -> bool:
        # TODO: wildcard support (* and ** glob-style matching)
        return any(
            _name_matches(t.name, name, exact) and (predicate is None or predicate(t.context))
            for t in self._tags
        )

    def get_tags(
        self,
        name: str,
        exact: bool = True,
        predicate: Optional[Callable[[dict], bool]] = None,
    ) -> list[Tag]:
        return [
            t for t in self._tags
            if _name_matches(t.name, name, exact) and (predicate is None or predicate(t.context))
        ]


def _name_matches(tag_name: str, query: str, exact: bool) -> bool:
    if exact:
        return tag_name == query
    return tag_name == query or tag_name.startswith(query + ".")
