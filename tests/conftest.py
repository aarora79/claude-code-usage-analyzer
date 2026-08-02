"""Shared pytest fixtures for the analyzer test suite."""

from typing import Any

import pytest


@pytest.fixture
def sample_pricing_map() -> dict[str, dict[str, Any]]:
    """Return a small pricing map covering the sample models.

    Returns:
        A pricing map keyed by full model name.
    """
    return {
        "claude-opus-4-8": {
            "input_cost_per_token": 5e-06,
            "output_cost_per_token": 25e-06,
            "cache_creation_input_token_cost": 6.25e-06,
            "cache_read_input_token_cost": 5e-07,
        },
        "claude-haiku-4-5-20251001": {
            "input_cost_per_token": 1e-06,
            "output_cost_per_token": 5e-06,
            "cache_creation_input_token_cost": 1.25e-06,
            "cache_read_input_token_cost": 1e-07,
        },
    }


@pytest.fixture
def sample_raw_data() -> dict[str, Any]:
    """Return a minimal but realistic ccusage-style raw data payload.

    Returns:
        A dictionary with ``daily`` and ``totals`` keys.
    """
    return {
        "daily": [
            {
                "date": "2026-01-01",
                "inputTokens": 1000,
                "outputTokens": 2000,
                "cacheCreationTokens": 3000,
                "cacheReadTokens": 40000,
                "totalTokens": 46000,
                "totalCost": 0.5,
                "modelBreakdowns": [
                    {
                        "modelName": "claude-opus-4-8",
                        "inputTokens": 1000,
                        "outputTokens": 2000,
                        "cacheCreationTokens": 3000,
                        "cacheReadTokens": 40000,
                        "cost": 0.5,
                    }
                ],
            },
            {
                # Newer ccusage uses "period" instead of "date".
                "period": "2026-01-02",
                "inputTokens": 500,
                "outputTokens": 1500,
                "cacheCreationTokens": 1000,
                "cacheReadTokens": 20000,
                "totalTokens": 23000,
                "totalCost": 0.25,
                "modelBreakdowns": [
                    {
                        "modelName": "claude-opus-4-8",
                        "inputTokens": 300,
                        "outputTokens": 1000,
                        "cacheCreationTokens": 800,
                        "cacheReadTokens": 15000,
                        "cost": 0.2,
                    },
                    {
                        "modelName": "claude-haiku-4-5-20251001",
                        "inputTokens": 200,
                        "outputTokens": 500,
                        "cacheCreationTokens": 200,
                        "cacheReadTokens": 5000,
                        "cost": 0.05,
                    },
                ],
            },
        ],
        "totals": {
            "inputTokens": 1500,
            "outputTokens": 3500,
            "cacheCreationTokens": 4000,
            "cacheReadTokens": 60000,
            "totalTokens": 69000,
            "totalCost": 0.75,
        },
    }
