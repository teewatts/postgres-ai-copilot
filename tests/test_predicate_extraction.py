"""
Tests for plan predicate extraction helpers.

These tests verify that the initial predicate extraction logic can identify
likely filter columns from simple PostgreSQL plan conditions.
"""

from app.services.predicate_extraction import extract_likely_filter_column


def test_extract_likely_filter_column_from_simple_filter() -> None:
    """Ensure a simple equality predicate yields the expected column name."""
    condition = "(email = 'alice@example.com'::text)"
    assert extract_likely_filter_column(condition) == "email"


def test_extract_likely_filter_column_from_casted_filter() -> None:
    """Ensure a casted predicate still yields the expected column name."""
    condition = "((email)::text = 'alice@example.com'::text)"
    assert extract_likely_filter_column(condition) == "email"


def test_extract_likely_filter_column_from_numeric_filter() -> None:
    """Ensure numeric equality predicates are supported by the initial helper."""
    condition = "(account_id = 123)"
    assert extract_likely_filter_column(condition) == "account_id"


def test_extract_likely_filter_column_returns_none_for_missing_condition() -> None:
    """Ensure the helper returns None when no condition is supplied."""
    assert extract_likely_filter_column(None) is None