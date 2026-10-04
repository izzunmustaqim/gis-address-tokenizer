"""AddressTokenizer orchestrator — splitting and rule dispatch.

See design.md 2.3-2.4: injectable rule list (default priority order).
Splitting has two strategies behind one method:

1. Comma path — split on commas; each segment is matched WHOLE against
   the specific rules (the literal design.md comma path).
2. Scan fallback — a segment (or a comma-free input, which is one
   segment) no specific rule claims in full is scanned with a regex for
   embedded components; unmatched residue spans become section tokens.
   This is what makes spec example 1s "21080 Kuala Terengganu" segment
   parse correctly and earns the comma-free bonus (Phase 5).

Rules remain the single authority on what counts: the scan only proposes
spans; _consume dispatches every emitted token through the rule list.
"""

from __future__ import annotations

import re
from collections.abc import Sequence

from .model import Address
from .rules import (
    CITIES,
    STATES,
    AptRule,
    CityRule,
    ComponentRule,
    PostcodeRule,
    SectionRule,
    StateRule,
    StreetRule,
)

_SECTION_KEY = SectionRule.name

# Normalization (spec.md 4): trailing punctuation must not corrupt
# matching — "...Terengganu." becomes "Terengganu"; collapse whitespace.
_TRAILING_PUNCT_RE = re.compile(r"[.,;:!?]+$")
_WS_RE = re.compile(r"\s+")

# Scan pattern: alternation of every specific component pattern.
# Boundaries keep partial words from matching ("xKajang" is not a city);
# longest-first city/state alternations make "Kuala Terengganu" win over
# any shorter prefix. (?!\w) after digits rejects "No 11A" outright so it
# falls through to section instead of becoming apt + "A".
_CITIES_ALT = "|".join(re.escape(c) for c in sorted(CITIES, key=len, reverse=True))
_STATES_ALT = "|".join(re.escape(s) for s in sorted(STATES, key=len, reverse=True))

# A street match is lazy: it runs until the next recognizable component
# (or end), so "Jalan Merdeka Kajang" yields street + city, not street
# swallowing the city. Lookaheads are anchored at the current position;
# the lazy part consumes the separating space before stopping.
_ANY_COMPONENT = (
    rf"(?=\Z|(?<!\w)No \d+(?!\w)|(?<!\w)\d{{5}}(?!\w)"
    rf"|(?<!\w)(?:{_CITIES_ALT})(?!\w)|(?<!\w)(?:{_STATES_ALT})(?!\w)"
    rf"|(?<!\w)(?:Jalan|Jln|Lorong)\ |(?<!\w)Persiaran)"
)
TOKEN_RE = re.compile(
    rf"(?<!\w)No \d+(?!\w)"
    rf"|(?<!\w)(?:Jalan|Jln|Lorong)\ .+?{_ANY_COMPONENT}"
    rf"|(?<!\w)Persiaran(?:\ .+?{_ANY_COMPONENT})?"
    rf"|(?<!\w)\d{{5}}(?!\w)"
    rf"|(?<!\w)(?:{_CITIES_ALT})(?!\w)"
    rf"|(?<!\w)(?:{_STATES_ALT})(?!\w)"
)

# Only sentence punctuation and whitespace — brackets stay intact in
# section text like "Taman Baru (Fasa 2)".
_RESIDUE_STRIP = " \t.,;!?"


def default_rules() -> list[ComponentRule]:
    """Specific rules in priority order; SectionRule always last."""
    return [
        AptRule(),
        StreetRule(),
        PostcodeRule(),
        CityRule(),
        StateRule(),
        SectionRule(),
    ]


class AddressTokenizer:
    """Takes raw input, splits into tokens, dispatches through rules."""

    def __init__(self, rules: Sequence[ComponentRule] | None = None) -> None:
        self._rules = list(rules) if rules is not None else default_rules()

    def tokenize(self, raw: str) -> Address:
        """Normalize, split, and consume each token into an Address.

        Empty / whitespace-only input yields an empty Address (spec 7).
        """
        address = Address()
        for token in self._split(raw):
            address = self._consume(address, token)
        return address

    def _split(self, raw: str) -> list[str]:
        """Comma segments (or one whole input); scan fallback per segment."""
        text = _WS_RE.sub(" ", _TRAILING_PUNCT_RE.sub("", raw.strip()))
        if not text:
            return []
        segments = text.split(",") if "," in text else [text]
        return [tok for seg in segments for tok in self._segment_tokens(seg.strip())]

    def _segment_tokens(self, segment: str) -> list[str]:
        """Whole-segment rule match when the scan finds no decomposition.

        The scan runs first: if it splits the segment into MULTIPLE
        tokens, decomposition wins — a prefix rule like StreetRule must
        not swallow embedded components ("Jalan Merdeka Kajang ...").
        When the scan yields one token (or none), a specific rule that
        matches the segment whole has the final say, which also keeps
        injected custom rules working on un-scannable text.
        """
        if not segment:
            return []
        scanned = self._scan(segment)
        if len(scanned) > 1:
            return scanned
        for rule in self._rules:
            if rule.name != _SECTION_KEY and rule.matches(segment):
                return [segment]
        return scanned

    def _scan(self, segment: str) -> list[str]:
        """Matched spans become tokens; residue spans become section tokens.

        Whitespace/punctuation-only residue is discarded, so the gap in
        "21080 Kuala Terengganu" does not produce a spurious section.
        """
        tokens: list[str] = []
        pos = 0
        for match in TOKEN_RE.finditer(segment):
            tokens.extend(self._residue_tokens(segment[pos : match.start()]))
            tokens.append(match.group().strip())
            pos = match.end()
        tokens.extend(self._residue_tokens(segment[pos:]))
        return tokens

    @staticmethod
    def _residue_tokens(span: str) -> list[str]:
        text = span.strip(_RESIDUE_STRIP)
        return [text] if text else []

    def _consume(self, address: Address, token: str) -> Address:
        """First matching rule wins; defensive fall-through returns unchanged."""
        for rule in self._rules:
            if rule.matches(token):
                return rule.apply(address, token)
        return address  # unreachable when SectionRule present
