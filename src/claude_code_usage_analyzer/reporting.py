"""Generate Markdown and Quarto reports from an analysis result.

These functions only format an already-computed analysis dictionary. They do no
calculation of their own, so the same numbers appear in every output format.
"""

import logging
from datetime import datetime
from typing import Any

from .constants import MINUTES_PER_WORKDAY

logger = logging.getLogger(__name__)


def _fmt_num(
    num: float,
    decimals: int = 2,
) -> str:
    """Format a number with thousands separators.

    Args:
        num: The value to format.
        decimals: Number of decimal places (0 renders an integer).

    Returns:
        The formatted string.
    """
    if decimals == 0:
        return f"{int(num):,}"
    return f"{num:,.{decimals}f}"


def _fmt_cost(
    cost: float,
) -> str:
    """Format a value as a US dollar amount.

    Args:
        cost: The dollar value.

    Returns:
        The formatted string, e.g. ``$31.93``.
    """
    return f"${_fmt_num(cost, 2)}"


def _per_minute_lines(
    daily_stats: dict[str, Any],
    stat_key: str,
) -> tuple[float, float, str]:
    """Compute per-minute usage figures for one statistic (mean/median/p95).

    Args:
        daily_stats: The ``daily_statistics`` section of the analysis.
        stat_key: Which statistic to use (``mean``, ``median``, or ``p95``).

    Returns:
        A tuple of (tokens per minute, cost per minute, breakdown sentence).
    """
    total_tokens = daily_stats["total_tokens"][stat_key]
    cost = daily_stats["total_cost"][stat_key]
    tokens_per_min = total_tokens / MINUTES_PER_WORKDAY
    cost_per_min = cost / MINUTES_PER_WORKDAY

    breakdown = (
        f"{_fmt_num(daily_stats['input_tokens'][stat_key] / MINUTES_PER_WORKDAY, 0)} input, "
        f"{_fmt_num(daily_stats['output_tokens'][stat_key] / MINUTES_PER_WORKDAY, 0)} output, "
        f"{_fmt_num(daily_stats['cache_create'][stat_key] / MINUTES_PER_WORKDAY, 0)} cache create, "
        f"{_fmt_num(daily_stats['cache_read'][stat_key] / MINUTES_PER_WORKDAY, 0)} cache read"
    )
    return tokens_per_min, cost_per_min, breakdown


def _append_request_stats_table(
    report: list[str],
    request_stats: dict[str, Any],
) -> None:
    """Append the per-request token statistics table to the report.

    Args:
        report: The list of report lines being built.
        request_stats: The ``request_statistics`` section of the analysis.
    """
    report.append("| Token Type | Count | Mean | Median | P75 | P95 | Max |")
    report.append("|------------|-------|------|--------|-----|-----|-----|")
    rows = [
        ("input_tokens", "Input Tokens"),
        ("output_tokens", "Output Tokens"),
        ("cache_write_tokens", "Cache Write"),
        ("cache_read_tokens", "Cache Read"),
        ("total_tokens", "Total Tokens"),
    ]
    for key, label in rows:
        if key in request_stats:
            s = request_stats[key]
            report.append(
                f"| **{label}** | {s['count']} | "
                f"{_fmt_num(s['mean'], 0)} | {_fmt_num(s['median'], 0)} | "
                f"{_fmt_num(s['p75'], 0)} | {_fmt_num(s['p95'], 0)} | "
                f"{_fmt_num(s['max'], 0)} |"
            )
    report.append("")


def _append_daily_token_table(
    report: list[str],
    daily_stats: dict[str, Any],
) -> None:
    """Append the daily token usage statistics table.

    Args:
        report: The list of report lines being built.
        daily_stats: The ``daily_statistics`` section of the analysis.
    """
    report.append("| Token Type | Mean | Median | P95 | Min | Max |")
    report.append("|------------|------|--------|-----|-----|-----|")
    rows = [
        ("input_tokens", "Input Tokens"),
        ("output_tokens", "Output Tokens"),
        ("cache_create", "Cache Creation"),
        ("cache_read", "Cache Read"),
        ("total_tokens", "Total Tokens"),
    ]
    for key, label in rows:
        s = daily_stats[key]
        report.append(
            f"| **{label}** | {_fmt_num(s['mean'], 0)} | {_fmt_num(s['median'], 0)} | "
            f"{_fmt_num(s['p95'], 0)} | {_fmt_num(s['min'], 0)} | {_fmt_num(s['max'], 0)} |"
        )
    report.append("")


def _append_cost_breakdown_table(
    report: list[str],
    daily_stats: dict[str, Any],
) -> None:
    """Append the daily cost breakdown by token type table.

    Args:
        report: The list of report lines being built.
        daily_stats: The ``daily_statistics`` section of the analysis.
    """
    report.append("| Token Type | Mean | Median | P95 | Total | % of Total |")
    report.append("|------------|------|--------|-----|-------|------------|")
    total_cost = daily_stats["total_cost"]["total"]
    rows = [
        ("cost_input", "Input Tokens"),
        ("cost_output", "Output Tokens"),
        ("cost_cache_create", "Cache Creation"),
        ("cost_cache_read", "Cache Read"),
    ]
    for key, label in rows:
        s = daily_stats[key]
        pct = (s["total"] / total_cost * 100) if total_cost else 0
        report.append(
            f"| **{label}** | {_fmt_cost(s['mean'])} | {_fmt_cost(s['median'])} | "
            f"{_fmt_cost(s['p95'])} | {_fmt_cost(s['total'])} | {_fmt_num(pct)}% |"
        )
    report.append("")


def _append_model_section(
    report: list[str],
    model_name: str,
    stats: dict[str, Any],
) -> None:
    """Append a per-model analysis section to a Markdown report.

    Args:
        report: The list of report lines being built.
        model_name: The shortened model display name.
        stats: The statistics dictionary for this model.
    """
    report.append(f"### {model_name}")
    report.append("")
    report.append(f"**Days Used:** {stats['days_used']}")
    report.append(f"**Cache Efficiency:** {_fmt_num(stats['cache_efficiency'])}%")
    report.append("")

    pricing = stats["pricing_per_million_tokens"]
    if pricing:
        report.append("**Pricing (per million tokens):**")
        report.append(f"- Input: ${_fmt_num(pricing['input'], 2)}")
        report.append(f"- Output: ${_fmt_num(pricing['output'], 2)}")
        report.append(f"- Cache Creation: ${_fmt_num(pricing['cache_create'], 2)}")
        report.append(f"- Cache Read: ${_fmt_num(pricing['cache_read'], 2)}")
        report.append("")

    report.append("#### Cost Breakdown by Token Type")
    report.append("")
    report.append("| Cost Type | Mean | Median | P95 | Total | % of Model Cost |")
    report.append("|-----------|------|--------|-----|-------|-----------------|")
    model_total = stats["statistics"]["total_cost"]["total"]
    cost_rows = [
        ("cost_input", "Input Tokens"),
        ("cost_output", "Output Tokens"),
        ("cost_cache_create", "Cache Creation"),
        ("cost_cache_read", "Cache Read"),
    ]
    for key, label in cost_rows:
        if key in stats["statistics"]:
            s = stats["statistics"][key]
            pct = (s["total"] / model_total * 100) if model_total else 0
            report.append(
                f"| **{label}** | {_fmt_cost(s['mean'])} | {_fmt_cost(s['median'])} | "
                f"{_fmt_cost(s['p95'])} | {_fmt_cost(s['total'])} | {_fmt_num(pct)}% |"
            )
    tc = stats["statistics"]["total_cost"]
    report.append(
        f"| **TOTAL** | {_fmt_cost(tc['mean'])} | {_fmt_cost(tc['median'])} | "
        f"{_fmt_cost(tc['p95'])} | {_fmt_cost(tc['total'])} | 100.00% |"
    )
    report.append("")

    report.append("#### Token Statistics")
    report.append("")
    report.append("| Token Type | Mean | Median | P95 | Total |")
    report.append("|------------|------|--------|-----|-------|")
    token_rows = [
        ("input_tokens", "Input"),
        ("output_tokens", "Output"),
        ("cache_create", "Cache Create"),
        ("cache_read", "Cache Read"),
        ("total_tokens", "Total"),
    ]
    for key, label in token_rows:
        s = stats["statistics"][key]
        report.append(
            f"| **{label}** | {_fmt_num(s['mean'], 0)} | {_fmt_num(s['median'], 0)} | "
            f"{_fmt_num(s['p95'], 0)} | {_fmt_num(s['total'], 0)} |"
        )
    report.append("")


def _cache_efficiency_label(
    efficiency: float,
) -> str:
    """Map a cache-efficiency percentage to a descriptive word.

    Args:
        efficiency: The cache-efficiency percentage.

    Returns:
        One of "excellent", "very good", "good", or "moderate".
    """
    if efficiency > 90:
        return "excellent"
    if efficiency > 80:
        return "very good"
    if efficiency > 70:
        return "good"
    return "moderate"


def generate_markdown_report(
    analysis: dict[str, Any],
) -> str:
    """Generate a human-readable Markdown report from an analysis result.

    Args:
        analysis: The complete analysis dictionary.

    Returns:
        The report as a single Markdown string.
    """
    logger.info("Generating Markdown report...")

    meta = analysis["metadata"]
    summary = analysis["summary"]
    daily_stats = analysis["daily_statistics"]
    request_stats = analysis.get("request_statistics", {})
    model_stats = analysis["model_statistics"]
    model_combos = analysis["model_combinations"]

    report: list[str] = []
    period = meta["analysis_period"]
    generated = datetime.fromisoformat(meta["generated_at"]).strftime("%Y-%m-%d %H:%M:%S")

    report.append("# Claude Code Usage Analysis Report")
    report.append("")
    report.append(
        f"**Analysis Period:** {period['start_date']} to {period['end_date']} "
        f"({period['total_days']} days)"
    )
    report.append(f"**Report Generated:** {generated}")
    report.append("")

    report.append("## Executive Summary")
    report.append("")
    report.append(f"- **Total Cost:** {_fmt_cost(summary['total_cost'])}")
    report.append(f"- **Total Tokens:** {_fmt_num(summary['total_tokens'], 0)}")
    report.append(f"- **Total Input Tokens:** {_fmt_num(summary['total_input_tokens'], 0)}")
    report.append(f"- **Total Output Tokens:** {_fmt_num(summary['total_output_tokens'], 0)}")
    report.append(
        f"- **Cache Creation Tokens:** {_fmt_num(summary['total_cache_creation_tokens'], 0)}"
    )
    report.append(f"- **Cache Read Tokens:** {_fmt_num(summary['total_cache_read_tokens'], 0)}")
    report.append(
        f"- **Overall Cache Efficiency:** {_fmt_num(summary['overall_cache_efficiency'])}%"
    )
    report.append("")

    if request_stats:
        report.append("## Per-Request Token Statistics")
        report.append("")
        report.append("Analysis of token usage across individual requests:")
        report.append("")
        _append_request_stats_table(report, request_stats)

    report.append("### Estimated Usage Per Minute (8-hour workday)")
    report.append("")
    for stat_key, label in [("mean", "Mean"), ("median", "Median"), ("p95", "P95")]:
        tokens_per_min, cost_per_min, breakdown = _per_minute_lines(daily_stats, stat_key)
        daily_cost = daily_stats["total_cost"][stat_key]
        daily_tokens = daily_stats["total_tokens"][stat_key]
        report.append(
            f"- **{label} Usage:** {_fmt_num(tokens_per_min, 0)} tokens per minute at "
            f"{_fmt_cost(cost_per_min)} per minute, i.e. a daily spend of "
            f"{_fmt_cost(daily_cost)} for {_fmt_num(daily_tokens, 0)} total tokens."
        )
        report.append(f"  - Per minute: {breakdown}.")
    report.append("")

    report.append("## Model Usage Patterns")
    report.append("")
    report.append("**Model Combinations Used:**")
    report.append("")
    for combo in model_combos:
        report.append(f"- **{' + '.join(combo['models'])}**: {combo['days']} days")
    report.append("")

    report.append("## Daily Cost Analysis")
    report.append("")
    report.append("### Total Daily Cost")
    report.append("")
    report.append("| Metric | Mean | Median | P95 | Min | Max |")
    report.append("|--------|------|--------|-----|-----|-----|")
    tc = daily_stats["total_cost"]
    report.append(
        f"| **Total Cost** | {_fmt_cost(tc['mean'])} | {_fmt_cost(tc['median'])} | "
        f"{_fmt_cost(tc['p95'])} | {_fmt_cost(tc['min'])} | {_fmt_cost(tc['max'])} |"
    )
    report.append("")
    report.append("### Daily Cost Breakdown by Token Type")
    report.append("")
    _append_cost_breakdown_table(report, daily_stats)

    report.append("## Daily Token Usage Statistics")
    report.append("")
    _append_daily_token_table(report, daily_stats)

    report.append("## Cache Efficiency Analysis")
    report.append("")
    report.append(
        "**Cache efficiency** is calculated as: `(Cache Read Tokens / Total Tokens) x 100`"
    )
    report.append("")
    report.append("| Metric | Mean | Median | P95 | Min | Max |")
    report.append("|--------|------|--------|-----|-----|-----|")
    ce = daily_stats["cache_efficiency"]
    report.append(
        f"| **Cache Efficiency** | {_fmt_num(ce['mean'])}% | {_fmt_num(ce['median'])}% | "
        f"{_fmt_num(ce['p95'])}% | {_fmt_num(ce['min'])}% | {_fmt_num(ce['max'])}% |"
    )
    report.append("")

    report.append("## Model-Specific Analysis")
    report.append("")
    sorted_models = sorted(
        model_stats.items(),
        key=lambda x: x[1]["statistics"]["total_cost"]["total"],
        reverse=True,
    )
    for model_name, stats in sorted_models:
        _append_model_section(report, model_name, stats)

    _append_key_insights(report, analysis, sorted_models)

    return "\n".join(report)


def _append_key_insights(
    report: list[str],
    analysis: dict[str, Any],
    sorted_models: list[tuple[str, dict[str, Any]]],
) -> None:
    """Append the key-insights section to a Markdown report.

    Args:
        report: The list of report lines being built.
        analysis: The complete analysis dictionary.
        sorted_models: Models sorted by descending total cost.
    """
    daily_stats = analysis["daily_statistics"]
    summary = analysis["summary"]

    avg_cost = daily_stats["total_cost"]["mean"]
    avg_input = daily_stats["cost_input"]["mean"]
    avg_output = daily_stats["cost_output"]["mean"]
    avg_cache_create = daily_stats["cost_cache_create"]["mean"]
    avg_cache_read = daily_stats["cost_cache_read"]["mean"]

    report.append("## Key Insights")
    report.append("")
    report.append(
        f"1. **Daily Cost Composition:** Your average daily cost of "
        f"{_fmt_cost(avg_cost)} breaks down as:"
    )
    if avg_cost:
        for label, value in [
            ("Input tokens", avg_input),
            ("Output tokens", avg_output),
            ("Cache creation", avg_cache_create),
            ("Cache reads", avg_cache_read),
        ]:
            pct = _fmt_num(value / avg_cost * 100)
            report.append(f"   - {label}: {_fmt_cost(value)} ({pct}%)")
    report.append("")

    p95_cost = daily_stats["total_cost"]["p95"]
    if avg_cost:
        report.append(
            f"2. **Cost Variability:** With a P95 of {_fmt_cost(p95_cost)}, your "
            f"highest usage days cost approximately {_fmt_num(p95_cost / avg_cost, 1)}x "
            "the average."
        )
        report.append("")

    avg_efficiency = daily_stats["cache_efficiency"]["mean"]
    report.append(
        f"3. **Cache Utilization:** Your average cache efficiency of "
        f"{_fmt_num(avg_efficiency)}% is {_cache_efficiency_label(avg_efficiency)}, "
        "significantly reducing processing costs."
    )
    report.append("")

    if sorted_models:
        primary_model = sorted_models[0]
        model_cost = primary_model[1]["statistics"]["total_cost"]["total"]
        total_cost = summary["total_cost"]
        model_pct = (model_cost / total_cost * 100) if total_cost else 0
        report.append(
            f"4. **Primary Model:** {primary_model[0]} accounts for "
            f"{_fmt_cost(model_cost)} ({_fmt_num(model_pct)}%) of total costs."
        )
        report.append("")

    report.append(
        f"5. **Monthly Projection:** Based on average daily cost, projected monthly "
        f"cost is approximately {_fmt_cost(avg_cost * 30)}."
    )
    report.append("")
