# Roadmap

How Invertebrate closes the gaps against hosted reviewers (Greptile, CodeRabbit), then gets measured against them head to head.

## Where things stand (measured 2026-11-06)

- `python evals/summarize.py`, newest run of each case: **$0.37 / 91s / 8 agent turns per review**, vs $0.18 / 61s / 4 turns for the same model with no skill.
- `context.py` `find_refs` loads every repo file into memory and runs a Python regex over every line once per changed symbol. Cost grows with symbols × repo size, so monorepos hurt most.
- Only runs when someone types "invertebrate". No CI, no history view.
- Evidence is 11 seeded-bug evals. No real-world cases, no comparison with competitors.

## Status (1.5.0, 2026-11-06)

| Step | State | Evidence |
|---|---|---|
| 1. `git grep` search | ✅ done | 50k files / 5M lines: 20.4s → 4.4s warm (338s cold before), output byte-identical. `tests/test_context.py` covers git + non-git paths; mutants fail it. |
| 2. CI workflow | ✅ built, ⏳ live run | `examples/invertebrate.yml`, `tests/test_workflow.py` (mutants fail it). Not yet run on a real PR with either auth method. |
| 3. Cost | ❌ no gain, stopped | Profile of 33 runs: with-skill median 8 turns, 162k cache-read / 24k cache-write / 4.4k output tokens vs 60k / 12k / 2.1k without. Cache reads (turns × context) dominate. Change tried: batch repro write+run+delete and the build check into one shell call. Re-measured on 1.5.0 (7 cases, 21 runs): median turns 8 → 8, cost $0.36 → $0.38. Not a measurable cut; the extra cost probably comes from the longer SKILL.md (linked issues, dashboard), not proven. Moving learn/visual-report text out of SKILL.md would save ~3%: not worth an extra Read turn. Per the done-when rule: recorded, stopped. |
| 4. Real-world evals | ✅ built, ⏳ run | 5 cases (`evals/real-*`) from upstream fixes: minimist 38a4d1c, pyjwt 2798504, cachetools 39b31bc + bcf9e81, humanize a47a89e. Scaffolds verified. |
| 5. Linked issues | ✅ done | SKILL.md §1. Eval `issue-requirement-missed`: with skill 15/15 grader checks over 3 runs; no skill misses severity + format every run. `clean-pr-no-issues` still 12/12 with skill. |
| 6. Dashboard | ✅ done | `scripts/dashboard.py` + marker counts, `tests/test_dashboard.py` (mutants fail it), checked light 1280px + dark 390px. |

⏳ = needs billed eval runs or a live GitHub repo.

## Gaps and plan

Ordered cheapest-and-measurable first.

### 1. Big monorepos: reference search via `git grep`

- `find_refs`: one `git grep -n -w -F -e name1 -e name2 …` call, output split back out by name in Python. The alias loop stays and re-greps only newly found aliases. The `os.walk` fallback stays for non-git dirs.
- `git grep` already skips ignored files and runs in parallel C. No new dependency.
- **Done when:** a scratch script builds a synthetic repo (~50k files, ~5M lines) and times `context.py` before and after. **Target: under 5s.** `tests/test_context.py` still passes, plus one new test for the git-grep path.

### 2. Run on every PR: GitHub Actions workflow

- Ship `examples/invertebrate.yml` using `anthropics/claude-code-action@v1` on `pull_request: [opened, synchronize]`. It installs the plugin through the action's `plugin_marketplaces` / `plugins` inputs, and the prompt is `invertebrate review PR #<n> --post`.
- **Auth, both supported:** `anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}` or `claude_code_oauth_token: ${{ secrets.CLAUDE_CODE_OAUTH_TOKEN }}`. The workflow passes whichever secret is set. The README shows how to create each one.
- `actions/checkout` with **`fetch-depth: 0`**. The action's docs show `fetch-depth: 1`, which would break the history tracing (`git log -L`) and the re-review ancestor check.
- **Fork PRs:** §4 asks before running a fork's code, and CI has nobody to ask. Add a SKILL.md rule: running without a person and the PR is from a fork → no `repro`/`build`, `trace`/`none` only.
- **Never `pull_request_target`**: it hands secrets to fork code. Say so in a comment in the workflow.
- Re-review already works through the `invertebrate:sha=` marker, so each push reviews only what changed.
- **Done when:** on a throwaway repo, a test PR gets a posted review with each auth method, and a second push posts a "Since last review" table.

### 3. Cost and time: profile, then cut

- Read the eval transcripts and count turns by kind: re-greps, build-command discovery, repro write/run/delete, report writing. No savings promised until that's done.
- Likely cut: move predictable, repeated work into `context.py`. Candidates are detecting the build/typecheck command and listing sibling files (same folder, same decorator or base class). That's fewer turns, not a persistent index.
- **Done when:** median cost and turns go down on the same evals, and no category's pass rate goes down. If profiling finds nothing worth cutting, record that here and stop.

### 4. Real-world evals (also the head-to-head corpus)

- 5–10 cases from real bug-fix commits in MIT-licensed OSS repos: check out the fix's parent, then apply the fix in reverse as "the PR". The ground truth is the real bug.
- **Done when:** the cases run in the current eval harness and appear in `summarize.py` output.

### 5. Ticket links

- `gh pr view --json closingIssuesReferences` pulls in the linked issue, and the existing claimed-fix check also tests the PR against what the issue asks for. One SKILL.md paragraph.
- Jira/Linear: not until someone asks.
- **Done when:** a new eval case (an issue asking for X, a PR that doesn't deliver X) is flagged, and `clean-pr-no-issues` still passes.

### 6. Dashboard (`invertebrate dashboard`)

Data first. Every posted review already carries a marker. Extend it so the dashboard can count findings without scraping the markdown:

```
<!-- invertebrate:sha=<sha> scores=1,2,4 new=P0:1,P1:2,P2:0 open=P0:1,P1:1,P2:0 fixed=2 proof=repro:2,build:0,trace:1,none:0 -->
```

Older markers have only `sha`/`scores`, so those reviews show their score and no counts.

- `scripts/dashboard.py` (stdlib): pulls PR reviews with `gh api … --paginate`, keeps the ones with a marker, parses them into rows `{pr, title, author, date, sha, score, found, proof, status}`, and writes one self-contained HTML file built the same way as `report.py`/`report.html`.
- Shows:
  - score trend over time
  - latest score per open PR
  - findings by severity per week
  - proof mix
  - fix rate: resolved ÷ (resolved + open + regressed) across re-reviews
  - a table of open P0s linking to their PRs
- SKILL.md §11: `invertebrate dashboard` runs the script and opens the file. `--since <date>` limits the range.
- Not included: cost per review (it isn't in the PR, and adding it means storing data elsewhere). A hosted/scheduled version can come later as an optional weekly job in the step 2 workflow that uploads the HTML as an Actions artifact, if wanted.
- **Done when:** `tests/test_dashboard.py` parses fixture review bodies (new marker, old marker, no marker, malformed marker) into the expected rows, and the rendered HTML has been screenshotted in light and dark mode.

## Then: head-to-head

Run Invertebrate, Greptile and CodeRabbit on the same PRs (the seeded evals plus the step 4 real-world cases) on a throwaway repo. Score all three with the same judge and graders, and publish the numbers in the README next to the with/without chart. Needs Greptile and CodeRabbit accounts on that repo.

## Not doing

- A persistent repo index or embedding store. `git grep` plus LSP covers it until step 1's benchmark says otherwise.
- Jira/Linear integrations, a hosted dashboard service.
