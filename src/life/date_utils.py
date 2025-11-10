# Copyright 2025 Ben Mensi
# SPDX-License-Identifier: Apache-2.0

"""
Date utilities for Life-CLI.

Provides date range helpers for task configuration.
"""

import re
from datetime import datetime, timedelta
from typing import Tuple


def parse_date_range(date_range_str: str) -> Tuple[str, str]:
    """
    Parse a date range string and return ISO format dates.

    Supports formats:
    - "7d" -> last 7 days
    - "30d" -> last 30 days
    - "1w" -> last 1 week (7 days)
    - "1m" -> last 1 month (30 days)

    Args:
        date_range_str: Date range string (e.g., "7d", "1w", "30d")

    Returns:
        Tuple of (from_date, to_date) in ISO format (YYYY-MM-DD)

    Example:
        >>> parse_date_range("7d")
        ('2024-11-03', '2024-11-10')
    """
    # Parse the date range string
    match = re.match(r'(\d+)([dwm])', date_range_str.lower())
    if not match:
        raise ValueError(
            f"Invalid date_range format: '{date_range_str}'. "
            "Expected format: number + unit (e.g., '7d', '1w', '30d')"
        )

    amount = int(match.group(1))
    unit = match.group(2)

    # Convert to days
    if unit == 'd':
        days = amount
    elif unit == 'w':
        days = amount * 7
    elif unit == 'm':
        days = amount * 30
    else:
        raise ValueError(f"Unknown unit: {unit}. Use 'd' (days), 'w' (weeks), or 'm' (months)")

    # Calculate dates
    to_date = datetime.now().date()
    from_date = to_date - timedelta(days=days)

    return from_date.isoformat(), to_date.isoformat()


def get_date_variables(date_range: str) -> dict:
    """
    Get date variables dictionary for a date range.

    Args:
        date_range: Date range string (e.g., "7d")

    Returns:
        Dictionary with 'from_date' and 'to_date' keys

    Example:
        >>> get_date_variables("7d")
        {'from_date': '2024-11-03', 'to_date': '2024-11-10'}
    """
    from_date, to_date = parse_date_range(date_range)
    return {
        "from_date": from_date,
        "to_date": to_date,
    }
