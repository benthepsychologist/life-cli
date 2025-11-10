# Copyright 2024 Life-CLI Contributors
# SPDX-License-Identifier: Apache-2.0

"""Tests for date_utils.py module."""

from datetime import datetime, timedelta

import pytest

from life.date_utils import get_date_variables, parse_date_range


class TestParseDateRange:
    """Test date range parsing."""

    def test_parse_days(self):
        """Test parsing days format."""
        from_date, to_date = parse_date_range("7d")

        # Should return ISO format dates
        assert len(from_date) == 10  # YYYY-MM-DD
        assert len(to_date) == 10

        # to_date should be today
        assert to_date == datetime.now().date().isoformat()

        # from_date should be 7 days ago
        expected_from = (datetime.now().date() - timedelta(days=7)).isoformat()
        assert from_date == expected_from

    def test_parse_weeks(self):
        """Test parsing weeks format."""
        from_date, to_date = parse_date_range("2w")

        # 2 weeks = 14 days
        expected_from = (datetime.now().date() - timedelta(days=14)).isoformat()
        assert from_date == expected_from

    def test_parse_months(self):
        """Test parsing months format."""
        from_date, to_date = parse_date_range("1m")

        # 1 month = 30 days
        expected_from = (datetime.now().date() - timedelta(days=30)).isoformat()
        assert from_date == expected_from

    def test_parse_case_insensitive(self):
        """Test that parsing is case-insensitive."""
        from1, to1 = parse_date_range("7D")
        from2, to2 = parse_date_range("7d")

        assert from1 == from2
        assert to1 == to2

    def test_parse_invalid_format(self):
        """Test error handling for invalid format."""
        with pytest.raises(ValueError, match="Invalid date_range format"):
            parse_date_range("invalid")

    def test_parse_invalid_unit(self):
        """Test error handling for invalid unit."""
        # Currently would fail at regex match, but documenting expected behavior
        with pytest.raises(ValueError):
            parse_date_range("7x")

    def test_parse_missing_number(self):
        """Test error handling for missing number."""
        with pytest.raises(ValueError):
            parse_date_range("d")

    def test_parse_various_amounts(self):
        """Test different day amounts."""
        test_cases = [
            ("1d", 1),
            ("7d", 7),
            ("30d", 30),
            ("90d", 90),
        ]

        for date_str, days in test_cases:
            from_date, to_date = parse_date_range(date_str)
            expected_from = (datetime.now().date() - timedelta(days=days)).isoformat()
            assert from_date == expected_from


class TestGetDateVariables:
    """Test date variables dictionary generation."""

    def test_get_date_variables(self):
        """Test getting date variables."""
        vars = get_date_variables("7d")

        assert "from_date" in vars
        assert "to_date" in vars
        assert len(vars) == 2

    def test_date_variables_format(self):
        """Test that date variables are in correct format."""
        vars = get_date_variables("7d")

        # Should be ISO format YYYY-MM-DD
        assert len(vars["from_date"]) == 10
        assert len(vars["to_date"]) == 10
        assert vars["from_date"] < vars["to_date"]

    def test_date_variables_various_ranges(self):
        """Test date variables with different ranges."""
        for range_str in ["1d", "7d", "1w", "30d", "1m"]:
            vars = get_date_variables(range_str)
            assert "from_date" in vars
            assert "to_date" in vars
            # from_date should always be before to_date
            assert vars["from_date"] <= vars["to_date"]
