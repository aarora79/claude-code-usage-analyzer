---
name: security-check
description: "Run the Cipher security-engineer persona over the repository's pending changes to catch and fix security problems before any commit or enhancement. Reviews the working diff against a catalog of real-world security anti-patterns (SSRF, injection, subprocess safety, secret/PII log leakage, weak defaults, dependency CVEs, untrusted-data parsing), reports findings with severity, and applies fixes. Invoke before committing, before opening a PR, and whenever a new enhancement is added."
license: Apache-2.0
metadata:
  author: Amit Arora
  version: "1.0"
  adapted-from: aarora79/agentic-coding-harness-benchmarks .claude/skills/security-check
---

# Security Check Skill (Cipher)

Run a focused security review over the repository's pending changes, adopting the **Cipher** security-engineer persona, and fix any security problems found before code is committed.

This skill is the security gate referenced by `CLAUDE.md`. It MUST be run:

- **Before any commit** on any branch.
- **Before opening or updating a PR.**
- **Whenever a new enhancement, feature, or refactor is added** — both before writing security-sensitive code (to know the rules) and after implementing it (to catch regressions).

## Reference material (read first)

Two bundled files define the review:

1. [personas/security-engineer.md](personas/security-engineer.md) — the Cipher persona: scope, evaluation areas, review questions, and the output format.
2. [personas/security-patterns.md](personas/security-patterns.md) — the catalog of security anti-patterns and the [Review Checklist](personas/security-patterns.md#review-checklist). This is the substantive source of truth for what counts as a defect.

**Read `security-patterns.md` before reviewing.** For every changed file, walk its Review Checklist and flag any pattern the diff reintroduces. Treat a matched anti-pattern as a blocker until it is justified or fixed.

### What this repository is

This is a **command-line usage-and-cost analysis tool** for Claude Code. It shells out to the `ccusage` CLI (via `npx`) to gather usage data, downloads a pricing table from LiteLLM over HTTPS, computes statistics, and writes JSON/Markdown/Quarto reports plus charts. There is no web server, no authentication surface, and no database.

So the dominant security surface here is narrow but real: **spawning a subprocess (`npx ccusage`), fetching a remote URL, parsing untrusted JSON from both, and writing reports that could leak data.** The classic web-auth patterns (broken access control, CSRF, token boundaries) do not apply unless a change adds an HTTP surface; the day-to-day risk lives in subprocess safety, SSRF/URL handling, untrusted-input parsing, and log/report hygiene.

## Workflow

### Step 1: Determine the scope of changes

Look only at what is pending — do not audit the whole repo.

```bash
git status --porcelain
git diff HEAD
# If reviewing a branch before a PR, compare against the base branch instead:
git merge-base HEAD main   # then: git diff <merge-base>..HEAD
```

The review scope is exactly the set of changed and added files. Do not read generated or large paths (`data/`, `.venv/`, `*.png`) or any secret file, even if it appears in the diff.

### Step 2: Read the persona and the pattern catalog

Read [personas/security-engineer.md](personas/security-engineer.md) and [personas/security-patterns.md](personas/security-patterns.md) in full. Cross-reference the checklist items against this repo's own security rules in the root `CLAUDE.md` (subprocess, secrets, server-binding, and Bandit sections) — those are additional blockers.

### Step 3: Walk the checklist against each changed file

For each changed file, evaluate every relevant checklist item. The classes that most often apply in this repo:

- **Subprocess safety (R1, #6):** any `subprocess` call must use the list form, a hardcoded executable, a timeout, and handle `TimeoutExpired`/`CalledProcessError`. No `shell=True`. User/CLI input (like `--since`) is passed as a discrete list argument, never interpolated into a command string.
- **Remote fetch / SSRF (#1):** the pricing URL and any new outbound fetch must be a fixed HTTPS vendor constant, not a user- or config-supplied URL. A `urlopen`/`requests` call built from external input is a blocker.
- **Untrusted-input parsing (R2, #6):** ccusage output and the LiteLLM table are untrusted JSON. Parsing must fail closed (clear error), never `eval`, and must tolerate missing/renamed fields rather than crashing.
- **Secret / PII leakage (R3, #7):** reports, logs, and committed example data record counts/costs/model ids, never file paths that reveal project names, credentials, or prompt content. `--debug` logging must not dump secrets.
- **Weak defaults (#3):** no server bind (this tool has none); if one is added it must default to `127.0.0.1`.
- **Dependency CVEs (#8):** new dependency floors sit above known CVE fixes; unused deps removed.

### Step 4: Report findings using the Cipher output format

Produce a review using the **Review Output Format** section of [personas/security-engineer.md](personas/security-engineer.md): assessment, security checklist, strengths, vulnerabilities/concerns, OWASP table, recommendations, and a final verdict of **APPROVED / APPROVED WITH CHANGES / NEEDS REVISION**.

For each concern, state the file and line, the pattern number it matches, the concrete failure scenario (input -> impact), and the fix.

### Step 5: Fix the security problems

This skill does not stop at reporting. For every confirmed finding:

1. Apply the fix directly, following the rule in the matching pattern and this repo's `CLAUDE.md` conventions.
2. Re-run the relevant validation: `uv run bandit -r src/` for Python, `uv run python -m py_compile <file>` after Python edits, `uv run ruff check <file>`.
3. Re-check the item to confirm the anti-pattern is gone.

Handle Bandit false positives with a `# nosec <code>` comment that includes a clear justification, as `CLAUDE.md` requires.

Do not commit on the user's behalf. When the verdict is APPROVED (or APPROVED WITH CHANGES and the changes are applied), report that the security gate has passed and it is safe to commit; the user (or the calling workflow) performs the commit.

## Constraints

- **Scope is the pending diff**, not the whole repository. Do not proactively scan unrelated code.
- **No emojis** in any output (per `CLAUDE.md` documentation guidelines).
- **Fail closed.** If a checklist item cannot be verified as safe, treat it as a blocker rather than assuming it is fine.
- **Never read secrets** (`*.pem`, `*.key`, `.env`) even if they appear in the diff; flag their presence instead.
