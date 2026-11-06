---
name: invertebrate
description: Invertebrate — Greptile-style AI code review of a PR, branch, or working-tree diff. Traces every changed symbol through the whole codebase (callers, callees, implementers, LSP references, git history of removed lines) to catch cross-file bugs and reverted fixes, proves each serious finding by running a repro test or build, re-reviews only what changed since its last review, and can propose team rules from past PR review comments ("invertebrate learn"). Outputs Greptile's format, color-coded for non-programmers — safe-to-merge verdict, plain-language summary, 0-5 confidence score, findings table, auto-chosen mermaid diagram, and inline comments with P0/P1/P2 severity, logic/syntax/style type, and suggested-fix diffs — plus an optional visual HTML report with charts. Honors `.invertebrate/` config, falling back to `.greptile/` (rules.md, config.json strictness/commentTypes/rules/ignorePatterns, files.json). Optionally posts the review to a GitHub PR via `gh`. Use ONLY when the user's message explicitly contains the word "invertebrate" (e.g. "invertebrate review PR #12", "run invertebrate on my branch"). Do NOT use for any other code review request — including mentions of Greptile, PR reviews, confidence scores, or `.greptile` folders — unless the word "invertebrate" is present.
---

# Invertebrate — Greptile-style review

Greptile's edge over a linter is **context**: it reviews the diff against a graph of the whole repo, so it catches the rename that left three callers broken, the new endpoint missing the auth decorator every sibling has, the "optimization" that a caller makes a no-op. Reproduce that. A review that only reads the diff is not this skill.

Its second edge is **signal**: every comment is a concrete, verified bug with a fix, not a style essay. Teams turn off reviewers that cry wolf. When in doubt, leave it out.

## 1. Resolve the target

| User gave | Diff source |
|---|---|
| PR number / URL | `gh pr view <n> --json title,body,baseRefName,headRefName,files` + `gh pr diff <n>` |
| Branch | `git diff <base>...HEAD` (three dots = diff from the merge base; base = main/master/develop, whichever exists) |
| Nothing | `git diff HEAD` (staged+unstaged); if empty, the current branch vs its base |
| A `.diff`/`.patch` file | that file; the working tree is the post-change repo |

Read the PR title/description if available (from `gh`, or a description file the user points to). "A security PR ships without the fix" is a real Greptile catch: list each claim the description makes ("fixes X", "adds validation for Y") and check the diff actually delivers it. A claimed fix that isn't in the diff is a finding at the severity of the bug it claims to fix.

**Re-review.** Look for a previous Invertebrate review of the same target: on a PR, the newest review body containing `invertebrate:sha=` (`gh api repos/<owner>/<repo>/pulls/<n>/reviews --paginate`); locally, a previous report the user points to (its footer sha). If found, call its sha `PREV`, and keep its `scores=` list for the score trend (older markers have none: use its `Confidence Score: N/5`):
- `git merge-base --is-ancestor PREV HEAD` succeeds → hunt for new findings only in `git diff PREV..HEAD`, but still build the context graph (§3) against the whole repo.
- It fails (force-push/rebase) → full review.
- Either way, re-check every previous finding against HEAD: `resolved` (the failure no longer reproduces / the code is gone), `open`, or `regressed` (was fixed, broken again). Status comes only from rerunning the previous finding's own repro/scenario: passes → `resolved`, even if you found a related gap. Never re-report an open finding as new. Before writing Findings, compare each new finding with every previous one. If it points at the same file:line or function, or has the same wrong outcome (e.g. another input that still overdraws), it is not new: add it as a note in that finding's status row, not in Findings.

A clean PR is a valid outcome. If verification leaves no findings, say so, score it 4-5/5, and stop — inventing issues to look thorough is the fastest way to get a reviewer muted.

## 2. Load review config

The config folder is `.invertebrate/`. For compatibility with teams already using Greptile, `.greptile/` uses the identical format and is read wherever no `.invertebrate/` exists. Resolve per directory: in each directory, `.invertebrate/` if present, else `.greptile/` — never both from one directory. Check the repo root **and** every directory containing a changed file (monorepo: nearest wins for scalar settings, lists/instructions accumulate from parents). Also accept a legacy root `greptile.json` with the same fields. Never create or modify these folders — they're read-only input.

- `config.json`:
  - `strictness` 1|2|3 (default 2) — see filtering in §5
  - `commentTypes` (default `["logic","syntax","style"]`) — drop findings of unlisted types
  - `ignorePatterns` (gitignore syntax, newline-separated) — skip matching files
  - `instructions` — free-form reviewer guidance, follow it
  - `rules[]` — `{id, rule, scope[glob], severity: low|medium|high, enabled}`; apply only where `scope` matches; `disabledRules` removes inherited ids
- `rules.md` — plain markdown rules for that directory tree
- `files.json` — `{files:[{path, description, scope}]}`: read these files as context when scope matches (or always if no scope)

Neither folder anywhere? Use CLAUDE.md / AGENTS.md / GEMINI.md / CONTRIBUTING.md coding standards as rules instead. Note in the report which config was applied.

The only exception to read-only: in learn mode (§10), when the user explicitly says to save proposed rules.

A rule violation becomes a finding that cites the rule (`Rule: <id or first words>`). Rule severity maps: high→P1, medium→P2, low→P2.

## 3. Build the context graph (the part that matters)

For each changed hunk, identify the symbols it **defines, removes, renames, or changes the signature/semantics of** (functions, methods, classes, types, exported constants, routes, DB columns, config keys, env vars, event names).

**Start with the helper, in one call.** Run `python3 <this skill's base directory>/scripts/context.py` (the base directory is the folder holding this SKILL.md) (`python` if `python3` is missing) with the diff source: `--diff <file>` for a diff file (PR target: save `gh pr diff <n>` to a scratch file first), else the git-diff args from §1 (`main...HEAD`, `HEAD`, `PREV..HEAD`). Add `--base <rev>` when removed lines' history should be read at a revision other than HEAD (the base branch for a branch target). It prints the changed symbols (definitions, plus the function enclosing each changed line), every whole-word reference across the repo with `x as y` aliases followed, files that only share the name (they never mention a changed module), and the commits that last touched each removed line (`FIX?` marks fix-like subjects). That is the first draft of the graph: don't re-grep or re-run `git log -L` for what it already lists. The steps below cover what it can't see: symbols it missed, LSP-only references, string references, siblings, callees, data flow. No Python available → do all of it by hand.

For each such symbol, search the **whole repo**, not just changed files:
- **Callers / references** — if an LSP tool is available (in Claude Code the `LSP` tool; load it via ToolSearch if it is only listed as deferred), use `findReferences` / `incomingCalls` on the symbol's definition (`goToImplementation` for interfaces): it follows aliased imports and re-exports and ignores unrelated symbols that share the name. Then grep the old and new name anyway (your search tool, or `rg`/`git grep`), for what LSP can't see: string references (routes, config keys, env vars, event names, reflection), other languages, and files LSP fails on. No LSP server → grep alone, and chase every alias (`import { x as y }`, `export { x as z }`, `export *`) to its own uses. A removed/renamed symbol with surviving references is a guaranteed bug.
- **History** — for lines the diff deletes or rewrites, read why they exist: `git log -L <start>,<end>:<file> --format='%h %s' <base>` (or `git blame <base> -L <start>,<end> -- <file>`). If the commit that added them reads like a fix (fix, bug, race, CVE, revert, security, an issue number), check whether the PR brings that bug back. A reverted fix is a finding that cites the commit (`Reverts fix <sha> "<subject>"`), at the severity of the original bug.
- **Siblings** — code that does the same kind of thing (other endpoints in the router, other handlers of the same interface, other migrations). New code that skips a pattern every sibling follows (auth decorator, audit log, validation, transaction, lock, `await`) is a top Greptile catch.
- **Callees** — read the implementation of anything the new code calls whose contract matters (does it throw? return null? already lock? is it async?).
- **Data flow** — where inputs come from (user-controlled? URL param?) and where they go (SQL/HogQL, shell, filesystem path, dynamic code execution, HTML).

Keep a short list: `symbol → files that depend on it → what the change does to them`. Use it to write findings; don't dump it in the report.

## 4. Hunt

Walk the diff with the graph in hand. Categories Greptile actually reports, with real examples:

- **Logic** — loop exits early leaving partial state; flag/condition inverted; aliased value escapes a check; warnings never reach the user.
- **Refactoring** — rename leaves callers undefined; moved code drops a side effect.
- **Security** — missing authn/authz on new endpoint; injection via user input into query/shell/path; sandbox/scope escape (symlinks, mounts, `~`, variable expansion); null/missing field bypasses a guard.
- **Validation** — empty/malformed input accepted as valid; valid input rejected; unanchored regex. For every user-controlled value the new code reads (body, query, header, path param), ask what happens when it's missing, `null`, or the wrong type (`request.json` is `None`, a list, or a string, so `.get` raises): a crash there is a 500 reachable from user input.
- **Runtime / Syntax** — call to undefined method; missing `await`; wrong arg count; type mismatch; code that won't compile.
- **Error handling** — swallowed exceptions; raw tracebacks/secrets leaked to clients; resource closed on wrong/undefined handle in the error path.
- **Concurrency** — check-then-act and read-modify-write races; shared mutable state across tasks/threads; startup ordering drops events.
- **Data loss / integrity** — non-atomic writes; double-apply on replay; silent truncation; deleted data reappearing.
- **Performance** — N+1 queries, O(n²) on hot path, an "optimization" that's a silent no-op.
- **Alignment / leakage** — ground truth or secrets exposed through a state/debug endpoint or log.

**Verify every candidate before keeping it.** You must be able to state: the exact line, the concrete input/state that triggers it, and the wrong outcome. If you can't construct the failure, drop it. Re-read the surrounding code — half of plausible-looking bugs are handled three lines later.

### Prove it by running code

A hosted reviewer can only argue a bug exists. You can run it. Every P0/P1 candidate gets a **Proof**, one of:

| Proof | Meaning |
|---|---|
| `repro` | You wrote a minimal test/script, ran it on the post-change code, and it failed exactly as predicted |
| `build` | The project's compiler/typechecker/build reports the error on the post-change code |
| `trace` | Static and deterministic: a reference to a removed/renamed symbol, a reverted fix, or a missing required argument shown by grep/LSP. No runtime doubt left |
| `none` | None of the above |

Procedure:
1. **Where to run.** Working tree, branch or `.diff` target → the repo as it is. PR target → don't touch the user's checkout: `git fetch origin pull/<n>/head:invertebrate-pr-<n>` then `git worktree add <scratch dir>/pr-<n> invertebrate-pr-<n>`; remove both when done. Running a PR runs its author's code: if the PR comes from a fork or someone other than the user, ask before executing anything.
2. **Build check.** If the project has a typecheck/build command whose tool is already installed (`tsc --noEmit`, `cargo check`, `go build ./...`, `mypy`, the `build`/`typecheck` script in package.json), run it once. New errors in changed or dependent files are `build` proofs and become P0.
3. **Repro.** For each remaining candidate, write the smallest test that triggers the failure scenario, using the project's test runner if it is already installed, else a stdlib-only script with plain asserts. Name it `invertebrate_repro_<n>` next to the project's tests, run it with a timeout, then delete it. The test must **assert correct behavior**, so it fails while the bug exists.
   - Fails as predicted → `repro`.
   - Passes → the bug doesn't happen. Drop the finding.
   - Fails for another reason (import error, missing fixture) → fix the test, at most twice, else `none`.
   - Framework not installed (Flask, Django, Express…) → don't give up: stub the boundary instead (put a fake module in `sys.modules`, or pass a fake `request` object) and call the handler directly. A missing framework alone is not a reason for `none`.
4. **Never** install dependencies, hit the network, or touch real databases/services to get a proof. If proving needs that, the proof is `none`.
5. **Order.** All proofs run on the unmodified post-change code, before the report is written and before any file is edited, even when the same message also asks for fixes. A `repro` label requires a run you executed that failed; a test that was only run after a fix proves nothing.
6. After the last run, no repro files may be left behind: check `git status --porcelain`, or list the directory if it isn't a git repo.

A P0/P1 with proof `none` drops one severity level (P0→P1, P1→P2) before filtering. Keep each repro's source: it goes in the inline comment so the reader can run it, and the fix loop (§8) reruns it.

## 5. Classify and filter

Each finding gets:
- **Severity** — **P0** must fix before merge (security hole, data loss, crash on a common path, build break). A missing auth, permission, or ownership check that lets one user read or change another user's data is a security hole: always P0, even when the fix is one line and even when another finding in the same function is P1. **P1** should fix (wrong behavior, broken edge case, rule violation with high severity). **P2** consider (maintainability, minor perf, low-severity rule).
- **Type** — `logic` (bugs, behavior, edge cases), `syntax` (won't compile/run, language misuse), `style` (quality, naming, conventions).

Filter by `strictness`:
- **1** — keep P0, P1, P2.
- **2** (default) — keep P0, P1; keep P2 only if it violates an explicit configured rule.
- **3** — keep P0, plus these P1s: security, crashes/500s reachable from user input, and violations of `high`-severity configured rules. Strictness 3 means "only what would page someone or that the team explicitly asked for", and a remotely triggerable crash qualifies.

Then drop types not in `commentTypes`. Pure formatting a formatter would fix: never report. A filtered finding may get at most one footer line naming it as filtered, with no advice to fix it anyway.

## 6. Confidence score (0-5)

| Score | Color + meter | Safe to merge? | Meaning |
|---|---|---|---|
| 5/5 | 🟢 ●●●●● | Yes | Production ready — merge |
| 4/5 | 🟢 ●●●●○ | After small fixes | Minor polish — merge after small fixes (only P2s) |
| 3/5 | 🟡 ●●●○○ | Not yet | Implementation issues — address feedback first (any P1) |
| 2/5 | 🟠 ●●○○○ | No | Significant bugs — needs rework (multiple P1s, or one P0 that's easy to fix) |
| 0-1/5 | 🔴 ●○○○○ / ○○○○○ | No | Critical problems — rethink (P0 security/data-loss, or design is wrong) |

Scores are contextual: the same bug in payments/auth/migrations scores lower than in an internal script. Give one sentence of justification.

## 7. Diagram

Pick by what changed; skip for trivial diffs (docs, config bumps, <~20 lines of local logic):
- **sequenceDiagram** — multi-component interactions, API/request flows, async/concurrent ordering (show the race if there is one)
- **erDiagram** — schema / data model changes
- **classDiagram** — class/interface hierarchy changes
- **flowchart** — control flow / business logic changes

Diagram the change, not the whole system. Keep it under ~15 nodes. Mark the buggy step with a `Note` / label.

## 8. Output

The report is also read by people who don't write code. Every code gets a color and a plain word next to it:

| Code | Shown as |
|---|---|
| P0 / P1 / P2 | 🔴 P0 Critical / 🟠 P1 High / 🟡 P2 Medium |
| logic / syntax / style | Bug (logic) / Won't compile (syntax) / Cleanup (style) |
| repro / build / trace / none | Proven by test (repro) / Proven by build (build) / Found by search (trace) / Unproven (none) |
| resolved / open / regressed | ✅ resolved / ⚠️ open / 🔴 regressed |

Use exactly this structure (sections may be omitted only where noted):

````markdown
## Invertebrate Review — <PR title or branch>

**Safe to merge? <answer from §6>** — <one sentence a non-programmer understands: the biggest problem and who it hurts, or "no problems found">

### Summary
<2-4 sentences, plain language: what the change does, who/what it affects, why. Then 1 sentence on the main risk.>

### Confidence Score: <color> N/5 <meter>
<one sentence why>

### Since last review (<PREV sha, 7 chars>) · score <all scores from the marker, then this one, e.g. 1/5 → 2/5 → 4/5>
| # | Previous finding | Status |
|---|---|---|
| 1 | <title> | ✅ resolved / ⚠️ open / 🔴 regressed |
(omit section unless this is a re-review)

### Findings
| # | Severity | Type | Proof | Location | Issue |
|---|---|---|---|---|---|
| 1 | 🔴 P0 Critical | Bug (logic) | Proven by test (repro) | `path/file.ts:42` | <short title> |
(If none: "✅ No issues found." On a re-review, list only new findings here.)

### Diagram
```mermaid
...
```
(omit section for trivial changes)

### Inline Comments

#### 1. 🔴 [P0 · logic] <short title>
`path/file.ts:42`

<What's wrong, the concrete failure scenario, and — if cross-file — which other files break and why. 2-5 sentences.>

```diff
- old line
+ fixed line
```

<details><summary>Repro (failed on this commit)</summary>

```python
<the repro test, verbatim, and the command that ran it>
```
</details>
(only for `repro` proofs; for `build`, quote the compiler error line instead)

#### 2. ...

---
<sub>Reviewed <N> files · config: <.invertebrate or .greptile path | CLAUDE.md / AGENTS.md | defaults> · strictness <n> · <commit sha if known></sub>
<!-- invertebrate:sha=<full head sha> scores=<previous scores from the marker, then this one, comma-separated, e.g. 1,2,4> -->
````

Suggested-fix diffs must be real, minimal, and apply to the actual code. If the fix spans files, show each file's hunk with its path as a heading line. If no safe one-hunk fix exists, describe it instead of inventing one.

After the report, offer: "Say `fix all`, `fix P0`, or `fix #2` and I'll apply them, or `html` for a visual report you can share." Don't apply fixes unprompted.

**Visual report** (only when asked: `html`, "visual report", "something I can show my manager"). Write the review you just gave as JSON to a temp file outside the repo (e.g. `invertebrate-review-<sha7>.json` in the OS temp folder), then run `python3 <this skill's base directory>/scripts/report.py <that file>`. It writes a self-contained `.html` next to it with a colored verdict, a findings-by-severity bar chart, the score trend, the rendered diagram, and one card per finding, and prints its path. Open it in the default browser and give the user the path. No Python → say the visual report needs Python. Shape (same content as the markdown report; omit keys that don't apply):

```json
{"title": "<PR title or branch>", "verdict": "<the Safe-to-merge sentence>", "score": 2,
 "score_reason": "<why>", "scores": [1, 2], "summary": "<summary>",
 "since_last": [{"title": "<previous finding>", "status": "resolved|open|regressed"}],
 "findings": [{"n": 1, "sev": "P0", "type": "logic", "proof": "repro", "location": "path/file.ts:42",
   "title": "<short title>", "body": "<what's wrong>", "diff": "- old\n+ new",
   "repro": "<the repro test and command, or the compiler error>"}],
 "diagram": <see below>, "footer": "<the footer line>"}
```

`scores` is the same history as the marker, ending with this score. `diagram` is the §7 diagram as data, not mermaid text. Mark the buggy step with `"bad": true`.
- sequenceDiagram → `{"kind": "sequence", "actors": ["Client", "API"], "steps": [{"from": "Client", "to": "API", "label": "POST /pay"}, {"note": "charged twice", "over": "API", "bad": true}]}`
- flowchart / classDiagram / erDiagram → `{"kind": "graph", "nodes": [{"id": "a", "label": "Order", "fields": ["id: int", "total_cents: int"]}], "edges": [{"from": "a", "to": "b", "label": "1 to many"}]}`. Class members and table columns go in `fields`; ER cardinality goes in the edge label.

**Fix loop.** When asked to fix, for each selected finding:
1. Apply the fix.
2. Recreate its repro from the report, run it, and delete it again. It must now **pass**. For a `build` proof, rerun the build. For `trace`, re-grep: no surviving references.
3. Run the project's existing tests that cover the changed files, if the runner is installed.
4. Report per finding: `fixed (repro passes)`, `fixed (build clean)`, `fixed (no references left)`, or `NOT fixed: <what still fails>`. Never claim a fix that the proof doesn't confirm. Findings with proof `none` are reported as `applied, unverified`.

## 9. Posting to GitHub (only when asked: `--post`, "post it", "comment on the PR")

Posting is outward-facing — only do it on an explicit request for that PR.

1. Get `owner/repo` (`gh repo view --json nameWithOwner -q .nameWithOwner`) and head sha (`gh pr view <n> --json headRefOid -q .headRefOid`).
2. Inline comments can only target lines present in the PR diff (RIGHT side, new line numbers). Findings on lines outside the diff go into the summary body only. On a re-review, post inline comments for new findings only; the "Since last review" table covers the old ones. The body must keep the `invertebrate:sha=` marker so the next run can find it.
3. Write the review JSON to a temp file and post it in one call:

```json
{
  "commit_id": "<head sha>",
  "event": "COMMENT",
  "body": "<the full markdown report from §8 minus the Inline Comments section>",
  "comments": [
    {"path": "src/file.ts", "line": 42, "side": "RIGHT",
     "body": "**P0 · logic** — <title>\n\n<explanation>\n\n```suggestion\n<replacement for exactly line 42>\n```"}
  ]
}
```

```bash
gh api repos/<owner>/<repo>/pulls/<n>/reviews --method POST --input review.json
```

Use GitHub ```` ```suggestion ```` blocks only when the replacement covers exactly the commented line(s) (use `start_line` + `line` for multi-line). Otherwise use a ```` ```diff ```` block. Never use `REQUEST_CHANGES`/`APPROVE` unless the user asks. Report the review URL from the response.

## 10. Learn mode (`invertebrate learn`)

Propose team rules from the repo's own review history. No server, nothing stored.

1. List recent merged PRs: `gh pr list --state merged --limit 30 --json number,title`.
2. For each, fetch review comments: `gh api repos/<owner>/<repo>/pulls/<n>/comments --paginate`. Each has `body`, `path`, `user.login`, `position` (null = the commented line changed later, i.e. outdated) and `reactions` (`+1`, `-1`).
3. Classify each comment:
   - **accepted**: outdated (`position` null) after a later commit, a `+1` reaction, or a reply agreeing ("fixed", "done", "good catch").
   - **rejected**: a `-1` reaction, or a reply dismissing it ("won't fix", "intended", "not an issue").
   - Otherwise ignore it.
4. Group by underlying concern (e.g. "mutating endpoints need audit_log", "no raw SQL strings"). A concern becomes a proposed rule only when it is **accepted at least twice** and never rejected. A concern rejected at least twice becomes a proposed **ignore** instruction ("don't flag X").
5. Output a proposed `rules.md` block and `config.json` `rules[]` entries, each with a scope glob taken from the files involved and the PR numbers as evidence. Then ask: "Say `save them` to write these to `.invertebrate/`."
6. Only on `save them`: append to the repo-root `.invertebrate/rules.md` / merge into `.invertebrate/config.json` (create the folder if it doesn't exist; never edit `.greptile/`). Show the resulting diff.
