# Claude Coding Rules

## Overview

Coding standards and best practices for all code in this repository. These rules prioritize maintainability, simplicity, and modern Python development.

## Core Principles

- Write code with minimal complexity for maximum maintainability and clarity.
- Choose simple, readable solutions over clever or complex implementations.
- Prioritize code that any team member can confidently understand, modify, and debug.

## What this repository is

A command-line usage-and-cost analysis tool for Claude Code. It shells out to the `ccusage` npm CLI to gather aggregated usage data, downloads a pricing table from LiteLLM over HTTPS, computes statistics, and writes a JSON analysis, a Markdown report, and a self-contained HTML dashboard, plus optional PNG charts. There is no web server or database. Pricing is resolved dynamically from LiteLLM against whatever models appear in the data, so new models work with no code change.

## Technology Stack

### Package Management

- Always use `uv` and `pyproject.toml` for package management. Never use `pip` directly.

### Libraries

- The core tool depends only on the Python standard library, so it runs with `uv run` and no install step. Charts are an optional extra (`matplotlib`, `numpy`) declared under `[project.optional-dependencies]`.
- **Formatting/Linting**: use `ruff` for both linting and formatting.
- **Type Checking**: use `mypy`.
- **Security**: use `bandit`.
- **Testing**: use `pytest` with `pytest-cov`.
- Do not add a runtime dependency where the standard library will do.

## Code Style

### Function Structure

- Internal/private functions start with an underscore (`_`) and are placed at the top of the file, followed by public functions.
- Keep functions modular -- no more than 30-50 lines.
- Two blank lines between function definitions; one parameter per line for readability.

### Type Annotations (Python 3.10+)

Use modern PEP 604/585 syntax -- built-in generics and `|` unions -- instead of importing from `typing`.

```python
# Good -- modern syntax
def resolve_pricing_map(
    model_names: list[str],
) -> dict[str, dict[str, Any]]:
    ...

# Avoid -- legacy syntax
from typing import Optional, List, Dict
def resolve_pricing_map(model_names: List[str]) -> Dict[str, Dict]:
    ...
```

- `X | None` instead of `Optional[X]`.
- `list`, `dict`, `tuple`, `set` directly instead of `List`, `Dict`, `Tuple`, `Set`.
- Use `collections.abc.Sequence` for read-only list-like parameters to avoid invariance errors under mypy.

### Main Function Pattern

- `main()` acts as a control-flow orchestrator: parse arguments and delegate to other functions.
- Do not implement business logic directly in `main()`. See `__main__.py` for the pattern.

### Module Organization

The package is split by responsibility so the logic stays testable:

- `constants.py` -- shared constants (URLs, timeouts, default paths). No constants hardcoded inside functions.
- `data_source.py` -- fetch and load ccusage data (the only subprocess site).
- `pricing.py` -- resolve model pricing dynamically from LiteLLM.
- `analysis.py` -- pure statistical analysis; no I/O, so it is trivial to unit test.
- `reporting.py` -- format the analysis into the Markdown report; no calculation.
- `dashboard.py` -- render the self-contained HTML dashboard from the analysis (data-viz method: validated palette, mean baselines, 2 sigma anomaly bands, table-view relief, dark mode). No calculation beyond deriving chart context.
- `charts.py` -- optional matplotlib charts; degrades to no-op when matplotlib is absent.
- `__main__.py` -- CLI orchestration only.

Keep analysis pure (no I/O) and keep reporting free of calculation, so every output format shows the same numbers.

### Command-Line Interface Design

- Use `argparse` with comprehensive help and examples in the epilog.
- Provide sensible defaults; expose a `--debug` flag that raises the log level to `DEBUG`.

### Constants

- Don't hard-code constants inside functions. Declare them in `constants.py`.

### Logging

- Configure logging with `basicConfig` at `INFO` level, using this exact format:

  ```python
  import logging

  logging.basicConfig(
      level=logging.INFO,
      format="%(asctime)s,p%(process)s,{%(filename)s:%(lineno)d},%(levelname)s,%(message)s",
  )
  ```

- Add sufficient log messages for debugging; use `logging.debug()` freely behind `--debug`.
- For long-running operations, report elapsed time on completion (the analyzer does this).
- Never log secrets, raw environment, or project-identifying paths (see Security).

### Avoid Deep Nesting

- Limit nesting to 2-3 levels. Use early returns and extract nested logic into well-named helper functions.

### Code Validation

After editing a Python file, run, from the `uv` project root:

```bash
uv run python -m py_compile <filename>
uv run ruff format <filename>
uv run ruff check --fix <filename>
```

CI (and the pre-commit workflow) will fail if a committed file is not ruff-formatted, so treat formatting as part of the edit, not an afterthought.

## Error Handling

- Use specific exception types; avoid bare `except:`.
- Use custom, domain-specific exceptions: `DataSourceError` (data_source), `PricingError` (pricing).
- Always log exceptions with context; fail fast and clearly -- don't suppress errors silently.
- Write clear, actionable error messages that include what was attempted and suggest a fix.

```python
try:
    data = json.loads(content)
except json.JSONDecodeError as exc:
    raise DataSourceError(
        f"Raw usage file {raw_data_path} is not valid JSON: {exc}"
    ) from exc
```

## Testing

- Use `pytest` as the primary framework, with `pytest-cov` for coverage.
- Follow the AAA pattern (Arrange, Act, Assert); use descriptive test names.
- Keep the network out of tests: stub `_download_pricing_table` and the ccusage subprocess with `monkeypatch`; use fixtures (`sample_raw_data`, `sample_pricing_map` in `conftest.py`) for shared data.
- Test both happy paths and error cases (missing file, invalid JSON, missing keys, zero-token days, unknown models).
- Run the full suite before submitting a PR. A PR with failing tests should never be merged.

```bash
uv run pytest -q
```

## Documentation

Use Google-style docstrings for all public and private functions, with modern type hints in the signature, documented exceptions, and a one-line summary.

## Security

The security surface here is narrow but real: spawning a subprocess, fetching a remote URL, parsing untrusted JSON, and writing reports.

### Subprocess

- Always use the list form (never `shell=True`), always set a `timeout`, and always handle `TimeoutExpired` and `CalledProcessError`.
- The executable and flags are hardcoded constants -- never built from user input. CLI values like `--since` are passed as discrete list arguments, never interpolated into a command string.
- Verify the executable exists (`shutil.which`) and fail with a clear message if not.
- Every `# nosec B603 B607 B404` suppression must include a justification.

```python
result = subprocess.run(  # noqa: S603  # nosec B603 - hardcoded command, list args, no shell
    ["npx", CCUSAGE_PACKAGE, "daily", "--since", since_date, "--breakdown", "--json"],
    capture_output=True,
    text=True,
    check=True,
    timeout=CCUSAGE_FETCH_TIMEOUT_SECONDS,
)
```

### Remote fetch

- Outbound URLs (the LiteLLM pricing table) are fixed HTTPS vendor constants, never user- or config-supplied. If a URL ever becomes configurable, validate it before fetching (SSRF).
- Parse fetched JSON with `json.loads`, never `eval`/`exec`.

### Untrusted input

- ccusage stdout and the LiteLLM table are untrusted. Fail closed with a clear error on malformed input, tolerate known field renames (`date` -> `period`), and skip-with-warning when a model has no pricing rather than crashing.

### Secrets and logging

- Never log secrets, raw environment, or project-identifying file paths. Never hardcode secrets; read them from environment variables.
- Committed `examples/` data is fictional or scrubbed; generated `data/` output stays gitignored.

### Server binding

- This tool binds no ports. If a server is ever added, bind to `127.0.0.1` by default; non-loopback exposure is an explicit, documented opt-in.

### Bandit scanning

- Run `uv run bandit -r src/` regularly. Handle false positives with a `# nosec <code>` comment that includes a clear justification.

### Mandatory Security Gate (`security-check` skill)

Run the `security-check` skill (the Cipher security-engineer persona) as a required gate:

- **Before every commit and before opening or updating a PR.**
- **Whenever a new enhancement, feature, or refactor is added.**

The skill reviews the pending diff against a catalog of security anti-patterns (SSRF, injection, subprocess safety, secret/PII log leakage, weak defaults, dependency CVEs, untrusted-input parsing), reports findings in the Cipher format, and fixes any problems it finds. Do not commit while the verdict is NEEDS REVISION. This gate is in addition to the Bandit scan, not a replacement. See [.claude/skills/security-check/SKILL.md](.claude/skills/security-check/SKILL.md).

## Development Workflow

Recommended tools: **Ruff** (lint + format), **Bandit** (security), **MyPy** (types), **Pytest** (tests). Run these before committing:

```bash
uv run ruff check --fix . && uv run ruff format . && uv run bandit -r src/ && uv run mypy src/ && uv run pytest
```

Ruff config targets Python 3.10+ (100-char lines) and auto-modernizes type hints (PEP 604/585) and imports.

## Dependency Management

- Always specify `requires-python` in `pyproject.toml` (`>=3.10`).
- Keep the core tool dependency-free; declare optional features under `[project.optional-dependencies]` and dev tools under `[dependency-groups]`.
- Pin floors above known CVE fixes; remove unused dependencies.

## Project Structure

```text
claude_code_usage_analyzer/
|-- src/claude_code_usage_analyzer/
|   |-- __main__.py        # CLI orchestration
|   |-- constants.py
|   |-- data_source.py     # ccusage subprocess + loading
|   |-- pricing.py         # dynamic LiteLLM pricing
|   |-- analysis.py        # pure statistics
|   |-- reporting.py       # Markdown report
|   |-- dashboard.py       # self-contained HTML dashboard
|   `-- charts.py          # optional matplotlib
|-- tests/                 # pytest suite
|-- examples/              # fictional sample outputs
|-- data/                  # generated output (gitignored)
|-- pyproject.toml
|-- README.md
`-- CLAUDE.md
```

## Platform Naming

- Always refer to the service as "Amazon Bedrock" (never "AWS Bedrock").

## GitHub Commit and Pull Request Guidelines

- Keep commit messages clean and professional.
- Do not include auto-generated attribution such as "Generated with Claude Code" or "Co-Authored-By: Claude".
- PR descriptions should be professional and focus on the technical changes.

## Documentation Guidelines

- Never add emojis to source code, comments, docstrings, documentation files, log messages, or shell scripts -- plain text only.
- Never use em-dashes in prose; use a comma, a colon, parentheses, or two sentences instead.
- A good README includes prerequisites, links to external resources, clear command examples, a development-workflow section, and performance notes.

## Scratchpad for Planning & Design

- Keep a `.scratchpad/` folder (added to `.gitignore`) for temporary planning documents. These files are temporary, local-only, and not suitable for long-term documentation.

## Summary

- **Simplicity first**: write code an entry-level developer can maintain.
- **Modern Python**: use 3.10+ features (PEP 604/585 type hints).
- **Stdlib core**: no runtime dependency where the standard library will do.
- **Security**: follow the subprocess, remote-fetch, untrusted-input, and secrets rules; run the `security-check` gate.
- **Type safety and tests**: keep mypy clean and the pytest suite green.

Always prioritize simplicity and clarity over cleverness.
