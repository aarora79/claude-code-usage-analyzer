#!/usr/bin/env python3
"""
Analyze Claude Code usage statistics and generate comprehensive JSON and Markdown reports.
Architecture:
1. Read raw usage data from ccusage
2. Fetch pricing from LiteLLM JSON
3. Perform all analysis and save complete results to JSON
4. Generate markdown report by reading the JSON file
"""

import json
import statistics
import urllib.request
from datetime import datetime
from typing import Dict, List, Any
from collections import Counter


LITELLM_PRICING_URL = "https://raw.githubusercontent.com/BerriAI/litellm/main/model_prices_and_context_window.json"


def fetch_model_pricing() -> Dict[str, Dict]:
    """Fetch and parse model pricing from LiteLLM."""
    print("Fetching model pricing from LiteLLM...")

    with urllib.request.urlopen(LITELLM_PRICING_URL) as response:
        all_prices = json.loads(response.read())

    # Map our model names to pricing data
    pricing_map = {}

    # Claude Opus 4.1
    opus_key = next((k for k in all_prices.keys()
                    if 'opus-4-1-20250805' in k or 'claude-opus-4-1-20250805' in k), None)
    if opus_key:
        pricing_map['claude-opus-4-1-20250805'] = all_prices[opus_key]

    # Claude Sonnet 4
    sonnet4_key = next((k for k in all_prices.keys()
                       if 'sonnet-4-20250514' in k and 'sonnet-4-5' not in k), None)
    if sonnet4_key:
        pricing_map['claude-sonnet-4-20250514'] = all_prices[sonnet4_key]

    # Claude Sonnet 4.5
    sonnet45_key = next((k for k in all_prices.keys()
                        if 'sonnet-4-5-20250929' in k or 'claude-sonnet-4-5-20250929' in k), None)
    if sonnet45_key:
        pricing_map['claude-sonnet-4-5-20250929'] = all_prices[sonnet45_key]

    return pricing_map


def calculate_percentile(data: List[float], percentile: int) -> float:
    """Calculate the percentile of a list of numbers."""
    if not data:
        return 0.0
    sorted_data = sorted(data)
    index = (percentile / 100) * (len(sorted_data) - 1)
    lower = int(index)
    upper = lower + 1
    weight = index - lower

    if upper >= len(sorted_data):
        return sorted_data[-1]

    return sorted_data[lower] * (1 - weight) + sorted_data[upper] * weight


def analyze_model_combinations(daily_data: List[Dict]) -> List[Dict[str, Any]]:
    """Analyze which combinations of models were used together."""
    model_combinations = []

    for day in daily_data:
        models_used = sorted([
            breakdown['modelName'].replace('claude-', '')
                                 .replace('-20250805', '')
                                 .replace('-20250514', '')
                                 .replace('-20250929', '')
            for breakdown in day.get('modelBreakdowns', [])
        ])

        if models_used:
            model_combinations.append(tuple(models_used))

    combination_counts = Counter(model_combinations)

    result = []
    for combination, count in sorted(combination_counts.items(),
                                     key=lambda x: x[1], reverse=True):
        result.append({
            'models': list(combination),
            'days': count
        })

    return result


def perform_complete_analysis(raw_data: Dict, pricing_map: Dict) -> Dict:
    """Perform complete analysis and return structured results."""
    print("Performing complete analysis...")

    daily_data = raw_data['daily']
    totals = raw_data['totals']

    # Analyze model combinations
    model_combinations = analyze_model_combinations(daily_data)

    # Daily statistics with cost breakdowns
    daily_stats = {
        'input_tokens': [],
        'output_tokens': [],
        'cache_create': [],
        'cache_read': [],
        'total_tokens': [],
        'total_cost': [],
        'cost_input': [],
        'cost_output': [],
        'cost_cache_create': [],
        'cost_cache_read': [],
        'cache_efficiency': []
    }

    for day in daily_data:
        daily_stats['input_tokens'].append(day['inputTokens'])
        daily_stats['output_tokens'].append(day['outputTokens'])
        daily_stats['cache_create'].append(day['cacheCreationTokens'])
        daily_stats['cache_read'].append(day['cacheReadTokens'])
        daily_stats['total_tokens'].append(day['totalTokens'])
        daily_stats['total_cost'].append(day['totalCost'])

        # Calculate cost breakdown for this day
        day_costs = {'input': 0, 'output': 0, 'cache_create': 0, 'cache_read': 0}

        for breakdown in day.get('modelBreakdowns', []):
            model_name = breakdown['modelName']
            if model_name in pricing_map:
                pricing = pricing_map[model_name]
                day_costs['input'] += breakdown['inputTokens'] * pricing.get('input_cost_per_token', 0)
                day_costs['output'] += breakdown['outputTokens'] * pricing.get('output_cost_per_token', 0)
                day_costs['cache_create'] += breakdown['cacheCreationTokens'] * pricing.get('cache_creation_input_token_cost', 0)
                day_costs['cache_read'] += breakdown['cacheReadTokens'] * pricing.get('cache_read_input_token_cost', 0)

        daily_stats['cost_input'].append(day_costs['input'])
        daily_stats['cost_output'].append(day_costs['output'])
        daily_stats['cost_cache_create'].append(day_costs['cache_create'])
        daily_stats['cost_cache_read'].append(day_costs['cache_read'])

        efficiency = (day['cacheReadTokens'] / day['totalTokens'] * 100) if day['totalTokens'] > 0 else 0
        daily_stats['cache_efficiency'].append(efficiency)

    # Calculate statistics for all metrics
    daily_statistics = {}
    for key, values in daily_stats.items():
        if values:
            daily_statistics[key] = {
                'mean': statistics.mean(values),
                'median': statistics.median(values),
                'p95': calculate_percentile(values, 95),
                'min': min(values),
                'max': max(values),
                'total': sum(values) if key != 'cache_efficiency' else None
            }

    # Model-specific analysis
    model_data = {}

    for day in daily_data:
        for breakdown in day.get('modelBreakdowns', []):
            model_name = breakdown['modelName']

            if model_name not in model_data:
                model_data[model_name] = {
                    'input_tokens': [],
                    'output_tokens': [],
                    'cache_create': [],
                    'cache_read': [],
                    'total_cost': [],
                    'cost_input': [],
                    'cost_output': [],
                    'cost_cache_create': [],
                    'cost_cache_read': [],
                    'days_used': 0,
                    'total_tokens': []
                }

            model_data[model_name]['days_used'] += 1
            model_data[model_name]['input_tokens'].append(breakdown['inputTokens'])
            model_data[model_name]['output_tokens'].append(breakdown['outputTokens'])
            model_data[model_name]['cache_create'].append(breakdown['cacheCreationTokens'])
            model_data[model_name]['cache_read'].append(breakdown['cacheReadTokens'])
            model_data[model_name]['total_cost'].append(breakdown['cost'])

            total = (breakdown['inputTokens'] + breakdown['outputTokens'] +
                    breakdown['cacheCreationTokens'] + breakdown['cacheReadTokens'])
            model_data[model_name]['total_tokens'].append(total)

            # Calculate cost breakdown
            if model_name in pricing_map:
                pricing = pricing_map[model_name]
                model_data[model_name]['cost_input'].append(
                    breakdown['inputTokens'] * pricing.get('input_cost_per_token', 0))
                model_data[model_name]['cost_output'].append(
                    breakdown['outputTokens'] * pricing.get('output_cost_per_token', 0))
                model_data[model_name]['cost_cache_create'].append(
                    breakdown['cacheCreationTokens'] * pricing.get('cache_creation_input_token_cost', 0))
                model_data[model_name]['cost_cache_read'].append(
                    breakdown['cacheReadTokens'] * pricing.get('cache_read_input_token_cost', 0))

    # Calculate statistics for each model
    model_statistics = {}
    for model_name, data in model_data.items():
        display_name = (model_name.replace('claude-', '')
                                  .replace('-20250805', '')
                                  .replace('-20250514', '')
                                  .replace('-20250929', ''))

        stats = {}
        for key in ['input_tokens', 'output_tokens', 'cache_create', 'cache_read',
                    'total_cost', 'total_tokens', 'cost_input', 'cost_output',
                    'cost_cache_create', 'cost_cache_read']:
            values = data[key]
            if values:
                stats[key] = {
                    'mean': statistics.mean(values),
                    'median': statistics.median(values),
                    'p95': calculate_percentile(values, 95),
                    'total': sum(values)
                }

        # Cache efficiency
        total_cache_read = sum(data['cache_read'])
        total_tokens = sum(data['total_tokens'])
        cache_efficiency = (total_cache_read / total_tokens * 100) if total_tokens > 0 else 0

        # Pricing per million tokens
        pricing_per_million = {}
        if model_name in pricing_map:
            pricing = pricing_map[model_name]
            pricing_per_million = {
                'input': pricing.get('input_cost_per_token', 0) * 1_000_000,
                'output': pricing.get('output_cost_per_token', 0) * 1_000_000,
                'cache_create': pricing.get('cache_creation_input_token_cost', 0) * 1_000_000,
                'cache_read': pricing.get('cache_read_input_token_cost', 0) * 1_000_000
            }

        model_statistics[display_name] = {
            'days_used': data['days_used'],
            'cache_efficiency': cache_efficiency,
            'pricing_per_million_tokens': pricing_per_million,
            'statistics': stats
        }

    # Build complete analysis result
    overall_cache_efficiency = (totals['cacheReadTokens'] / totals['totalTokens'] * 100) if totals['totalTokens'] > 0 else 0

    analysis_result = {
        'metadata': {
            'analysis_period': {
                'start_date': min([day['date'] for day in daily_data]),
                'end_date': max([day['date'] for day in daily_data]),
                'total_days': len(daily_data)
            },
            'generated_at': datetime.now().isoformat(),
            'source': 'ccusage CLI tool',
            'pricing_source': LITELLM_PRICING_URL
        },
        'summary': {
            'total_cost': totals['totalCost'],
            'total_tokens': totals['totalTokens'],
            'total_input_tokens': totals['inputTokens'],
            'total_output_tokens': totals['outputTokens'],
            'total_cache_creation_tokens': totals['cacheCreationTokens'],
            'total_cache_read_tokens': totals['cacheReadTokens'],
            'overall_cache_efficiency': overall_cache_efficiency
        },
        'model_combinations': model_combinations,
        'daily_statistics': daily_statistics,
        'model_statistics': model_statistics
    }

    return analysis_result


def generate_markdown_from_json(analysis_json: Dict) -> str:
    """Generate markdown report from analysis JSON."""
    print("Generating markdown report from analysis JSON...")

    def fmt_num(num: float, decimals: int = 2) -> str:
        """Format number with thousands separator."""
        if decimals == 0:
            return f"{int(num):,}"
        return f"{num:,.{decimals}f}"

    def fmt_cost(cost: float) -> str:
        """Format cost in dollars."""
        return f"${fmt_num(cost, 2)}"

    meta = analysis_json['metadata']
    summary = analysis_json['summary']
    daily_stats = analysis_json['daily_statistics']
    model_stats = analysis_json['model_statistics']
    model_combos = analysis_json['model_combinations']

    report = []
    report.append("# Claude Code Usage Analysis Report")
    report.append("")
    report.append(f"**Analysis Period:** {meta['analysis_period']['start_date']} to {meta['analysis_period']['end_date']} ({meta['analysis_period']['total_days']} days)")
    report.append(f"**Report Generated:** {datetime.fromisoformat(meta['generated_at']).strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("")

    # Executive Summary
    report.append("## Executive Summary")
    report.append("")
    report.append(f"- **Total Cost:** {fmt_cost(summary['total_cost'])}")
    report.append(f"- **Total Tokens:** {fmt_num(summary['total_tokens'], 0)}")
    report.append(f"- **Total Input Tokens:** {fmt_num(summary['total_input_tokens'], 0)}")
    report.append(f"- **Total Output Tokens:** {fmt_num(summary['total_output_tokens'], 0)}")
    report.append(f"- **Cache Creation Tokens:** {fmt_num(summary['total_cache_creation_tokens'], 0)}")
    report.append(f"- **Cache Read Tokens:** {fmt_num(summary['total_cache_read_tokens'], 0)}")
    report.append(f"- **Overall Cache Efficiency:** {fmt_num(summary['overall_cache_efficiency'])}%")
    report.append("")

    # Tokens per minute estimates (assuming 8-hour workday = 480 minutes)
    MINUTES_PER_WORKDAY = 8 * 60  # 480 minutes

    report.append("### Estimated Usage Per Minute (8-hour workday)")
    report.append("")

    # Mean daily usage
    mean_total_tokens = daily_stats['total_tokens']['mean']
    mean_cost = daily_stats['total_cost']['mean']
    mean_input = daily_stats['input_tokens']['mean']
    mean_output = daily_stats['output_tokens']['mean']
    mean_cache_create = daily_stats['cache_create']['mean']
    mean_cache_read = daily_stats['cache_read']['mean']
    mean_tokens_per_min = mean_total_tokens / MINUTES_PER_WORKDAY
    mean_cost_per_min = mean_cost / MINUTES_PER_WORKDAY

    report.append(f"- **Mean Usage:** On an average day, you process {fmt_num(mean_tokens_per_min, 0)} tokens per minute at a cost of {fmt_cost(mean_cost_per_min)} per minute. This means your daily spend is {fmt_cost(mean_cost)} for {fmt_num(mean_total_tokens, 0)} total tokens.")
    report.append(f"  - This is composed of {fmt_num(mean_input/MINUTES_PER_WORKDAY, 0)} input tokens, {fmt_num(mean_output/MINUTES_PER_WORKDAY, 0)} output tokens, {fmt_num(mean_cache_create/MINUTES_PER_WORKDAY, 0)} cache creation tokens, and {fmt_num(mean_cache_read/MINUTES_PER_WORKDAY, 0)} cache read tokens per minute.")

    # Median daily usage
    median_total_tokens = daily_stats['total_tokens']['median']
    median_cost = daily_stats['total_cost']['median']
    median_input = daily_stats['input_tokens']['median']
    median_output = daily_stats['output_tokens']['median']
    median_cache_create = daily_stats['cache_create']['median']
    median_cache_read = daily_stats['cache_read']['median']
    median_tokens_per_min = median_total_tokens / MINUTES_PER_WORKDAY
    median_cost_per_min = median_cost / MINUTES_PER_WORKDAY

    report.append(f"- **Median Usage:** On a typical day, you process {fmt_num(median_tokens_per_min, 0)} tokens per minute at a cost of {fmt_cost(median_cost_per_min)} per minute. This means your daily spend is {fmt_cost(median_cost)} for {fmt_num(median_total_tokens, 0)} total tokens.")
    report.append(f"  - This is composed of {fmt_num(median_input/MINUTES_PER_WORKDAY, 0)} input tokens, {fmt_num(median_output/MINUTES_PER_WORKDAY, 0)} output tokens, {fmt_num(median_cache_create/MINUTES_PER_WORKDAY, 0)} cache creation tokens, and {fmt_num(median_cache_read/MINUTES_PER_WORKDAY, 0)} cache read tokens per minute.")

    # P95 daily usage
    p95_total_tokens = daily_stats['total_tokens']['p95']
    p95_cost = daily_stats['total_cost']['p95']
    p95_input = daily_stats['input_tokens']['p95']
    p95_output = daily_stats['output_tokens']['p95']
    p95_cache_create = daily_stats['cache_create']['p95']
    p95_cache_read = daily_stats['cache_read']['p95']
    p95_tokens_per_min = p95_total_tokens / MINUTES_PER_WORKDAY
    p95_cost_per_min = p95_cost / MINUTES_PER_WORKDAY

    report.append(f"- **P95 Usage:** On your busiest days (95th percentile), you process {fmt_num(p95_tokens_per_min, 0)} tokens per minute at a cost of {fmt_cost(p95_cost_per_min)} per minute. This means your daily spend is {fmt_cost(p95_cost)} for {fmt_num(p95_total_tokens, 0)} total tokens.")
    report.append(f"  - This is composed of {fmt_num(p95_input/MINUTES_PER_WORKDAY, 0)} input tokens, {fmt_num(p95_output/MINUTES_PER_WORKDAY, 0)} output tokens, {fmt_num(p95_cache_create/MINUTES_PER_WORKDAY, 0)} cache creation tokens, and {fmt_num(p95_cache_read/MINUTES_PER_WORKDAY, 0)} cache read tokens per minute.")
    report.append("")

    # Model Combinations
    report.append("## Model Usage Patterns")
    report.append("")
    report.append("**Model Combinations Used:**")
    report.append("")
    for combo in model_combos:
        models_str = " + ".join(combo['models'])
        report.append(f"- **{models_str}**: {combo['days']} days")
    report.append("")

    # Daily Cost Analysis
    report.append("## Daily Cost Analysis")
    report.append("")
    report.append("### Total Daily Cost")
    report.append("")
    report.append("| Metric | Mean | Median | P95 | Min | Max |")
    report.append("|--------|------|--------|-----|-----|-----|")
    tc = daily_stats['total_cost']
    report.append(f"| **Total Cost** | {fmt_cost(tc['mean'])} | {fmt_cost(tc['median'])} | "
                 f"{fmt_cost(tc['p95'])} | {fmt_cost(tc['min'])} | {fmt_cost(tc['max'])} |")
    report.append("")

    # Cost breakdown by token type
    report.append("### Daily Cost Breakdown by Token Type")
    report.append("")
    report.append("| Token Type | Mean | Median | P95 | Total | % of Total |")
    report.append("|------------|------|--------|-----|-------|------------|")

    total_cost = daily_stats['total_cost']['total']
    for key, label in [
        ('cost_input', 'Input Tokens'),
        ('cost_output', 'Output Tokens'),
        ('cost_cache_create', 'Cache Creation'),
        ('cost_cache_read', 'Cache Read')
    ]:
        s = daily_stats[key]
        pct = (s['total'] / total_cost * 100) if total_cost > 0 else 0
        report.append(f"| **{label}** | {fmt_cost(s['mean'])} | {fmt_cost(s['median'])} | "
                     f"{fmt_cost(s['p95'])} | {fmt_cost(s['total'])} | {fmt_num(pct)}% |")
    report.append("")

    # Daily Token Statistics
    report.append("## Daily Token Usage Statistics")
    report.append("")
    report.append("| Token Type | Mean | Median | P95 | Min | Max |")
    report.append("|------------|------|--------|-----|-----|-----|")

    for key, label in [
        ('input_tokens', 'Input Tokens'),
        ('output_tokens', 'Output Tokens'),
        ('cache_create', 'Cache Creation'),
        ('cache_read', 'Cache Read'),
        ('total_tokens', 'Total Tokens')
    ]:
        s = daily_stats[key]
        report.append(f"| **{label}** | {fmt_num(s['mean'], 0)} | {fmt_num(s['median'], 0)} | "
                     f"{fmt_num(s['p95'], 0)} | {fmt_num(s['min'], 0)} | {fmt_num(s['max'], 0)} |")
    report.append("")

    # Cache Efficiency
    report.append("## Cache Efficiency Analysis")
    report.append("")
    report.append("**Cache efficiency** is calculated as: `(Cache Read Tokens / Total Tokens) × 100`")
    report.append("")
    report.append("Higher percentages indicate better cache utilization, meaning:")
    report.append("- Fewer tokens need to be processed from scratch")
    report.append("- Lower costs per request (cache reads cost ~10-20x less than new tokens)")
    report.append("- Faster response times")
    report.append("")
    report.append("| Metric | Mean | Median | P95 | Min | Max |")
    report.append("|--------|------|--------|-----|-----|-----|")
    ce = daily_stats['cache_efficiency']
    report.append(f"| **Cache Efficiency** | {fmt_num(ce['mean'])}% | {fmt_num(ce['median'])}% | "
                 f"{fmt_num(ce['p95'])}% | {fmt_num(ce['min'])}% | {fmt_num(ce['max'])}% |")
    report.append("")

    # Model-specific analysis
    report.append("## Model-Specific Analysis")
    report.append("")

    # Sort models by total cost
    sorted_models = sorted(model_stats.items(),
                          key=lambda x: x[1]['statistics']['total_cost']['total'],
                          reverse=True)

    for model_name, stats in sorted_models:
        report.append(f"### {model_name}")
        report.append("")
        report.append(f"**Days Used:** {stats['days_used']}")
        report.append(f"**Cache Efficiency:** {fmt_num(stats['cache_efficiency'])}%")
        report.append("")

        # Pricing
        if stats['pricing_per_million_tokens']:
            pricing = stats['pricing_per_million_tokens']
            report.append("**Pricing (per million tokens):**")
            report.append(f"- Input: ${fmt_num(pricing['input'], 2)}")
            report.append(f"- Output: ${fmt_num(pricing['output'], 2)}")
            report.append(f"- Cache Creation: ${fmt_num(pricing['cache_create'], 2)}")
            report.append(f"- Cache Read: ${fmt_num(pricing['cache_read'], 2)}")
            report.append("")

        # Cost breakdown
        report.append("#### Cost Breakdown by Token Type")
        report.append("")
        report.append("| Cost Type | Mean | Median | P95 | Total | % of Model Cost |")
        report.append("|-----------|------|--------|-----|-------|-----------------|")

        model_total = stats['statistics']['total_cost']['total']
        for key, label in [
            ('cost_input', 'Input Tokens'),
            ('cost_output', 'Output Tokens'),
            ('cost_cache_create', 'Cache Creation'),
            ('cost_cache_read', 'Cache Read')
        ]:
            if key in stats['statistics']:
                s = stats['statistics'][key]
                pct = (s['total'] / model_total * 100) if model_total > 0 else 0
                report.append(f"| **{label}** | {fmt_cost(s['mean'])} | {fmt_cost(s['median'])} | "
                             f"{fmt_cost(s['p95'])} | {fmt_cost(s['total'])} | {fmt_num(pct)}% |")

        # Total row
        tc_stat = stats['statistics']['total_cost']
        report.append(f"| **TOTAL** | {fmt_cost(tc_stat['mean'])} | {fmt_cost(tc_stat['median'])} | "
                     f"{fmt_cost(tc_stat['p95'])} | {fmt_cost(tc_stat['total'])} | 100.00% |")
        report.append("")

        # Token statistics
        report.append("#### Token Statistics")
        report.append("")
        report.append("| Token Type | Mean | Median | P95 | Total |")
        report.append("|------------|------|--------|-----|-------|")

        for key, label in [
            ('input_tokens', 'Input'),
            ('output_tokens', 'Output'),
            ('cache_create', 'Cache Create'),
            ('cache_read', 'Cache Read'),
            ('total_tokens', 'Total')
        ]:
            s = stats['statistics'][key]
            report.append(f"| **{label}** | {fmt_num(s['mean'], 0)} | {fmt_num(s['median'], 0)} | "
                         f"{fmt_num(s['p95'], 0)} | {fmt_num(s['total'], 0)} |")
        report.append("")

    # Key Insights
    report.append("## Key Insights")
    report.append("")

    avg_cost = daily_stats['total_cost']['mean']
    avg_input = daily_stats['cost_input']['mean']
    avg_output = daily_stats['cost_output']['mean']
    avg_cache_create = daily_stats['cost_cache_create']['mean']
    avg_cache_read = daily_stats['cost_cache_read']['mean']

    report.append(f"1. **Daily Cost Composition:** Your average daily cost of {fmt_cost(avg_cost)} breaks down as:")
    report.append(f"   - Input tokens: {fmt_cost(avg_input)} ({fmt_num(avg_input/avg_cost*100)}%)")
    report.append(f"   - Output tokens: {fmt_cost(avg_output)} ({fmt_num(avg_output/avg_cost*100)}%)")
    report.append(f"   - Cache creation: {fmt_cost(avg_cache_create)} ({fmt_num(avg_cache_create/avg_cost*100)}%)")
    report.append(f"   - Cache reads: {fmt_cost(avg_cache_read)} ({fmt_num(avg_cache_read/avg_cost*100)}%)")
    report.append("")

    p95_cost = daily_stats['total_cost']['p95']
    report.append(f"2. **Cost Variability:** With a P95 of {fmt_cost(p95_cost)}, your highest usage days cost approximately {fmt_num(p95_cost / avg_cost, 1)}x the average.")
    report.append("")

    avg_efficiency = daily_stats['cache_efficiency']['mean']
    if avg_efficiency > 90:
        eff_desc = "excellent"
    elif avg_efficiency > 80:
        eff_desc = "very good"
    elif avg_efficiency > 70:
        eff_desc = "good"
    else:
        eff_desc = "moderate"

    report.append(f"3. **Cache Utilization:** Your average cache efficiency of {fmt_num(avg_efficiency)}% is {eff_desc}, significantly reducing processing costs.")
    report.append("")

    primary_model = sorted_models[0]
    model_cost = primary_model[1]['statistics']['total_cost']['total']
    report.append(f"4. **Primary Model:** {primary_model[0]} accounts for {fmt_cost(model_cost)} ({fmt_num(model_cost / summary['total_cost'] * 100)}%) of total costs.")
    report.append("")

    monthly_proj = avg_cost * 30
    report.append(f"5. **Monthly Projection:** Based on average daily cost, projected monthly cost is approximately {fmt_cost(monthly_proj)}.")
    report.append("")

    return "\n".join(report)


def fetch_raw_usage_data(since_date: str = "20250701", output_file: str = "/tmp/claude-usage-raw.json") -> str:
    """Fetch raw usage data using ccusage CLI tool."""
    import subprocess
    import os

    print(f"Fetching raw usage data from ccusage (since {since_date})...")

    try:
        # Run npx ccusage command
        cmd = f"npx ccusage@latest daily --since {since_date} --breakdown --json"
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            check=True
        )

        # Save output to file
        with open(output_file, 'w') as f:
            f.write(result.stdout)

        print(f"✓ Raw usage data saved to: {output_file}")
        return output_file

    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to fetch usage data: {e}")
        print(f"  Make sure 'ccusage' is available (run: npm install -g ccusage)")
        raise
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        raise


def main():
    """Main function to analyze usage and generate reports."""
    import sys
    import os
    import argparse
    from pathlib import Path

    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Analyze Claude Code usage and generate cost reports",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze usage (fetches data automatically if needed)
  claude-usage-analyzer

  # Specify custom start date (YYYYMMDD format)
  claude-usage-analyzer --since 20250901

  # Force re-fetch of data
  claude-usage-analyzer --refresh

Output files:
  data/raw/claude-usage-raw.json        - Raw usage data cache
  data/output/claude-usage-analysis.json - Complete analysis (JSON)
  data/output/claude-usage-report.md    - Human-readable report (Markdown)
"""
    )
    parser.add_argument(
        "--since",
        type=str,
        default="20250701",
        help="Start date for usage data in YYYYMMDD format (default: 20250701)"
    )
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Force re-fetch of raw usage data even if cache exists"
    )

    args = parser.parse_args()

    print("=" * 60)
    print("Claude Code Usage Analysis")
    print("=" * 60)
    print()

    # Create data directories if they don't exist
    data_raw_dir = Path('data/raw')
    data_output_dir = Path('data/output')
    data_raw_dir.mkdir(parents=True, exist_ok=True)
    data_output_dir.mkdir(parents=True, exist_ok=True)

    # Check if raw data file exists, if not fetch it
    raw_data_file = data_raw_dir / 'claude-usage-raw.json'

    if not os.path.exists(raw_data_file) or args.refresh:
        if args.refresh:
            print("Refresh requested - re-fetching usage data...")
        else:
            print(f"Raw data file not found at {raw_data_file}")
            print("Fetching usage data from ccusage...")
        print()

        since_date = args.since

        try:
            fetch_raw_usage_data(since_date, str(raw_data_file))
        except Exception:
            print()
            print("Failed to fetch usage data automatically.")
            print()
            print("Please run this command manually:")
            print(f"  npx ccusage@latest daily --since {since_date} --breakdown --json > {raw_data_file}")
            print()
            sys.exit(1)

    # Read raw usage data
    print()
    print("Reading raw usage data...")
    with open(raw_data_file, 'r') as f:
        content = f.read()

    # Remove ccusage warning line if present
    if content.startswith('[ccusage]'):
        content = '\n'.join(content.split('\n')[1:])

    raw_data = json.loads(content)

    # Fetch pricing
    pricing_map = fetch_model_pricing()

    # Perform complete analysis
    analysis_result = perform_complete_analysis(raw_data, pricing_map)

    # Save analysis JSON
    json_file = data_output_dir / 'claude-usage-analysis.json'
    print(f"Saving analysis JSON to: {json_file}")
    with open(json_file, 'w') as f:
        json.dump(analysis_result, f, indent=2)

    # Generate markdown from JSON
    markdown_report = generate_markdown_from_json(analysis_result)

    # Save markdown report
    md_file = data_output_dir / 'claude-usage-report.md'
    print(f"Saving markdown report to: {md_file}")
    with open(md_file, 'w') as f:
        f.write(markdown_report)

    print()
    print("=" * 60)
    print("Analysis Complete!")
    print("=" * 60)
    print(f"JSON Analysis: {json_file}")
    print(f"Markdown Report: {md_file}")
    print()
    print(f"Total Cost: ${analysis_result['summary']['total_cost']:.2f}")
    print(f"Total Tokens: {analysis_result['summary']['total_tokens']:,}")
    print(f"Cache Efficiency: {analysis_result['summary']['overall_cache_efficiency']:.2f}%")


if __name__ == '__main__':
    main()
