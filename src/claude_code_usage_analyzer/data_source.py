"""Fetch and load raw Claude Code usage data via the ccusage CLI."""

import json
import logging
import shutil
import subprocess  # nosec B404 - used only with a hardcoded command and list args
from pathlib import Path
from typing import Any

from .constants import (
    CCUSAGE_FETCH_TIMEOUT_SECONDS,
    CCUSAGE_PACKAGE,
)

logger = logging.getLogger(__name__)


class DataSourceError(Exception):
    """Raised when usage data cannot be fetched or parsed."""


def _build_ccusage_command(
    since_date: str,
) -> list[str]:
    """Build the ccusage command as an argument list.

    The executable (``npx``) and all flags are hardcoded. Only the validated
    ``since_date`` is passed as a separate list argument, never interpolated
    into a shell string, so there is no shell-injection surface.

    Args:
        since_date: Start date in YYYYMMDD format.

    Returns:
        The command and arguments as a list.
    """
    return [
        "npx",
        CCUSAGE_PACKAGE,
        "daily",
        "--since",
        since_date,
        "--breakdown",
        "--json",
    ]


def _strip_ccusage_noise(
    content: str,
) -> str:
    """Remove non-JSON banner lines ccusage may print before the JSON body.

    Args:
        content: Raw stdout captured from ccusage.

    Returns:
        The content starting at the first JSON object.
    """
    brace_index = content.find("{")
    if brace_index <= 0:
        return content
    return content[brace_index:]


def fetch_raw_usage_data(
    since_date: str,
    output_path: Path,
) -> None:
    """Fetch raw usage data using the ccusage CLI and write it to a file.

    Args:
        since_date: Start date in YYYYMMDD format.
        output_path: Where to write the fetched JSON.

    Raises:
        DataSourceError: If npx/ccusage is unavailable, times out, or fails.
    """
    if shutil.which("npx") is None:
        raise DataSourceError(
            "The 'npx' command was not found. Install Node.js and npm "
            "(https://nodejs.org/) so the tool can run "
            f"'npx {CCUSAGE_PACKAGE}'."
        )

    command = _build_ccusage_command(since_date)
    logger.info("Fetching usage data from ccusage (since %s)...", since_date)

    try:
        # Safety: hardcoded executable, list args, no shell; since_date is a
        # discrete argument, not interpolated into a command string.
        result = subprocess.run(  # noqa: S603  # nosec B603
            command,
            capture_output=True,
            text=True,
            check=True,
            timeout=CCUSAGE_FETCH_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired as exc:
        raise DataSourceError(
            f"ccusage timed out after {CCUSAGE_FETCH_TIMEOUT_SECONDS} seconds."
        ) from exc
    except subprocess.CalledProcessError as exc:
        raise DataSourceError(
            f"ccusage failed (exit code {exc.returncode}). stderr: {exc.stderr.strip()}"
        ) from exc

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(result.stdout, encoding="utf-8")
    logger.info("Raw usage data saved to: %s", output_path)


def load_raw_usage_data(
    raw_data_path: Path,
) -> dict[str, Any]:
    """Load and parse cached raw usage data from disk.

    Args:
        raw_data_path: Path to the cached ccusage JSON file.

    Returns:
        The parsed ccusage data (with ``daily`` and ``totals`` keys).

    Raises:
        DataSourceError: If the file is missing, empty, or not valid JSON.
    """
    if not raw_data_path.exists():
        raise DataSourceError(f"Raw data file not found: {raw_data_path}")

    content = raw_data_path.read_text(encoding="utf-8")
    content = _strip_ccusage_noise(content)

    try:
        data = json.loads(content)
    except json.JSONDecodeError as exc:
        raise DataSourceError(f"Raw usage file {raw_data_path} is not valid JSON: {exc}") from exc

    if "daily" not in data or "totals" not in data:
        raise DataSourceError(
            f"Raw usage file {raw_data_path} is missing expected "
            "'daily'/'totals' keys. Re-fetch with --refresh."
        )

    return data
