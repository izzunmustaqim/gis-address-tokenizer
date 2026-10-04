"""Address value object — frozen dataclass with six optional fields.

See design.md §2.1: with_field(), to_dict() (canonical key order, Nones
omitted), to_json(). Imports nothing from the package.
"""

from __future__ import annotations

import dataclasses
import json
from dataclasses import dataclass

# Canonical output key order (spec.md §5).
FIELD_NAMES: tuple[str, ...] = (
    "apt",
    "section",
    "postcode",
    "city",
    "state",
    "street",
)


@dataclass(frozen=True)
class Address:
    """Immutable address; all six components optional.

    Frozen + with_field keeps the object immutable while rules "fill it in"
    by returning updated copies — safe to share, no hidden mutation.
    Postcode is a string so leading zeros survive ("01000").
    """

    apt: str | None = None
    section: str | None = None
    postcode: str | None = None
    city: str | None = None
    state: str | None = None
    street: str | None = None

    def with_field(self, name: str, value: str) -> Address:
        """Return a new Address with `name` set to `value`."""
        if name not in FIELD_NAMES:
            raise ValueError(f"unknown address field: {name!r}")
        return dataclasses.replace(self, **{name: value})

    def to_dict(self) -> dict[str, str]:
        """Canonical-order dict of only the non-None components."""
        return {
            name: value
            for name in FIELD_NAMES
            if (value := getattr(self, name)) is not None
        }

    def to_json(self, *, indent: int | None = 2) -> str:
        """JSON serialization of to_dict(); absent fields omitted entirely."""
        return json.dumps(self.to_dict(), indent=indent)
