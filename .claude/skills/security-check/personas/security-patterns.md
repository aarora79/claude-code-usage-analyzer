# Security Patterns and Anti-Patterns

A catalog of recurring security defect classes, distilled into reusable rules, so that new code and code reviews do not reintroduce the same classes of vulnerability.

These patterns were generalized from real defects fixed across production projects. The vulnerability classes are language- and repo-agnostic; the specific mechanisms named as examples are illustrative. Read each entry for its **rule** and map it to the analogous mechanism in the code actually under review.

**How to use this document:**

- **Writing a feature:** read the patterns that touch your surface (spawning a process? read #6 and R1. Outbound fetch? read #1. Parsing external data? read R2. New logging or report field? read #7 and R3).
- **Reviewing a change:** the [Review Checklist](#review-checklist) at the bottom maps each pattern to a yes/no question. The Security Engineer persona references this file.

Each pattern is written as: **the mistake** -> **the rule** -> **how to enforce it** -> **what to check**.

---

## 1. Server-side fetch of a user/config-controlled URL (SSRF)

**The mistake.** Taking a URL that a user, config, or external source supplied and fetching it with a plain HTTP client. An attacker points it at `169.254.169.254` (cloud metadata), a loopback admin port, or an internal host and exfiltrates a secret or reaches an internal service.

**The rule.** Every server-side fetch of a non-first-party URL is validated and fails closed: `http`/`https` only; the host must resolve exclusively to public IPs; the cloud metadata address is never allowlistable. A fetch of a **fixed vendor constant** (as this tool does for the LiteLLM pricing table) is safe precisely because the URL is not external input -- keep it a constant.

**How to enforce it.** Keep outbound URLs as hardcoded constants. If a URL ever becomes configurable, route it through a validating guard before the fetch.

**What to check.** Does any new code build an HTTP call (`urllib`/`httpx`/`requests`) from a stored or CLI-supplied URL without validation? Is the pricing/remote URL still a fixed HTTPS constant, or did a change make it user-supplied?

---

## 3. Weak, committed, or default-permissive secrets and config

**The mistake.** Shipping a usable insecure default: a hardcoded credential, a dev port bound to `0.0.0.0`, TLS disabled by default.

**The rule.** Secrets have no working default and fail closed. Any server bind defaults to loopback (`127.0.0.1`); public exposure is an explicit opt-in (per `CLAUDE.md`). This tool has no server today -- if one is added, apply the rule.

**What to check.** Any new secret with a working default? Any `0.0.0.0` bind, `verify=False`, or TLS disabled introduced by the change?

---

## 6. Injection through unescaped interpolation

**The mistake.** Building a downstream string (a shell command, a query, markup) by interpolating untrusted input without escaping. For this tool the concrete risk is a subprocess command: interpolating a CLI value like `--since` into a command string, or using `shell=True`.

**The rule.**

- Never interpolate untrusted input into a shell/query/markup context without a context-appropriate escape.
- Shell: use the list form of subprocess, never `shell=True`; pass user data as discrete list arguments, never interpolated into the command (per `CLAUDE.md`).
- Never use `eval`/`exec` on external data; parse JSON with `json.loads`.

**What to check.** Any f-string or `+` that puts CLI/external data into a command, query, or markup string? Any `shell=True`? Any `eval`/`exec` on fetched or parsed data?

---

## 7. Secret and PII leakage into logs and reports

**The mistake.** Logging raw environment, a full request/response dict, or writing credentials or identifying data into a committed report or example file. For this tool: a report or `--debug` log that includes a real project path, a prompt, or a token.

**The rule.**

- Logs and reports record counts, costs, latencies, and model ids -- never credentials, raw prompt content, or project-identifying file paths.
- `--debug` output is more verbose but still redacts secrets; never dump the full environment.
- Committed example data (`examples/`) is fictional or scrubbed, never a real user's usage.

**What to check.** Does new logging print the environment, a token, or a full external payload? Does a new report/example field include a credential, a prompt, or an identifying path?

---

## 8. Dependency CVE exposure

**The mistake.** A dependency floor low enough to permit a version with a known CVE, or carrying an unused dependency that drags in CVE-bearing transitive deps.

**The rule.** Raise manifest floors above the fixed version (not just the lockfile). Remove dependencies that are declared but never imported. Keep the core tool dependency-free where possible (this one uses only the standard library plus an optional matplotlib extra).

**What to check.** Does a new dependency's floor sit above known CVE fixes? Is a newly added dependency actually imported? Was a core dependency added where the standard library would do?

---

## Repository-Specific Patterns

The patterns above are generic. The ones below are specific to **this** repository -- a command-line usage-and-cost analyzer that spawns `ccusage`, fetches a pricing table, and writes reports.

### R1. Spawning the ccusage subprocess

**The mistake.** Building the `npx ccusage` call with `shell=True`, interpolating `--since` or a path into a command string, omitting a timeout, or not handling `TimeoutExpired`/`CalledProcessError`.

**The rule** (mirrors `CLAUDE.md` "Subprocess").

- List form only, never `shell=True`.
- The executable (`npx`) and all flags are hardcoded constants -- never built from user input. The `--since` value and any path are passed as discrete list arguments.
- Always set a `timeout`; always handle `TimeoutExpired` and `CalledProcessError`.
- Every `# nosec B603/B607/B404` carries a justification (hardcoded command, list args, no shell).
- Verify the executable exists (`shutil.which`) and fail with a clear, actionable error if not.

**What to check.** Any new `subprocess.run`/`Popen` with `shell=True`? Any executable or flag built from a variable? A missing `timeout=`? A new `nosec` without a justification comment?

### R2. Parsing untrusted ccusage and LiteLLM output

**The mistake.** Trusting the shape of ccusage stdout or the LiteLLM pricing table -- indexing keys that may be missing or renamed, or worse, `eval`-ing the payload. A ccusage version bump that renames a field (e.g. `date` -> `period`) should degrade gracefully, not crash or silently miscompute.

**The rule.**

- Parse with `json.loads`, never `eval`/`exec`.
- Fail closed with a clear `DataSourceError`/`PricingError` on malformed input, missing top-level keys, or an empty payload.
- Tolerate known field renames (read `date` or `period`); log a warning and skip, rather than crash, when a model has no pricing entry.
- Strip any non-JSON banner lines ccusage prints before parsing.

**What to check.** Does new parsing assume a key exists without a default or guard? Does it `eval` anything? Does it fail closed with an actionable error, or crash with a raw `KeyError`/`JSONDecodeError`?

### R3. Secret and PII hygiene in reports and committed data

**The mistake.** Writing a real project path, prompt content, or credential into a generated report, a `--debug` log, or a committed `examples/` file. Usage JSONL can contain project names in paths; reports and examples must not leak them.

**The rule** (specializes generic pattern #7).

- Reports and metrics record counts, costs, and model ids only.
- Committed `examples/` data is fictional or scrubbed and clearly labeled as such.
- Generated output under `data/` stays gitignored.

**What to check.** Does a new report/example field include an identifying path, prompt, or token? Is generated `data/` output newly committed instead of gitignored?

---

## Review Checklist

Fast pass for a change touching the relevant surface. Any "no" is a blocker until justified.

**Outbound requests**
- [ ] Every remote fetch targets a fixed HTTPS vendor URL, not user/config input (#1)

**Secrets and config**
- [ ] No new secret ships with a working default; any server bind is loopback by default (#3)

**Injection**
- [ ] No CLI/external input interpolated into a command/query/markup without escaping (#6)
- [ ] Subprocess uses the list form; no `shell=True`; no `eval`/`exec` on external data (#6)

**Logging and reports**
- [ ] No environment, token, prompt, or identifying path written into a log, report, or committed example (#7, R3)

**Dependencies**
- [ ] New dependency floors sit above known CVE fixes; unused deps removed (#8)

**This repo (usage analyzer)**
- [ ] The ccusage subprocess uses the list form with a hardcoded executable, a timeout, and `TimeoutExpired`/`CalledProcessError` handling; `nosec` justified (R1)
- [ ] Untrusted ccusage/LiteLLM JSON is parsed with `json.loads`, fails closed on malformed input, and tolerates missing/renamed fields (R2)
- [ ] No identifying path, prompt, or credential written into a report, `--debug` log, or committed example; generated `data/` stays gitignored (R3)

---

*Maintained alongside `CLAUDE.md` (subprocess/secrets/server-binding/Bandit sections). When a new class of security defect is found, add the pattern here so reviews catch the next instance.*
