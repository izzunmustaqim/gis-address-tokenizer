"""Integration tests: raw string in, Address out (spec 5, tasks Phase 4)."""

import json

import pytest

from address_tokenizer import AddressTokenizer
from address_tokenizer.model import Address
from address_tokenizer.rules import CityRule, SectionRule


@pytest.fixture
def tokenizer() -> AddressTokenizer:
    return AddressTokenizer()


class TestSpecExamples:
    def test_example_1_full_address(self, tokenizer: AddressTokenizer) -> None:
        raw = "No 11, Chendering, 21080 Kuala Terengganu, Terengganu."
        assert tokenizer.tokenize(raw).to_dict() == {
            "apt": "No 11",
            "section": "Chendering",
            "postcode": "21080",
            "city": "Kuala Terengganu",
            "state": "Terengganu",
        }

    def test_example_2_incomplete_address(self, tokenizer: AddressTokenizer) -> None:
        raw = "No 11, Kuala Terengganu, Chendering"
        assert tokenizer.tokenize(raw).to_dict() == {
            "apt": "No 11",
            "section": "Chendering",
            "city": "Kuala Terengganu",
        }

    def test_example_1_json_roundtrip(self, tokenizer: AddressTokenizer) -> None:
        raw = "No 11, Chendering, 21080 Kuala Terengganu, Terengganu."
        parsed = json.loads(tokenizer.tokenize(raw).to_json())
        assert parsed["postcode"] == "21080"


class TestOrderAgnostic:
    def test_state_and_city_first_apt_last(self, tokenizer: AddressTokenizer) -> None:
        raw = "Selangor, Kajang, No 11"
        assert tokenizer.tokenize(raw).to_dict() == {
            "apt": "No 11",
            "city": "Kajang",
            "state": "Selangor",
        }

    def test_reversed_example_1(self, tokenizer: AddressTokenizer) -> None:
        raw = "Terengganu, Kuala Terengganu, 21080, Chendering, No 11"
        assert tokenizer.tokenize(raw).to_dict() == {
            "apt": "No 11",
            "section": "Chendering",
            "postcode": "21080",
            "city": "Kuala Terengganu",
            "state": "Terengganu",
        }


class TestSingleComponent:
    @pytest.mark.parametrize(
        ("raw", "expected"),
        [
            ("No 42", {"apt": "No 42"}),
            ("Kajang", {"city": "Kajang"}),
            ("Selangor", {"state": "Selangor"}),
            ("01000", {"postcode": "01000"}),
            ("Jalan Merdeka", {"street": "Jalan Merdeka"}),
            ("Chendering", {"section": "Chendering"}),
        ],
    )
    def test_one_field(
        self, tokenizer: AddressTokenizer, raw: str, expected: dict[str, str]
    ) -> None:
        assert tokenizer.tokenize(raw).to_dict() == expected


class TestRobustness:
    @pytest.mark.parametrize("raw", ["", "   ", "\t\n", ", , ,"])
    def test_empty_input_returns_empty_address(
        self, tokenizer: AddressTokenizer, raw: str
    ) -> None:
        addr = tokenizer.tokenize(raw)
        assert isinstance(addr, Address)
        assert addr.to_dict() == {}

    @pytest.mark.parametrize("raw", ["No ABC, Kajang", "No 11A, Kajang", "no 11, Kajang"])
    def test_malformed_apt_not_accepted(
        self, tokenizer: AddressTokenizer, raw: str
    ) -> None:
        assert "apt" not in tokenizer.tokenize(raw).to_dict()

    @pytest.mark.parametrize("raw", ["00000, Kajang", "99999, Kajang", "2108, Kajang"])
    def test_bad_postcode_not_accepted(
        self, tokenizer: AddressTokenizer, raw: str
    ) -> None:
        assert "postcode" not in tokenizer.tokenize(raw).to_dict()

    def test_unknown_names_become_section(self, tokenizer: AddressTokenizer) -> None:
        addr = tokenizer.tokenize("Kajang, Perak, Atlantis").to_dict()
        assert addr["city"] == "Kajang"
        assert "state" not in addr

    def test_trailing_period_does_not_corrupt_match(
        self, tokenizer: AddressTokenizer
    ) -> None:
        assert tokenizer.tokenize("Kajang.").to_dict() == {"city": "Kajang"}

    def test_whitespace_is_collapsed(self, tokenizer: AddressTokenizer) -> None:
        raw = "No  11 ,   Kajang"
        assert tokenizer.tokenize(raw).to_dict() == {"apt": "No 11", "city": "Kajang"}


class TestInjectedRules:
    def test_custom_rule_list_is_used(self) -> None:
        tok = AddressTokenizer(rules=[CityRule(), SectionRule()])
        addr = tok.tokenize("No 11, Kajang").to_dict()
        assert addr == {"section": "No 11", "city": "Kajang"}


class TestCommaFreeBonus:
    """Phase 5: regex-scan path when input has no commas (spec 4 bonus)."""

    @pytest.mark.parametrize(
        ("raw", "expected"),
        [
            (
                "No 11 Chendering 21080 Kuala Terengganu Terengganu",
                {
                    "apt": "No 11",
                    "section": "Chendering",
                    "postcode": "21080",
                    "city": "Kuala Terengganu",
                    "state": "Terengganu",
                },
            ),
            (
                "No 11 Kuala Terengganu Chendering",
                {"apt": "No 11", "section": "Chendering", "city": "Kuala Terengganu"},
            ),
            (
                "21080 Kuala Terengganu",
                {"postcode": "21080", "city": "Kuala Terengganu"},
            ),
            (
                "Jalan Merdeka Kajang Selangor 63000",
                {
                    "street": "Jalan Merdeka",
                    "city": "Kajang",
                    "state": "Selangor",
                    "postcode": "63000",
                },
            ),
        ],
    )
    def test_comma_free_parses(
        self, tokenizer: AddressTokenizer, raw: str, expected: dict[str, str]
    ) -> None:
        assert tokenizer.tokenize(raw).to_dict() == expected

    def test_mixed_comma_and_comma_free(self, tokenizer: AddressTokenizer) -> None:
        raw = "No 11, Chendering 21080 Kuala Terengganu, Terengganu"
        assert tokenizer.tokenize(raw).to_dict() == {
            "apt": "No 11",
            "section": "Chendering",
            "postcode": "21080",
            "city": "Kuala Terengganu",
            "state": "Terengganu",
        }

    def test_trailing_period_comma_free(self, tokenizer: AddressTokenizer) -> None:
        assert tokenizer.tokenize("21080 Kuala Terengganu.").to_dict() == {
            "postcode": "21080",
            "city": "Kuala Terengganu",
        }

    def test_residue_between_matches_is_section_not_noise(
        self, tokenizer: AddressTokenizer
    ) -> None:
        # the single space between postcode and city must not become section
        addr = tokenizer.tokenize("21080 Kuala Terengganu").to_dict()
        assert "section" not in addr
