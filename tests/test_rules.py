"""Table-driven unit tests per rule (design.md §5, tasks Phase 3)."""

import pytest

from address_tokenizer.model import Address
from address_tokenizer.rules import (
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

ALL_RULES: list[ComponentRule] = [
    AptRule(),
    StreetRule(),
    PostcodeRule(),
    CityRule(),
    StateRule(),
    SectionRule(),
]


class TestAptRule:
    rule = AptRule()

    @pytest.mark.parametrize("token", ["No 11", "No 1", "No 12345"])
    def test_accepts(self, token: str) -> None:
        assert self.rule.matches(token)

    @pytest.mark.parametrize(
        "token", ["No", "No ", "No ABC", "no 11", "N0 11", "11", "No 11A", ""]
    )
    def test_rejects(self, token: str) -> None:
        assert not self.rule.matches(token)


class TestStreetRule:
    rule = StreetRule()

    @pytest.mark.parametrize(
        "token",
        ["Jalan Merdeka", "Jln Merdeka", "Lorong 4", "Persiaran Raya",
         "Persiaran"],
    )
    def test_accepts(self, token: str) -> None:
        assert self.rule.matches(token)

    @pytest.mark.parametrize(
        "token",
        ["Jalan", "Jln", "Lorong", "jalan Merdeka", "Jalanx", "Road 1", ""],
    )
    def test_rejects(self, token: str) -> None:
        assert not self.rule.matches(token)


class TestPostcodeRule:
    rule = PostcodeRule()

    @pytest.mark.parametrize("token", ["01000", "98859", "21080", "50000"])
    def test_accepts(self, token: str) -> None:
        assert self.rule.matches(token)

    @pytest.mark.parametrize(
        "token",
        ["00999", "98860", "00000", "99999", "2108", "210800", "2108A", "", " 21080"],
    )
    def test_rejects(self, token: str) -> None:
        assert not self.rule.matches(token)


class TestCityRule:
    rule = CityRule()

    @pytest.mark.parametrize("token", sorted(CITIES)[:3] + ["Kuala Terengganu"])
    def test_accepts(self, token: str) -> None:
        assert self.rule.matches(token)

    @pytest.mark.parametrize(
        "token", ["Kuala", "Kajang.", "kajang", "Unknown Town", ""]
    )
    def test_rejects(self, token: str) -> None:
        assert not self.rule.matches(token)


class TestStateRule:
    rule = StateRule()

    @pytest.mark.parametrize("token", sorted(STATES)[:3] + ["Terengganu"])
    def test_accepts(self, token: str) -> None:
        assert self.rule.matches(token)

    @pytest.mark.parametrize("token", ["Terengganu.", "terengganu", "Perak", ""])
    def test_rejects(self, token: str) -> None:
        assert not self.rule.matches(token)


class TestSectionRule:
    rule = SectionRule()

    @pytest.mark.parametrize("token", ["Chendering", "", "anything at all", "12345"])
    def test_always_matches(self, token: str) -> None:
        assert self.rule.matches(token)


class TestApply:
    @pytest.mark.parametrize("rule", ALL_RULES, ids=lambda r: r.name)
    def test_sets_own_field(self, rule: ComponentRule) -> None:
        addr = rule.apply(Address(), "Chendering")
        assert getattr(addr, rule.name) == "Chendering"

    @pytest.mark.parametrize("rule", ALL_RULES, ids=lambda r: r.name)
    def test_does_not_touch_other_fields(self, rule: ComponentRule) -> None:
        base = Address(apt="No 1")
        addr = rule.apply(base, "Chendering")
        other = [f for f in ("apt", "section", "postcode", "city", "state", "street")
                 if f != rule.name]
        assert all(getattr(addr, f) == getattr(base, f) for f in other)
