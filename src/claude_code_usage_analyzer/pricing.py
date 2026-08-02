"""Resolve per-model pricing from the LiteLLM pricing table.

The previous version of this tool hardcoded a fixed set of model IDs (Opus 4.1,
Sonnet 4, Sonnet 4.5). Any model outside that list was silently dropped, so when
Claude Code moved to newer models their cost breakdowns showed as zero.

This module instead resolves pricing dynamically: it takes whatever model names
actually appear in the usage data and looks each one up in LiteLLM, so new models
work with no code change.
"""

import json
import logging
import urllib.request
from functools import lru_cache
from typing import Any

from .constants import (
    LITELLM_PRICING_URL,
    PRICING_FETCH_TIMEOUT_SECONDS,
)

logger = logging.getLogger(__name__)


class PricingError(Exception):
    """Raised when model pricing cannot be fetched or parsed."""


@lru_cache(maxsize=1)
def _download_pricing_table() -> dict[str, Any]:
    """Download and parse the full LiteLLM pricing table.

    Cached so repeated lookups within a run hit the network only once.

    Returns:
        The raw LiteLLM pricing dictionary keyed by model name.

    Raises:
        PricingError: If the table cannot be downloaded or parsed.
    """
    logger.info("Fetching model pricing from LiteLLM...")
    try:
        # Safety: the URL is a fixed HTTPS vendor constant, never user input.
        request = urllib.request.Request(  # noqa: S310  # nosec B310
            LITELLM_PRICING_URL,
            headers={"User-Agent": "claude-code-usage-analyzer"},
        )
        with urllib.request.urlopen(  # noqa: S310  # nosec B310
            request,
            timeout=PRICING_FETCH_TIMEOUT_SECONDS,
        ) as response:
            return json.loads(response.read())
    except (urllib.error.URLError, TimeoutError) as exc:
        raise PricingError(
            f"Failed to fetch pricing from LiteLLM ({LITELLM_PRICING_URL}). "
            f"Check your internet connection and try again. Details: {exc}"
        ) from exc
    except json.JSONDecodeError as exc:
        raise PricingError(f"LiteLLM pricing table was not valid JSON: {exc}") from exc


def _match_pricing_key(
    model_name: str,
    pricing_table: dict[str, Any],
) -> str | None:
    """Find the best LiteLLM key for a ccusage model name.

    ccusage reports plain Claude Code model names (e.g. ``claude-opus-4-8``).
    LiteLLM usually publishes that exact key, but it also ships provider-prefixed
    variants (``us.anthropic.claude-opus-4-8``, ``vertex_ai/...``). We prefer an
    exact match and fall back to the shortest key that ends with the model name,
    which selects the plain Anthropic entry over the prefixed provider variants.

    Args:
        model_name: The model name as reported by ccusage.
        pricing_table: The full LiteLLM pricing dictionary.

    Returns:
        The matching LiteLLM key, or None if no reasonable match exists.
    """
    if model_name in pricing_table:
        return model_name

    suffix_matches = [
        key for key in pricing_table if key.endswith(model_name) and "cost" not in key.lower()
    ]
    if not suffix_matches:
        return None

    # The shortest suffix match is the least provider-prefixed one.
    return min(suffix_matches, key=len)


def resolve_pricing_map(
    model_names: list[str],
) -> dict[str, dict[str, Any]]:
    """Resolve pricing for each model name found in the usage data.

    Args:
        model_names: Model names reported by ccusage (may contain duplicates).

    Returns:
        A mapping of each input model name to its LiteLLM pricing entry. Models
        that cannot be matched are omitted and logged as a warning.

    Raises:
        PricingError: If the pricing table itself cannot be fetched.
    """
    pricing_table = _download_pricing_table()

    pricing_map: dict[str, dict[str, Any]] = {}
    for model_name in sorted(set(model_names)):
        matched_key = _match_pricing_key(model_name, pricing_table)
        if matched_key is None:
            logger.warning(
                "No LiteLLM pricing found for model '%s'; its cost breakdown will be zero.",
                model_name,
            )
            continue
        pricing_map[model_name] = pricing_table[matched_key]
        logger.debug("Resolved pricing for '%s' via key '%s'", model_name, matched_key)

    if not pricing_map:
        logger.warning("No pricing could be resolved for any model in the usage data.")

    return pricing_map
