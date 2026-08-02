"""Tests for the data_source module."""

import json

import pytest

from claude_code_usage_analyzer import data_source


class TestBuildCcusageCommand:
    """Tests for _build_ccusage_command."""

    def test_uses_list_form_with_since(self):
        cmd = data_source._build_ccusage_command("20260101")
        assert cmd[0] == "npx"
        assert "--since" in cmd
        assert cmd[cmd.index("--since") + 1] == "20260101"

    def test_never_uses_shell_metacharacters_inline(self):
        # The date is a discrete argument, so a malicious value cannot break out.
        cmd = data_source._build_ccusage_command("2026; rm -rf /")
        assert cmd[cmd.index("--since") + 1] == "2026; rm -rf /"
        assert all(";" not in part for part in cmd if part != "2026; rm -rf /")


class TestStripCcusageNoise:
    """Tests for _strip_ccusage_noise."""

    def test_strips_leading_banner(self):
        raw = '[ccusage] warning line\n{"daily": []}'
        assert data_source._strip_ccusage_noise(raw) == '{"daily": []}'

    def test_leaves_clean_json_untouched(self):
        raw = '{"daily": []}'
        assert data_source._strip_ccusage_noise(raw) == raw


class TestLoadRawUsageData:
    """Tests for load_raw_usage_data."""

    def test_loads_valid_file(self, tmp_path):
        path = tmp_path / "raw.json"
        path.write_text(json.dumps({"daily": [], "totals": {}}))
        data = data_source.load_raw_usage_data(path)
        assert data == {"daily": [], "totals": {}}

    def test_strips_banner_before_parsing(self, tmp_path):
        path = tmp_path / "raw.json"
        path.write_text('[ccusage] note\n{"daily": [], "totals": {}}')
        data = data_source.load_raw_usage_data(path)
        assert "daily" in data

    def test_missing_file_raises(self, tmp_path):
        with pytest.raises(data_source.DataSourceError, match="not found"):
            data_source.load_raw_usage_data(tmp_path / "missing.json")

    def test_invalid_json_raises(self, tmp_path):
        path = tmp_path / "raw.json"
        path.write_text("not json {")
        with pytest.raises(data_source.DataSourceError, match="not valid JSON"):
            data_source.load_raw_usage_data(path)

    def test_missing_keys_raises(self, tmp_path):
        path = tmp_path / "raw.json"
        path.write_text(json.dumps({"daily": []}))
        with pytest.raises(data_source.DataSourceError, match="missing expected"):
            data_source.load_raw_usage_data(path)
