"""Shared constants for the Claude Code usage analyzer."""

# LiteLLM publishes an up-to-date pricing table for every model it supports.
# We resolve pricing dynamically against this file so new models work without
# any code change. Documentation: https://github.com/BerriAI/litellm
LITELLM_PRICING_URL: str = (
    "https://raw.githubusercontent.com/BerriAI/litellm/main/model_prices_and_context_window.json"
)

# The ccusage npm package reads Claude Code's local usage JSONL files and
# aggregates them per day and per model. Docs: https://www.npmjs.com/package/ccusage
CCUSAGE_PACKAGE: str = "ccusage@latest"

# Default start date (YYYYMMDD) used when the caller does not pass --since.
DEFAULT_SINCE_DATE: str = "20250101"

# Network and subprocess timeouts, in seconds.
PRICING_FETCH_TIMEOUT_SECONDS: int = 30
CCUSAGE_FETCH_TIMEOUT_SECONDS: int = 300

# Assumed length of a working day, used only for the per-minute usage estimates.
MINUTES_PER_WORKDAY: int = 8 * 60

# Default file locations, relative to the current working directory.
DEFAULT_RAW_DATA_PATH: str = "data/raw/claude-usage-raw.json"
DEFAULT_OUTPUT_DIR: str = "data/output"
