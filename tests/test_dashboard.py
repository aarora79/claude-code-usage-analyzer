"""Tests for the HTML dashboard generator."""

from claude_code_usage_analyzer import analysis, dashboard


class TestComputeDashboardContext:
    """Tests for _compute_dashboard_context."""

    def test_context_has_expected_keys(self, sample_raw_data, sample_pricing_map):
        result = analysis.perform_complete_analysis(sample_raw_data, sample_pricing_map)
        ctx = dashboard._compute_dashboard_context(result)
        for key in ("total_cost", "cost_mean", "cost_std", "primary_model", "primary_pct"):
            assert key in ctx

    def test_primary_model_is_highest_cost(self, sample_raw_data, sample_pricing_map):
        result = analysis.perform_complete_analysis(sample_raw_data, sample_pricing_map)
        ctx = dashboard._compute_dashboard_context(result)
        # opus-4-8 has the higher total cost in the fixture.
        assert ctx["primary_model"] == "opus-4-8"
        assert 0 <= ctx["primary_pct"] <= 100

    def test_monthly_projection_is_mean_times_30(self, sample_raw_data, sample_pricing_map):
        result = analysis.perform_complete_analysis(sample_raw_data, sample_pricing_map)
        ctx = dashboard._compute_dashboard_context(result)
        assert ctx["monthly_projection"] == ctx["cost_mean"] * 30


class TestModelSplit:
    """Tests for the per-model cost split."""

    def test_split_sorted_by_cost_descending(self, sample_raw_data, sample_pricing_map):
        result = analysis.perform_complete_analysis(sample_raw_data, sample_pricing_map)
        ctx = dashboard._compute_dashboard_context(result)
        split = ctx["model_split"]
        assert split
        costs = [row["cost"] for row in split]
        assert costs == sorted(costs, reverse=True)

    def test_split_shares_sum_to_100(self, sample_raw_data, sample_pricing_map):
        result = analysis.perform_complete_analysis(sample_raw_data, sample_pricing_map)
        ctx = dashboard._compute_dashboard_context(result)
        total_pct = sum(row["pct"] for row in ctx["model_split"])
        assert abs(total_pct - 100.0) < 0.01

    def test_split_rows_have_expected_keys(self, sample_raw_data, sample_pricing_map):
        result = analysis.perform_complete_analysis(sample_raw_data, sample_pricing_map)
        ctx = dashboard._compute_dashboard_context(result)
        for key in ("name", "cost", "pct", "days_used", "cache_efficiency"):
            assert key in ctx["model_split"][0]

    def test_primary_model_matches_first_split_row(self, sample_raw_data, sample_pricing_map):
        result = analysis.perform_complete_analysis(sample_raw_data, sample_pricing_map)
        ctx = dashboard._compute_dashboard_context(result)
        assert ctx["primary_model"] == ctx["model_split"][0]["name"]

    def test_empty_model_stats_yields_empty_split(self):
        rows = dashboard._build_model_split({}, total_cost=0)
        assert rows == []


class TestGenerateDashboardHtml:
    """Tests for generate_dashboard_html."""

    def test_returns_self_contained_html(self, sample_raw_data, sample_pricing_map):
        result = analysis.perform_complete_analysis(sample_raw_data, sample_pricing_map)
        html = dashboard.generate_dashboard_html(result)
        assert html.startswith("<!DOCTYPE html>")
        assert "</html>" in html

    def test_no_external_resources(self, sample_raw_data, sample_pricing_map):
        result = analysis.perform_complete_analysis(sample_raw_data, sample_pricing_map)
        html = dashboard.generate_dashboard_html(result)
        # A self-contained file must not pull in a CDN, web font, or remote script.
        for needle in ("cdn", "googleapis", "unpkg", "jsdelivr", "<script src", "<link "):
            assert needle not in html.lower()

    def test_all_template_tokens_replaced(self, sample_raw_data, sample_pricing_map):
        result = analysis.perform_complete_analysis(sample_raw_data, sample_pricing_map)
        html = dashboard.generate_dashboard_html(result)
        for token in ("__SERIES_JSON__", "__CONTEXT_JSON__", "__GENERATED__"):
            assert token not in html

    def test_embeds_daily_series_dates(self, sample_raw_data, sample_pricing_map):
        result = analysis.perform_complete_analysis(sample_raw_data, sample_pricing_map)
        html = dashboard.generate_dashboard_html(result)
        # The series JSON should carry the fixture's dates.
        assert "2026-01-01" in html
        assert "2026-01-02" in html


class TestScriptBlockEscaping:
    """The embedded JSON must not be able to break out of its <script> block."""

    def test_angle_brackets_escaped(self):
        payload = {"name": "</script><img src=x onerror=alert(1)>"}
        text = dashboard._json_for_script_block(payload)
        assert "</script>" not in text
        assert "<" not in text and ">" not in text
        assert "\\u003c" in text

    def test_still_valid_json(self):
        import json

        payload = {"a": "x<y>z&w", "n": 3}
        text = dashboard._json_for_script_block(payload)
        # Escaping is reversible: JSON.parse (and json.loads) read it back unchanged.
        assert json.loads(text) == payload

    def test_malicious_model_name_does_not_break_out(self, sample_raw_data, sample_pricing_map):
        # A model name containing markup must stay inside the script block.
        sample_raw_data["daily"][0]["modelBreakdowns"][0]["modelName"] = "</script><b>x"
        result = analysis.perform_complete_analysis(sample_raw_data, sample_pricing_map)
        html = dashboard.generate_dashboard_html(result)
        assert "</script><b>x" not in html
