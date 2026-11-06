# Invertebrate

A [Claude Code](https://claude.com/claude-code) skill for AI code review in the style of [Greptile](https://www.greptile.com). Before judging a change, it traces every changed function, type, and route through the **whole repository**. That catches bugs that reading the diff alone misses: a rename that leaves callers broken, a unit change (cents → dollars) that some callers never picked up, a new endpoint missing the auth check that its sibling endpoints all have, or a "cleanup" that deletes a line an earlier commit added to fix a bug.

Because it runs locally, it can also **prove** what it finds. Each serious finding comes with a test that fails on the PR's code, or a compiler error. A finding it can't reproduce is dropped. When you ask it to fix a finding, it reruns that test to confirm the fix.

Not affiliated with or endorsed by Greptile.

## Install

In your terminal (Claude Code 2.1.275 or later):

```bash
claude plugin install invertebrate --marketplace sedricedwards/invertebrate
```

Or inside a Claude Code session:

```
/plugin install invertebrate --marketplace sedricedwards/invertebrate
```

To update later: `claude plugin update invertebrate`. To remove: `claude plugin uninstall invertebrate`.

## Use

The skill runs **only** when your message contains the word "invertebrate":

```
invertebrate review PR #12
run invertebrate on my branch
invertebrate review my uncommitted changes
invertebrate review PR #12 and post it
invertebrate re-review PR #12
invertebrate learn
```

Accepted targets are a PR number or URL (needs the `gh` CLI), a branch (compared against main/master), the working tree, or a `.diff`/`.patch` file.

## Output

Everything is color-coded and labeled in plain words, so people who don't write code can read it too.

- **Verdict**: "Safe to merge? Yes / After small fixes / Not yet / No", plus one sentence on the biggest problem
- **Summary**: what the change does and its main risk, in plain language
- **Confidence score**: 0–5 with a traffic-light color and meter, e.g. `🟡 3/5 ●●●○○` (🟢 5–4 = merge, 🟡 3 = fix first, 🟠 2 = rework, 🔴 0–1 = rethink)
- **Findings table**: each finding's severity (🔴 P0 Critical / 🟠 P1 High / 🟡 P2 Medium), type (Bug / Won't compile / Cleanup), proof, and location
  - Proof is one of: Proven by test (a test it wrote and ran failed), Proven by build (compiler/typecheck error), Found by search (for example a surviving reference to a removed symbol), or Unproven
  - Unproven P0/P1 findings are demoted one level
- **Diagram**: mermaid sequence, ER, class, or flow diagram, chosen to fit the change; skipped for trivial diffs. It's drawn as a picture on GitHub and in the visual report; in the terminal you see its source
- **Inline comments**: the concrete failure scenario, a suggested-fix diff, and the repro test so you can run it yourself
- **Since last review** (re-reviews only): each earlier finding marked ✅ resolved / ⚠️ open / 🔴 regressed, and the score across reviews (e.g. `1/5 → 2/5 → 4/5`). Only new findings get new comments

### Visual report

After a review, say `html` and Invertebrate writes a self-contained HTML page to your temp folder and opens it: the colored verdict, a bar chart of findings by severity, a chart of the score across reviews, the diagram drawn as a picture, and one color-coded card per finding. It needs Python. The page is one small file (about 25 KB) that works offline and loads nothing from the internet; the charts and diagram are drawn by code built into the page.

### Proving findings

Invertebrate runs the project's build/typecheck if the tool is already installed, and runs a short repro test for each candidate bug, then deletes those tests. It never installs dependencies or uses the network for this. For a PR it uses a separate git worktree and leaves your checkout alone. It asks first if the PR was opened by someone else, because running it runs their code.

### Re-reviews

Each review ends with a hidden `<!-- invertebrate:sha=... -->` marker. On the next run against the same PR (or a saved review you point to), Invertebrate reviews only the commits since then and rechecks the earlier findings. After a force-push it falls back to a full review.

### Learn mode

`invertebrate learn` reads review comments on your last 30 merged PRs. It proposes rules for concerns the team accepted at least twice, and "don't flag" instructions for ones the team rejected at least twice. Each proposal links its PRs as evidence. Nothing is written until you say `save them`; then the rules go into `.invertebrate/`.

Posting to GitHub happens only when you ask (`post it`, `--post`). The review is posted as a single `COMMENT` review and never approves or requests changes.

## Configuration

You can add an optional `.invertebrate/` folder to your repo, at the root or in any subdirectory. Invertebrate only reads it; the one exception is learn mode, and only after you say `save them`. Settings in a subfolder's `.invertebrate/` apply to changes in that part of the repo.

Already using Greptile? Invertebrate reads your existing `.greptile/` folder as is, since the format is the same. If a directory has both folders, `.invertebrate/` wins.

| File | Purpose |
|---|---|
| `config.json` | `strictness` 1–3, `commentTypes`, `ignorePatterns`, `instructions`, scoped `rules` with severity |
| `rules.md` | Plain-English team rules |
| `files.json` | Extra files to read as context |

Example `.invertebrate/config.json`:

```json
{
  "strictness": 2,
  "rules": [
    { "id": "audit-mutations", "rule": "Every endpoint that changes data must call audit_log().", "scope": ["app/**/*.py"], "severity": "high" }
  ]
}
```

If there's no config folder at all, it uses `CLAUDE.md` / `AGENTS.md` / `CONTRIBUTING.md` as the rules.

## Tests

`evals/` contains 11 seeded-bug sample projects: a cross-file rename, a semantic unit change, a missing auth check under strictness 3, an async race, a PR that claims a security fix it doesn't deliver, a clean PR that should get no findings, and a repo with both `.invertebrate/` and `.greptile/` to check that `.invertebrate/` wins. Four more cover the newer features:

- `repro-then-fix`: the bug must be proven with a test that was actually run, a decoy the caller already handles must not be reported, and the fix must be confirmed by rerunning the repro
- `reverted-fix`: the PR deletes a guard that a commit titled "Fix double charge…" added, and the review must cite that commit
- `alias-reexport-distractors`: the broken callers are reachable only through `import { x as y }` and a re-export, among 30 unrelated callers of a function with the same name
- `incremental-rereview`: a second review of a branch must mark the old finding resolved and report only the new bug

Learn mode has no case, because it needs a live GitHub repository. To run them:

```bash
git clone https://github.com/sedricedwards/invertebrate && cd invertebrate
claude plugin eval . --allow-tools Write,Edit,Bash --scaffold
```

These are real, billed model runs.

In our runs (3 per case, each with and without the skill), both configurations found every planted bug. What the skill added was a consistent report format and correct handling of config strictness. Its known weakness: at default strictness it tends to drop small but useful remarks, such as a test that doesn't actually exercise the change.

## Not included

- Learning live from 👍/👎 reactions (learn mode proposes rules from past PRs instead)
- Automatic review of every PR (it runs on request only)

## Privacy and external services

Invertebrate declares no connectors. It contacts one outside service, **GitHub**, through the GitHub CLI (`gh`), signed in as you:

| When | What is sent to GitHub |
|---|---|
| You give a PR number or URL | Requests for that PR's title, description, file list and diff (read only) |
| You explicitly ask to post the review | The review text and inline comments, posted to that PR as a `COMMENT` review |
| You re-review a PR | A request for that PR's earlier reviews (read only) |
| You run `invertebrate learn` | Requests for your recent merged PRs and their review comments (read only) |

It contacts no other service, and it collects and stores nothing. See the [Privacy Policy](PRIVACY.md).

## License

MIT
