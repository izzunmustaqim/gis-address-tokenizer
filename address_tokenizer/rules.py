"""ComponentRule ABC + concrete rules + SectionRule.

See design.md §2.2: ComponentRule (name, matches, apply) and one concrete
rule per component. Every `matches` is regex / frozenset / range based and
total — no input raises. Depends only on model.
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from typing import ClassVar

from .model import Address

# --- Lookup data (spec.md §3.1–3.2, exact match) ---------------------------

CITIES = frozenset(
    {
        "Kuala Terengganu",
        "Kuala Lumpur",
        "Kajang",
        "Bangi",
        "Damansara",
        "Petaling Jaya",
        "Puchong",
        "Subang Jaya",
        "Cyberjaya",
        "Putrajaya",
        "Mantin",
        "Kuching",
        "Seremban",
    }
)

STATES = frozenset(
    {
        "Selangor",
        "Terengganu",
        "Pahang",
        "Kelantan",
        "Melaka",
        "Pulau Pinang",
        "Kedah",
        "Johor",
        "Perlis",
        "Sabah",
        "Sarawak",
    }
)

# Street prefixes (spec.md §3 row 6). The first three carry a required
# trailing space; "Persiaran" needs any content after it.
_WORD_STREET_PREFIXES = ("Jalan ", "Jln ", "Lorong ")

_APT_RE = re.compile(r"No \d+")
_POSTCODE_RE = re.compile(r"\d{5}")


class ComponentRule(ABC):
    """Single interface every component rule implements.

    `matches` is a pure predicate; `apply` is only called after `matches`
    returns True (tokenizer contract), so the tokenizer can probe rules
    without committing to a mutation.
    """

    name: ClassVar[str]  # output key, e.g. "city"

    @abstractmethod
    def matches(self, token: str) -> bool:
        """True if this token belongs to this component. Must not raise."""

    @abstractmethod
    def apply(self, address: Address, token: str) -> Address:
        """Return address with this component set from token."""


class _FieldRule(ComponentRule):
    """Shared base: rules that set their own `name` field from the token."""

    def apply(self, address: Address, token: str) -> Address:
        return address.with_field(self.name, token)


class AptRule(_FieldRule):
    """`No <digits>` — rejects `No`, `No ABC`, `no 11`."""

    name: ClassVar[str] = "apt"

    def matches(self, token: str) -> bool:
        return _APT_RE.fullmatch(token) is not None


class StreetRule(_FieldRule):
    """Begins with `Jalan `, `Jln `, `Lorong `, or `Persiaran` + content."""

    name: ClassVar[str] = "street"

    def matches(self, token: str) -> bool:
        if token.startswith("Persiaran"):
            return len(token) > len("Persiaran")  # needs content after prefix
        return token.startswith(_WORD_STREET_PREFIXES)


class PostcodeRule(_FieldRule):
    """5 digits AND inclusive range 01000–98859 (spec.md §3)."""

    name: ClassVar[str] = "postcode"

    def matches(self, token: str) -> bool:
        if _POSTCODE_RE.fullmatch(token) is None:
            return False
        return 1000 <= int(token) <= 98859


class CityRule(_FieldRule):
    """Exact membership in the fixed city list."""

    name: ClassVar[str] = "city"

    def matches(self, token: str) -> bool:
        return token in CITIES


class StateRule(_FieldRule):
    """Exact membership in the fixed state list."""

    name: ClassVar[str] = "state"

    def matches(self, token: str) -> bool:
        return token in STATES


class SectionRule(_FieldRule):
    """Catch-all: always matches; consulted last by the tokenizer."""

    name: ClassVar[str] = "section"

    def matches(self, token: str) -> bool:
        return True
