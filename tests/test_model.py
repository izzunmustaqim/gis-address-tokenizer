"""Unit tests for the Address value object (design.md §2.1, tasks Phase 2)."""

import dataclasses
import json

import pytest

from address_tokenizer.model import FIELD_NAMES, Address


class TestEmptyAddress:
    def test_defaults_are_all_none(self) -> None:
        addr = Address()
        assert all(getattr(addr, f) is None for f in FIELD_NAMES)

    def test_to_dict_is_empty(self) -> None:
        assert Address().to_dict() == {}

    def test_to_json_is_empty_object(self) -> None:
        assert json.loads(Address().to_json()) == {}


class TestPartialAddress:
    def test_omits_absent_keys(self) -> None:
        addr = Address(apt="No 11", city="Kajang")
        assert addr.to_dict() == {"apt": "No 11", "city": "Kajang"}

    def test_canonical_key_order(self) -> None:
        addr = Address(street="Jalan Foo", apt="No 1", section="Sect")
        assert list(addr.to_dict()) == ["apt", "section", "street"]

    def test_none_never_emitted_as_null(self) -> None:
        # explicit Nones (the default) must be dropped, not serialized
        addr = Address(city="Kajang", state=None)
        assert "state" not in addr.to_dict()
        assert "null" not in addr.to_json()


class TestPostcode:
    def test_leading_zeros_preserved(self) -> None:
        addr = Address(postcode="01000")
        assert addr.to_dict() == {"postcode": "01000"}
        assert json.loads(addr.to_json()) == {"postcode": "01000"}


class TestWithField:
    def test_returns_new_instance_original_unchanged(self) -> None:
        base = Address()
        updated = base.with_field("city", "Kajang")
        assert updated.city == "Kajang"
        assert base.city is None
        assert updated is not base

    def test_sets_named_field(self) -> None:
        addr = Address().with_field("apt", "No 11").with_field("state", "Selangor")
        assert addr.apt == "No 11"
        assert addr.state == "Selangor"

    @pytest.mark.parametrize("bad", ["country", "City", "", "POSTCODE"])
    def test_unknown_field_raises_value_error(self, bad: str) -> None:
        with pytest.raises(ValueError, match="unknown address field"):
            Address().with_field(bad, "x")


class TestImmutability:
    def test_frozen(self) -> None:
        addr = Address()
        with pytest.raises(dataclasses.FrozenInstanceError):
            addr.city = "Kajang"  # type: ignore[misc]
