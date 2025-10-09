# Claude Code Usage Analyzer

Comprehensive usage and cost analysis tool for Claude Code with detailed breakdowns by model and token type.

## Features

- **Detailed Cost Analysis**: Break down your daily costs by token type (input, output, cache creation, cache read)
- **Model-Specific Statistics**: Analyze usage patterns for each Claude model (Opus 4.1, Sonnet 4, Sonnet 4.5)
- **Cache Efficiency Tracking**: Understand how well caching is reducing your costs
- **Model Combination Analysis**: See which models were used together and for how many days
- **Statistical Insights**: Mean, median, P95, min, and max for all metrics
- **Pricing Information**: Per-million token pricing from LiteLLM
- **JSON + Markdown Output**: Structured data for automation and human-readable reports

## Prerequisites

- Python 3.9 or higher
- [uv](https://docs.astral.sh/uv/) package manager
- Claude Code with usage data (requires `ccusage` CLI tool)

## Installation

### Using uv (Recommended)

```bash
# Clone the repository
git clone https://github.com/yourusername/claude-code-usage-analyzer.git
cd claude-code-usage-analyzer

# No installation needed! Just run with uv
uv run src/analyze_usage.py
```

### Alternative: Install with pip

```bash
pip install -e .
```

## Usage

### Quick Start (Automatic)

The analyzer will automatically fetch your usage data if not already present:

```bash
# Using uv (recommended) - fetches data automatically
uv run src/analyze_usage.py

# Or with custom date range (YYYYMMDD format)
uv run src/analyze_usage.py 20250901

# Or if installed
claude-usage-analyzer
```

The tool will:
1. Check if `/tmp/claude-usage-raw.json` exists
2. If not, automatically run `npx ccusage@latest` to fetch your data
3. Perform analysis
4. Generate JSON and markdown reports

### Manual Workflow (Optional)

If you prefer to fetch data manually or the automatic fetch fails:

#### Step 1: Generate Raw Usage Data

```bash
npx ccusage@latest daily --since 20250701 --breakdown --json > /tmp/claude-usage-raw.json
```

#### Step 2: Run the Analyzer

```bash
uv run src/analyze_usage.py
```

### Output Files

The analyzer generates two files:

1. **`/tmp/claude-usage-analysis.json`** - Complete analysis in JSON format
   - All computed statistics
   - Model combinations
   - Daily and model-specific breakdowns
   - Pricing information

2. **`/tmp/claude-usage-report.md`** - Human-readable markdown report
   - Executive summary
   - Daily cost analysis
   - Token usage statistics
   - Cache efficiency metrics
   - Model-specific insights

## Understanding the Output

### JSON Structure

```json
{
  "metadata": {
    "analysis_period": {
      "start_date": "2025-09-09",
      "end_date": "2025-10-09",
      "total_days": 31
    },
    "generated_at": "2025-10-09T21:08:50",
    "source": "ccusage CLI tool",
    "pricing_source": "https://raw.githubusercontent.com/BerriAI/litellm/main/model_prices_and_context_window.json"
  },
  "summary": {
    "total_cost": 989.90,
    "total_tokens": 1126304159,
    "overall_cache_efficiency": 92.66
  },
  "model_combinations": [
    {
      "models": ["opus-4-1", "sonnet-4"],
      "days": 20
    }
  ],
  "daily_statistics": {
    "total_cost": {
      "mean": 31.93,
      "median": 29.54,
      "p95": 65.15,
      "min": 1.14,
      "max": 75.29
    },
    "cost_breakdown": {
      "input": { ... },
      "output": { ... },
      "cache_create": { ... },
      "cache_read": { ... }
    }
  },
  "model_statistics": {
    "opus-4-1": {
      "pricing_per_million_tokens": {
        "input": 15.0,
        "output": 75.0,
        "cache_create": 18.75,
        "cache_read": 1.5
      },
      "statistics": { ... }
    }
  }
}
```

### Key Metrics Explained

#### Cache Efficiency
Calculated as: `(Cache Read Tokens / Total Tokens) × 100`

Higher percentages mean:
- Fewer tokens processed from scratch
- Lower costs (cache reads cost 10-20x less)
- Faster response times

#### Cost Breakdown by Token Type
Your daily cost is composed of:
- **Input tokens**: New prompts and messages
- **Output tokens**: Model-generated responses
- **Cache creation**: First-time caching of context
- **Cache reads**: Reusing cached context (cheapest)

#### Model Combinations
Shows which models were used together on the same day, helping identify usage patterns and transitions between models.

## Example Output

### Daily Cost Analysis
```
Average Daily Cost: $31.93
  - Input tokens: $0.02 (0.06%)
  - Output tokens: $0.98 (3.07%)
  - Cache creation: $15.00 (46.98%)
  - Cache reads: $15.93 (49.89%)
```

### Model Pricing (Per Million Tokens)
```
Claude Opus 4.1:
  - Input: $15.00
  - Output: $75.00
  - Cache Create: $18.75
  - Cache Read: $1.50

Claude Sonnet 4/4.5:
  - Input: $3.00
  - Output: $15.00
  - Cache Create: $3.75
  - Cache Read: $0.30
```

## Customization

### Custom Input/Output Paths

Edit `src/analyze_usage.py` and modify these paths:

```python
# Input file (raw ccusage data)
raw_data_file = '/tmp/claude-usage-raw.json'

# Output files
json_output = '/tmp/claude-usage-analysis.json'
md_output = '/tmp/claude-usage-report.md'
```

### Date Range

When generating raw data, adjust the `--since` parameter:

```bash
# Get all data from September 1, 2025
npx ccusage@latest daily --since 20250901 --breakdown --json > /tmp/claude-usage-raw.json

# Get data from specific date to another
npx ccusage@latest daily --since 20250901 --until 20251001 --breakdown --json > /tmp/claude-usage-raw.json
```

## Sample Files

Check the `examples/` directory for:
- `sample-analysis.json` - Example JSON output
- `sample-report.md` - Example markdown report

## Troubleshooting

### "No such file or directory: /tmp/claude-usage-raw.json"

You need to generate the raw usage data first:
```bash
npx ccusage@latest daily --since 20250701 --breakdown --json > /tmp/claude-usage-raw.json
```

### "Failed to fetch pricing from LiteLLM"

The tool needs internet access to fetch current pricing. If offline, it will fail. Ensure you have a working internet connection.

### Pricing seems outdated

The tool fetches pricing directly from LiteLLM's GitHub repository. If you notice discrepancies:
1. Check https://github.com/BerriAI/litellm/blob/main/model_prices_and_context_window.json
2. Verify your Claude model names match the pricing database

## Architecture

The tool follows a two-step process:

1. **Analysis Phase**:
   - Reads raw ccusage JSON
   - Fetches current pricing from LiteLLM
   - Performs all statistical calculations
   - Saves complete results to JSON

2. **Report Generation Phase**:
   - Reads the analysis JSON
   - Formats data into markdown report
   - No calculations, just formatting

This separation ensures:
- All computed data is available in JSON for automation
- Markdown can be regenerated without re-analysis
- Easy integration with other tools

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

MIT License - see LICENSE file for details

## Acknowledgments

- Built for [Claude Code](https://docs.claude.com/en/docs/claude-code) users
- Pricing data from [LiteLLM](https://github.com/BerriAI/litellm)
- Usage data from [ccusage](https://www.npmjs.com/package/ccusage) CLI tool

## Support

For issues, questions, or suggestions:
- Open an issue on GitHub
- Check existing issues for solutions

## Roadmap

- [ ] Support for custom date ranges via CLI arguments
- [ ] Visualization of usage trends over time
- [ ] Cost optimization recommendations
- [ ] Export to CSV/Excel formats
- [ ] Integration with CI/CD for automated reporting
