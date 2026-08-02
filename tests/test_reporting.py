"""Tests for the reporting module."""

from claude_code_usage_analyzer import analysis, reporting


class TestFormatters:
    """Tests for the number/cost formatters."""

    def test_fmt_num_with_decimals(self):
        assert reporting._fmt_num(1234.567, 2) == "1,234.57"

    def test_fmt_num_integer(self):
        assert reporting._fmt_num(1234567, 0) == "1,234,567"

    def test_fmt_cost(self):
        assert reporting._fmt_cost(31.9) == "$31.90"


class TestCacheEfficiencyLabel:
    """Tests for _cache_efficiency_label."""

    def test_excellent(self):
        assert reporting._cache_efficiency_label(95) == "excellent"

    def test_moderate(self):
        assert reporting._cache_efficiency_label(50) == "moderate"


class TestGenerateMarkdownReport:
    """Tests for the Markdown report generator."""

    def test_report_has_expected_sections(self, sample_raw_data, sample_pricing_map):
        result = analysis.perform_complete_analysis(sample_raw_data, sample_pricing_map)
        report = reporting.generate_markdown_report(result)
        assert "# Claude Code Usage Analysis Report" in report
        assert "## Executive Summary" in report
        assert "## Model-Specific Analysis" in report
        assert "## Key Insights" in report

    def test_report_includes_shortened_model_names(self, sample_raw_data, sample_pricing_map):
        result = analysis.perform_complete_analysis(sample_raw_data, sample_pricing_map)
        report = reporting.generate_markdown_report(result)
        assert "opus-4-8" in report
        assert "claude-opus-4-8" not in report  # prefix should be stripped

    def test_no_quarto_generator_remains(self):
        # Quarto output was removed in favor of the HTML dashboard.
        assert not hasattr(reporting, "generate_quarto_report")
