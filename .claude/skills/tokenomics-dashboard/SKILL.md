---
name: tokenomics-dashboard
description: "Generate the Claude Code tokenomics dashboard for a chosen number of days of history and present it with a director-level commentary. Ask the user for one input only, the number of days of history to analyze, then state that you will fetch that data using the ccusage tool, run the analyzer, and open the resulting self-contained HTML dashboard with a written cost-governance summary. Trigger when the user asks for a tokenomics dashboard, a usage/cost dashboard, a spend review, or 'analyze my last N days of Claude Code usage'."
license: Apache-2.0
metadata:
  author: Amit Arora
  version: "1.0"
---

# Tokenomics Dashboard Skill

Produce the self-contained HTML tokenomics dashboard for a chosen window of Claude Code usage, then present it to the user with a director-of-tokenomics commentary. This wraps the `claude-usage-analyzer` CLI, which fetches usage via `ccusage`, prices it from LiteLLM, and writes the dashboard to `data/output/tokenomics-dashboard.html`.

## The one input: number of days

The skill takes exactly one input from the user: **how many days of history to analyze.**

1. If the user already gave a number ("last 30 days", "past 2 weeks"), use it and skip the question.
2. Otherwise ask, and only this: "How many days of history should I analyze?" Offer sensible options (7, 30, 90) and note they can enter another number.
3. State plainly, before fetching: **"I will get this data using the ccusage tool."** ccusage reads Claude Code's local usage files; nothing is uploaded.

Do not ask about output paths, formats, or models. Those are fixed: the analyzer always writes to `data/output/` and prices every model dynamically.

## Workflow

### Step 1: Confirm the window and compute the start date

Convert the number of days into a `--since` date in `YYYYMMDD` format. The analyzer's `--since` is an inclusive start date, so for "last N days" use today minus (N - 1) days. Get today's date from the environment context; do not guess it. Tell the user the resulting date range you will analyze.

### Step 2: Run the analyzer (it fetches via ccusage)

From the repository root, run the CLI with a refresh so the window is re-fetched, not served from a stale cache:

```bash
uv run claude-usage-analyzer --since <YYYYMMDD> --refresh
```

- Announce that this uses `npx ccusage@latest` under the hood to read local usage data, then prices it from LiteLLM.
- If `npx`/`ccusage` is unavailable, the tool prints an actionable error; relay it and stop rather than inventing numbers.
- The run writes `data/output/tokenomics-dashboard.html`, `claude-usage-report.md`, and `claude-usage-analysis.json`.

### Step 3: Read the numbers, do not invent them

Read `data/output/claude-usage-analysis.json` for the real figures. Every number in your commentary must come from that file (or the Markdown report). Never estimate or carry over numbers from a previous run.

Pull at least: total cost, mean/median/P95 daily cost, overall cache efficiency, the cost split by token type, the primary model and its share, and the monthly projection (mean daily cost times 30). The `daily_series` array holds the per-day points; the dashboard flags days beyond mean +/- 2 sigma as anomalies, so identify those from the series if you want to call them out.

### Step 4: Present the dashboard with commentary

Point the user to the file (`data/output/tokenomics-dashboard.html`) and tell them it is self-contained: it opens directly in any browser with no server or dependencies. If a browser or screenshot tool is available and helpful, you may render it to confirm it looks right; this is optional.

Then write a **director-of-tokenomics commentary** in the same spirit as the dashboard's own insight cards. Keep it tight and decision-oriented:

- **Headline:** total spend for the window and the monthly run-rate projection.
- **Cost structure:** the cache-vs-fresh split, since caching usually dominates; call out whether prompt volume is or is not the cost lever.
- **Concentration risk:** the primary model and its share of spend (a single-model mix is a risk to name).
- **Anomalies:** any day beyond the +/- 2 sigma bands, with the plain-language reason (for example, a cache-read-heavy spike), and suggest tying it to a specific initiative.
- **One or two actions:** concrete, cost-governance-oriented next steps.

Use plain text and Markdown tables where helpful. No emojis (per `CLAUDE.md`). Keep figures directional and honest; if the window is short or has few active days, say the statistics are thin rather than over-reading them.

## Constraints

- **One input only:** number of days. Everything else is fixed.
- **Always say you will use ccusage** before fetching, so the user knows where the data comes from.
- **Never fabricate numbers:** read them from the generated JSON/Markdown, not from memory or a prior run.
- **No emojis** in any output.
- The generated `data/` output is gitignored; do not commit it.
