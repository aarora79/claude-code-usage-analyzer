#!/usr/bin/env python3
"""Command-line entry point for the Claude Code usage analyzer.

Control flow:
1. Parse arguments.
2. Fetch raw usage data via ccusage (or reuse the cache).
3. Resolve model pricing dynamically from LiteLLM.
4. Perform the analysis.
5. Write JSON, Markdown, Quarto, and chart outputs.
"""

import argparse
import json
import logging
import time
from pathlib import Path

from .analysis import perform_complete_analysis
from .charts import (
    generate_token_distribution_chart,
    generate_token_histogram,
)
from .constants import (
    DEFAULT_OUTPUT_DIR,
    DEFAULT_RAW_DATA_PATH,
    DEFAULT_SINCE_DATE,
)
from .dashboard import generate_dashboard_html
from .data_source import (
    fetch_raw_usage_data,
    load_raw_usage_data,
)
from .pricing import resolve_pricing_map
from .reporting import generate_markdown_report

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s,p%(process)s,{%(filename)s:%(lineno)d},%(levelname)s,%(message)s",
)
logger = logging.getLogger(__name__)


def _parse_args() -> argparse.Namespace:
    """Parse command-line arguments.

    Returns:
        The parsed argument namespace.
    """
    parser = argparse.ArgumentParser(
        description="Analyze Claude Code usage and generate cost reports.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze usage (fetches data automatically if needed)
  uv run claude-usage-analyzer

  # Specify a custom start date (YYYYMMDD)
  uv run claude-usage-analyzer --since 20260101

  # Force a re-fetch of the raw data
  uv run claude-usage-analyzer --refresh

  # Enable verbose debug logging
  uv run claude-usage-analyzer --debug
""",
    )
    parser.add_argument(
        "--since",
        type=str,
        default=DEFAULT_SINCE_DATE,
        help=f"Start date for usage data in YYYYMMDD format (default: {DEFAULT_SINCE_DATE}).",
    )
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Force re-fetch of raw usage data even if a cache exists.",
    )
    parser.add_argument(
        "--raw-data-path",
        type=str,
        default=DEFAULT_RAW_DATA_PATH,
        help=f"Path to the raw ccusage cache (default: {DEFAULT_RAW_DATA_PATH}).",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=DEFAULT_OUTPUT_DIR,
        help=f"Directory for generated reports (default: {DEFAULT_OUTPUT_DIR}).",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable verbose debug logging.",
    )
    return parser.parse_args()


def _ensure_raw_data(
    raw_data_path: Path,
    since_date: str,
    refresh: bool,
) -> None:
    """Fetch raw usage data if it is missing or a refresh was requested.

    Args:
        raw_data_path: Path to the raw ccusage cache.
        since_date: Start date in YYYYMMDD format.
        refresh: Whether to force a re-fetch.
    """
    if raw_data_path.exists() and not refresh:
        logger.info("Using cached raw usage data at %s", raw_data_path)
        return

    reason = "Refresh requested" if refresh else "No cached raw data found"
    logger.info("%s; fetching from ccusage.", reason)
    fetch_raw_usage_data(since_date, raw_data_path)


def _collect_model_names(
    raw_data: dict,
) -> list[str]:
    """Collect every model name that appears in the usage data.

    Args:
        raw_data: Parsed ccusage data.

    Returns:
        The list of model names (with duplicates).
    """
    model_names = []
    for day in raw_data["daily"]:
        for breakdown in day.get("modelBreakdowns", []):
            model_names.append(breakdown["modelName"])
    return model_names


def _write_outputs(
    analysis: dict,
    output_dir: Path,
) -> None:
    """Write the JSON, Markdown, Quarto, and chart outputs.

    Args:
        analysis: The complete analysis dictionary.
        output_dir: Directory for the generated files.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    json_file = output_dir / "claude-usage-analysis.json"
    json_file.write_text(json.dumps(analysis, indent=2), encoding="utf-8")
    logger.info("Saved analysis JSON to: %s", json_file)

    md_file = output_dir / "claude-usage-report.md"
    md_file.write_text(generate_markdown_report(analysis), encoding="utf-8")
    logger.info("Saved Markdown report to: %s", md_file)

    dashboard_file = output_dir / "tokenomics-dashboard.html"
    dashboard_file.write_text(generate_dashboard_html(analysis), encoding="utf-8")
    logger.info("Saved HTML dashboard to: %s", dashboard_file)

    if generate_token_distribution_chart(analysis, output_dir) is None:
        logger.info("Skipped distribution chart (matplotlib unavailable or no data).")
    if generate_token_histogram(analysis, output_dir) is None:
        logger.info("Skipped histogram (matplotlib unavailable or no data).")


def _log_summary(
    analysis: dict,
    elapsed_seconds: float,
) -> None:
    """Log a short summary of the analysis result.

    Args:
        analysis: The complete analysis dictionary.
        elapsed_seconds: Wall-clock time the run took.
    """
    summary = analysis["summary"]
    logger.info("Analysis complete in %.1f seconds.", elapsed_seconds)
    logger.info("Total Cost: $%.2f", summary["total_cost"])
    logger.info("Total Tokens: %s", f"{summary['total_tokens']:,}")
    logger.info("Cache Efficiency: %.2f%%", summary["overall_cache_efficiency"])


def main() -> None:
    """Orchestrate the full analyze-and-report flow."""
    args = _parse_args()
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    start_time = time.time()
    raw_data_path = Path(args.raw_data_path)
    output_dir = Path(args.output_dir)

    _ensure_raw_data(raw_data_path, args.since, args.refresh)
    raw_data = load_raw_usage_data(raw_data_path)

    pricing_map = resolve_pricing_map(_collect_model_names(raw_data))
    analysis = perform_complete_analysis(raw_data, pricing_map)

    _write_outputs(analysis, output_dir)
    _log_summary(analysis, time.time() - start_time)


if __name__ == "__main__":
    main()
