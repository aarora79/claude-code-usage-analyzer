"""Tests for the analysis module."""

import pytest

from claude_code_usage_analyzer import analysis


class TestShortenModelName:
    """Tests for _shorten_model_name."""

    def test_strips_claude_prefix(self):
        assert analysis._shorten_model_name("claude-opus-4-8") == "opus-4-8"

    def test_strips_trailing_date_stamp(self):
        assert analysis._shorten_model_name("claude-haiku-4-5-20251001") == "haiku-4-5"

    def test_leaves_undated_names_alone(self):
        assert analysis._shorten_model_name("gpt-5.5") == "gpt-5.5"

    def test_does_not_strip_version_that_is_not_a_date(self):
        # A trailing "-4-5" is a version, not an 8-digit date, so it stays.
        assert analysis._shorten_model_name("claude-sonnet-4-5") == "sonnet-4-5"


class TestCalculatePercentile:
    """Tests for _calculate_percentile."""

    def test_empty_returns_zero(self):
        assert analysis._calculate_percentile([], 95) == 0.0

    def test_median_of_simple_list(self):
        assert analysis._calculate_percentile([1, 2, 3, 4, 5], 50) == 3

    def test_max_percentile_returns_max(self):
        assert analysis._calculate_percentile([10, 20, 30], 100) == 30


class TestAnalyzeModelCombinations:
    """Tests for analyze_model_combinations."""

    def test_counts_days_per_combination(self, sample_raw_data):
        result = analysis.analyze_model_combinations(sample_raw_data["daily"])
        combos = {tuple(item["models"]): item["days"] for item in result}
        assert combos[("opus-4-8",)] == 1
        assert combos[("haiku-4-5", "opus-4-8")] == 1

    def test_sorted_by_descending_days(self, sample_raw_data):
        # Duplicate the single-model day so it clearly leads.
        daily = sample_raw_data["daily"] + [sample_raw_data["daily"][0]]
        result = analysis.analyze_model_combinations(daily)
        assert result[0]["days"] >= result[-1]["days"]


class TestPerformCompleteAnalysis:
    """Tests for the top-level analysis function."""

    def test_summary_matches_totals(self, sample_raw_data, sample_pricing_map):
        result = analysis.perform_complete_analysis(sample_raw_data, sample_pricing_map)
        assert result["summary"]["total_cost"] == 0.75
        assert result["summary"]["total_tokens"] == 69000

    def test_cache_efficiency_computed(self, sample_raw_data, sample_pricing_map):
        result = analysis.perform_complete_analysis(sample_raw_data, sample_pricing_map)
        # 60000 cache read / 69000 total * 100
        assert result["summary"]["overall_cache_efficiency"] == pytest.approx(86.96, abs=0.1)

    def test_period_field_used_for_dates(self, sample_raw_data, sample_pricing_map):
        result = analysis.perform_complete_analysis(sample_raw_data, sample_pricing_map)
        period = result["metadata"]["analysis_period"]
        assert period["start_date"] == "2026-01-01"
        assert period["end_date"] == "2026-01-02"

    def test_cost_breakdown_uses_pricing(self, sample_raw_data, sample_pricing_map):
        result = analysis.perform_complete_analysis(sample_raw_data, sample_pricing_map)
        # Day 1 opus input cost = 1000 tokens * 5e-06 = 0.005
        cost_input = result["daily_statistics"]["cost_input"]
        assert cost_input["max"] == pytest.approx(0.005, abs=1e-6)

    def test_model_missing_pricing_yields_zero_cost(self, sample_raw_data):
        # Empty pricing map means no cost breakdown, but tokens still counted.
        result = analysis.perform_complete_analysis(sample_raw_data, {})
        assert result["daily_statistics"]["cost_input"]["total"] == 0
        assert result["summary"]["total_tokens"] == 69000

    def test_handles_zero_total_tokens(self, sample_pricing_map):
        raw = {
            "daily": [
                {
                    "date": "2026-01-01",
                    "inputTokens": 0,
                    "outputTokens": 0,
                    "cacheCreationTokens": 0,
                    "cacheReadTokens": 0,
                    "totalTokens": 0,
                    "totalCost": 0,
                    "modelBreakdowns": [],
                }
            ],
            "totals": {
                "inputTokens": 0,
                "outputTokens": 0,
                "cacheCreationTokens": 0,
                "cacheReadTokens": 0,
                "totalTokens": 0,
                "totalCost": 0,
            },
        }
        result = analysis.perform_complete_analysis(raw, sample_pricing_map)
        assert result["summary"]["overall_cache_efficiency"] == 0
