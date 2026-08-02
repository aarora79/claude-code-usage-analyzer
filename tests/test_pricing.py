"""Tests for dynamic pricing resolution."""

from claude_code_usage_analyzer import pricing


class TestMatchPricingKey:
    """Tests for _match_pricing_key."""

    def test_exact_match_preferred(self):
        table = {"claude-opus-4-8": {}, "us.anthropic.claude-opus-4-8": {}}
        assert pricing._match_pricing_key("claude-opus-4-8", table) == "claude-opus-4-8"

    def test_shortest_suffix_match_when_no_exact(self):
        table = {
            "us.anthropic.claude-opus-4-8": {},
            "vertex_ai/claude-opus-4-8": {},
        }
        result = pricing._match_pricing_key("claude-opus-4-8", table)
        assert result == "vertex_ai/claude-opus-4-8" or result == "us.anthropic.claude-opus-4-8"
        assert result.endswith("claude-opus-4-8")

    def test_returns_none_when_unmatched(self):
        table = {"claude-sonnet-5": {}}
        assert pricing._match_pricing_key("totally-unknown-model", table) is None


class TestResolvePricingMap:
    """Tests for resolve_pricing_map (with the network layer stubbed)."""

    def test_resolves_known_models(self, monkeypatch):
        fake_table = {
            "claude-opus-4-8": {"input_cost_per_token": 5e-06},
            "claude-haiku-4-5-20251001": {"input_cost_per_token": 1e-06},
        }
        monkeypatch.setattr(pricing, "_download_pricing_table", lambda: fake_table)

        result = pricing.resolve_pricing_map(
            ["claude-opus-4-8", "claude-opus-4-8", "claude-haiku-4-5-20251001"]
        )

        assert set(result.keys()) == {"claude-opus-4-8", "claude-haiku-4-5-20251001"}
        assert result["claude-opus-4-8"]["input_cost_per_token"] == 5e-06

    def test_unknown_model_is_skipped_not_fatal(self, monkeypatch):
        fake_table = {"claude-opus-4-8": {"input_cost_per_token": 5e-06}}
        monkeypatch.setattr(pricing, "_download_pricing_table", lambda: fake_table)

        result = pricing.resolve_pricing_map(["claude-opus-4-8", "gpt-brand-new"])

        assert "claude-opus-4-8" in result
        assert "gpt-brand-new" not in result

    def test_empty_when_nothing_matches(self, monkeypatch):
        monkeypatch.setattr(pricing, "_download_pricing_table", lambda: {"other": {}})
        assert pricing.resolve_pricing_map(["unknown"]) == {}
