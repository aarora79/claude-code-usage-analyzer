"""Statistical analysis of Claude Code usage data.

Pure functions that take parsed ccusage data plus a pricing map and return a
structured analysis dictionary. No I/O happens here, which keeps the logic easy
to unit test.
"""

import logging
import re
import statistics
from collections import Counter
from collections.abc import Sequence
from datetime import datetime
from typing import Any

from .constants import LITELLM_PRICING_URL

logger = logging.getLogger(__name__)

# Matches a trailing model date stamp such as "-20250805" so display names stay
# readable without hardcoding any specific date.
_DATE_SUFFIX_PATTERN = re.compile(r"-\d{8}$")

# Cost fields on a LiteLLM pricing entry, mapped to the token field they price.
_COST_FIELDS = {
    "input": "input_cost_per_token",
    "output": "output_cost_per_token",
    "cache_create": "cache_creation_input_token_cost",
    "cache_read": "cache_read_input_token_cost",
}


def _shorten_model_name(
    model_name: str,
) -> str:
    """Convert a full model name into a short display name.

    Strips the ``claude-`` prefix and any trailing ``-YYYYMMDD`` date stamp. This
    is generic, so it works for any current or future model without code changes.

    Args:
        model_name: The full model name from ccusage.

    Returns:
        A shortened, human-friendly model name.
    """
    shortened = model_name.replace("claude-", "")
    return _DATE_SUFFIX_PATTERN.sub("", shortened)


def _day_date(
    day: dict[str, Any],
) -> str:
    """Return a day record's date, tolerating ccusage field renames.

    Older ccusage versions used ``date``; newer ones use ``period``. This helper
    reads whichever is present so the analyzer works across versions.

    Args:
        day: A single per-day usage record.

    Returns:
        The date string, or "unknown" if neither field is present.
    """
    return day.get("date") or day.get("period") or "unknown"


def _calculate_percentile(
    data: Sequence[float],
    percentile: int,
) -> float:
    """Calculate a percentile of a list using linear interpolation.

    Args:
        data: The values to summarize.
        percentile: The percentile to compute (0-100).

    Returns:
        The interpolated percentile value, or 0.0 for empty input.
    """
    if not data:
        return 0.0

    sorted_data = sorted(data)
    index = (percentile / 100) * (len(sorted_data) - 1)
    lower = int(index)
    upper = lower + 1
    weight = index - lower

    if upper >= len(sorted_data):
        return sorted_data[-1]

    return sorted_data[lower] * (1 - weight) + sorted_data[upper] * weight


def _summarize(
    values: Sequence[float],
    include_total: bool = True,
) -> dict[str, Any]:
    """Compute standard summary statistics for a list of values.

    Args:
        values: The values to summarize.
        include_total: Whether to include a summed total.

    Returns:
        A dictionary of summary statistics.
    """
    summary: dict[str, Any] = {
        "mean": statistics.mean(values),
        "median": statistics.median(values),
        "p95": _calculate_percentile(values, 95),
        "min": min(values),
        "max": max(values),
    }
    if include_total:
        summary["total"] = sum(values)
    return summary


def _breakdown_cost(
    breakdown: dict[str, Any],
    pricing: dict[str, Any],
) -> dict[str, float]:
    """Compute the cost of one model breakdown from its token counts.

    Args:
        breakdown: A single ``modelBreakdowns`` entry.
        pricing: The LiteLLM pricing entry for that model.

    Returns:
        A cost breakdown keyed by token type.
    """
    token_fields = {
        "input": "inputTokens",
        "output": "outputTokens",
        "cache_create": "cacheCreationTokens",
        "cache_read": "cacheReadTokens",
    }
    costs = {}
    for cost_key, price_key in _COST_FIELDS.items():
        token_count = breakdown.get(token_fields[cost_key], 0)
        costs[cost_key] = token_count * pricing.get(price_key, 0)
    return costs


def analyze_model_combinations(
    daily_data: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Count how often each combination of models was used on the same day.

    Args:
        daily_data: The per-day usage records from ccusage.

    Returns:
        Combinations sorted by descending number of days used.
    """
    combinations = []
    for day in daily_data:
        models_used = sorted(
            _shorten_model_name(b["modelName"]) for b in day.get("modelBreakdowns", [])
        )
        if models_used:
            combinations.append(tuple(models_used))

    counts = Counter(combinations)
    return [
        {"models": list(combo), "days": count}
        for combo, count in sorted(counts.items(), key=lambda x: x[1], reverse=True)
    ]


def _calculate_request_statistics(
    daily_data: list[dict[str, Any]],
) -> dict[str, Any]:
    """Compute per-request (per model-breakdown) token statistics.

    Args:
        daily_data: The per-day usage records from ccusage.

    Returns:
        Summary statistics for each token type across all breakdowns.
    """
    buckets: dict[str, list[int]] = {
        "input_tokens": [],
        "output_tokens": [],
        "cache_write_tokens": [],
        "cache_read_tokens": [],
        "total_tokens": [],
    }

    for day in daily_data:
        for breakdown in day.get("modelBreakdowns", []):
            input_tokens = breakdown.get("inputTokens", 0)
            output_tokens = breakdown.get("outputTokens", 0)
            cache_write = breakdown.get("cacheCreationTokens", 0)
            cache_read = breakdown.get("cacheReadTokens", 0)

            buckets["input_tokens"].append(input_tokens)
            buckets["output_tokens"].append(output_tokens)
            buckets["cache_write_tokens"].append(cache_write)
            buckets["cache_read_tokens"].append(cache_read)
            buckets["total_tokens"].append(input_tokens + output_tokens + cache_write + cache_read)

    result = {}
    for key, values in buckets.items():
        if values:
            result[key] = {
                "mean": statistics.mean(values),
                "median": statistics.median(values),
                "p75": _calculate_percentile(values, 75),
                "p95": _calculate_percentile(values, 95),
                "p99": _calculate_percentile(values, 99),
                "min": min(values),
                "max": max(values),
                "total": sum(values),
                "count": len(values),
            }
    return result


def _collect_daily_statistics(
    daily_data: list[dict[str, Any]],
    pricing_map: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Compute daily token and cost statistics.

    Args:
        daily_data: The per-day usage records from ccusage.
        pricing_map: Resolved pricing keyed by model name.

    Returns:
        Summary statistics for each daily metric.
    """
    metrics: dict[str, list[float]] = {
        "input_tokens": [],
        "output_tokens": [],
        "cache_create": [],
        "cache_read": [],
        "total_tokens": [],
        "total_cost": [],
        "cost_input": [],
        "cost_output": [],
        "cost_cache_create": [],
        "cost_cache_read": [],
        "cache_efficiency": [],
    }

    for day in daily_data:
        metrics["input_tokens"].append(day["inputTokens"])
        metrics["output_tokens"].append(day["outputTokens"])
        metrics["cache_create"].append(day["cacheCreationTokens"])
        metrics["cache_read"].append(day["cacheReadTokens"])
        metrics["total_tokens"].append(day["totalTokens"])
        metrics["total_cost"].append(day["totalCost"])

        day_costs = {"input": 0.0, "output": 0.0, "cache_create": 0.0, "cache_read": 0.0}
        for breakdown in day.get("modelBreakdowns", []):
            pricing = pricing_map.get(breakdown["modelName"])
            if pricing is None:
                continue
            for key, value in _breakdown_cost(breakdown, pricing).items():
                day_costs[key] += value

        metrics["cost_input"].append(day_costs["input"])
        metrics["cost_output"].append(day_costs["output"])
        metrics["cost_cache_create"].append(day_costs["cache_create"])
        metrics["cost_cache_read"].append(day_costs["cache_read"])

        total_tokens = day["totalTokens"]
        efficiency = (day["cacheReadTokens"] / total_tokens * 100) if total_tokens else 0
        metrics["cache_efficiency"].append(efficiency)

    daily_statistics = {}
    for key, values in metrics.items():
        if values:
            daily_statistics[key] = _summarize(
                values,
                include_total=(key != "cache_efficiency"),
            )
    return daily_statistics


def _collect_model_statistics(
    daily_data: list[dict[str, Any]],
    pricing_map: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Compute per-model token, cost, and pricing statistics.

    Args:
        daily_data: The per-day usage records from ccusage.
        pricing_map: Resolved pricing keyed by model name.

    Returns:
        Statistics keyed by shortened model display name.
    """
    per_model: dict[str, dict[str, Any]] = {}

    for day in daily_data:
        for breakdown in day.get("modelBreakdowns", []):
            model_name = breakdown["modelName"]
            data = per_model.setdefault(
                model_name,
                {
                    "input_tokens": [],
                    "output_tokens": [],
                    "cache_create": [],
                    "cache_read": [],
                    "total_cost": [],
                    "cost_input": [],
                    "cost_output": [],
                    "cost_cache_create": [],
                    "cost_cache_read": [],
                    "total_tokens": [],
                    "days_used": 0,
                },
            )

            data["days_used"] += 1
            data["input_tokens"].append(breakdown["inputTokens"])
            data["output_tokens"].append(breakdown["outputTokens"])
            data["cache_create"].append(breakdown["cacheCreationTokens"])
            data["cache_read"].append(breakdown["cacheReadTokens"])
            data["total_cost"].append(breakdown["cost"])
            data["total_tokens"].append(
                breakdown["inputTokens"]
                + breakdown["outputTokens"]
                + breakdown["cacheCreationTokens"]
                + breakdown["cacheReadTokens"]
            )

            pricing = pricing_map.get(model_name)
            if pricing is not None:
                costs = _breakdown_cost(breakdown, pricing)
                data["cost_input"].append(costs["input"])
                data["cost_output"].append(costs["output"])
                data["cost_cache_create"].append(costs["cache_create"])
                data["cost_cache_read"].append(costs["cache_read"])

    return _summarize_model_statistics(per_model, pricing_map)


def _summarize_model_statistics(
    per_model: dict[str, dict[str, Any]],
    pricing_map: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Turn accumulated per-model lists into summary statistics.

    Args:
        per_model: Accumulated raw values keyed by full model name.
        pricing_map: Resolved pricing keyed by model name.

    Returns:
        Statistics keyed by shortened model display name.
    """
    stat_keys = [
        "input_tokens",
        "output_tokens",
        "cache_create",
        "cache_read",
        "total_cost",
        "total_tokens",
        "cost_input",
        "cost_output",
        "cost_cache_create",
        "cost_cache_read",
    ]

    model_statistics = {}
    for model_name, data in per_model.items():
        display_name = _shorten_model_name(model_name)

        stats = {}
        for key in stat_keys:
            values = data[key]
            if values:
                stats[key] = {
                    "mean": statistics.mean(values),
                    "median": statistics.median(values),
                    "p95": _calculate_percentile(values, 95),
                    "total": sum(values),
                }

        total_tokens = sum(data["total_tokens"])
        cache_efficiency = sum(data["cache_read"]) / total_tokens * 100 if total_tokens else 0

        pricing_per_million = {}
        pricing = pricing_map.get(model_name)
        if pricing is not None:
            pricing_per_million = {
                cost_key: pricing.get(price_key, 0) * 1_000_000
                for cost_key, price_key in _COST_FIELDS.items()
            }

        model_statistics[display_name] = {
            "days_used": data["days_used"],
            "cache_efficiency": cache_efficiency,
            "pricing_per_million_tokens": pricing_per_million,
            "statistics": stats,
        }

    return model_statistics


def perform_complete_analysis(
    raw_data: dict[str, Any],
    pricing_map: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Perform the complete analysis and return a structured result.

    Args:
        raw_data: Parsed ccusage data with ``daily`` and ``totals`` keys.
        pricing_map: Resolved pricing keyed by model name.

    Returns:
        The complete analysis dictionary ready for serialization and reporting.
    """
    logger.info("Performing complete analysis...")

    daily_data = raw_data["daily"]
    totals = raw_data["totals"]

    total_tokens = totals["totalTokens"]
    overall_cache_efficiency = totals["cacheReadTokens"] / total_tokens * 100 if total_tokens else 0

    return {
        "metadata": {
            "analysis_period": {
                "start_date": min(_day_date(day) for day in daily_data),
                "end_date": max(_day_date(day) for day in daily_data),
                "total_days": len(daily_data),
            },
            "generated_at": datetime.now().isoformat(),
            "source": "ccusage CLI tool",
            "pricing_source": LITELLM_PRICING_URL,
        },
        "summary": {
            "total_cost": totals["totalCost"],
            "total_tokens": total_tokens,
            "total_input_tokens": totals["inputTokens"],
            "total_output_tokens": totals["outputTokens"],
            "total_cache_creation_tokens": totals["cacheCreationTokens"],
            "total_cache_read_tokens": totals["cacheReadTokens"],
            "overall_cache_efficiency": overall_cache_efficiency,
        },
        "model_combinations": analyze_model_combinations(daily_data),
        "daily_statistics": _collect_daily_statistics(daily_data, pricing_map),
        "request_statistics": _calculate_request_statistics(daily_data),
        "model_statistics": _collect_model_statistics(daily_data, pricing_map),
    }
