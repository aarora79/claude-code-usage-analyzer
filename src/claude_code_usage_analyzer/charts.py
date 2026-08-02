"""Optional matplotlib charts for token distributions.

Charts are a best-effort extra. If matplotlib is not installed the functions
return None instead of failing, so the core JSON and Markdown reports always work.
"""

import logging
from pathlib import Path
from typing import Any

try:
    import matplotlib

    matplotlib.use("Agg")  # Non-interactive backend, safe for headless runs.
    import matplotlib.pyplot as plt

    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False


logger = logging.getLogger(__name__)

_TOKEN_TYPES = [
    ("input_tokens", "Input Tokens"),
    ("output_tokens", "Output Tokens"),
    ("cache_write_tokens", "Cache Write Tokens"),
    ("cache_read_tokens", "Cache Read Tokens"),
    ("total_tokens", "Total Tokens"),
]


def _thousands_formatter(
    value: float,
    _position: int,
) -> str:
    """Format an axis tick value with thousands separators.

    Args:
        value: The tick value.
        _position: Unused tick position (required by matplotlib).

    Returns:
        The formatted tick label.
    """
    return f"{int(value):,}"


def _annotate_bars(
    axis: Any,
    bars: Any,
) -> None:
    """Write the numeric value above each bar.

    Args:
        axis: The matplotlib axis.
        bars: The bar container returned by ``ax.bar``.
    """
    for bar in bars:
        height = bar.get_height()
        axis.text(
            bar.get_x() + bar.get_width() / 2.0,
            height,
            f"{int(height):,}",
            ha="center",
            va="bottom",
            fontweight="bold",
            fontsize=8,
        )


def generate_token_distribution_chart(
    analysis: dict[str, Any],
    output_dir: Path,
) -> Path | None:
    """Generate a min/P95/max bar chart per token type.

    Args:
        analysis: The complete analysis dictionary.
        output_dir: Directory to write the chart into.

    Returns:
        The chart path, or None if matplotlib is unavailable or there is no data.
    """
    request_stats = analysis.get("request_statistics", {})
    if not MATPLOTLIB_AVAILABLE or not request_stats:
        return None

    output_dir.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle("Token Usage Distribution Analysis", fontsize=16, fontweight="bold")

    colors = ["#3498db", "#e74c3c", "#2ecc71"]
    for idx, (key, label) in enumerate(_TOKEN_TYPES[:4]):
        axis = axes[idx // 2, idx % 2]
        if key not in request_stats:
            continue
        stats = request_stats[key]
        data = [stats.get("min", 0), stats.get("p95", 0), stats.get("max", 0)]
        bars = axis.bar(["Min", "P95", "Max"], data, color=colors, alpha=0.7, edgecolor="black")
        axis.set_ylabel("Token Count", fontweight="bold")
        axis.set_title(label, fontweight="bold")
        axis.yaxis.set_major_formatter(plt.FuncFormatter(_thousands_formatter))
        _annotate_bars(axis, bars)

    plt.tight_layout()
    chart_path = output_dir / "token-distribution.png"
    plt.savefig(chart_path, dpi=100, bbox_inches="tight")
    plt.close(fig)
    logger.info("Token distribution chart saved to: %s", chart_path)
    return chart_path


def generate_token_histogram(
    analysis: dict[str, Any],
    output_dir: Path,
) -> Path | None:
    """Generate a mean/median/P75/P95/max bar chart per token type.

    Args:
        analysis: The complete analysis dictionary.
        output_dir: Directory to write the chart into.

    Returns:
        The chart path, or None if matplotlib is unavailable or there is no data.
    """
    request_stats = analysis.get("request_statistics", {})
    if not MATPLOTLIB_AVAILABLE or not request_stats:
        return None

    output_dir.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(2, 3, figsize=(16, 10))
    fig.suptitle("Token Metrics: Mean, Median, P75, P95, Max", fontsize=16, fontweight="bold")

    metrics = ["mean", "median", "p75", "p95", "max"]
    labels = ["Mean", "Median", "P75", "P95", "Max"]
    colors = ["#3498db", "#2ecc71", "#f39c12", "#e74c3c", "#9b59b6"]

    for idx, (key, label) in enumerate(_TOKEN_TYPES):
        axis = axes[idx // 3, idx % 3]
        if key not in request_stats:
            continue
        stats = request_stats[key]
        values = [stats.get(m, 0) for m in metrics]
        bars = axis.bar(labels, values, color=colors, alpha=0.7, edgecolor="black")
        axis.set_ylabel("Token Count", fontweight="bold")
        axis.set_title(label, fontweight="bold")
        axis.yaxis.set_major_formatter(plt.FuncFormatter(_thousands_formatter))
        axis.tick_params(axis="x", rotation=45)
        _annotate_bars(axis, bars)

    axes[1, 2].axis("off")
    plt.tight_layout()
    chart_path = output_dir / "token-histogram.png"
    plt.savefig(chart_path, dpi=100, bbox_inches="tight")
    plt.close(fig)
    logger.info("Token histogram saved to: %s", chart_path)
    return chart_path
