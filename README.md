# Invertebrate

A [Claude Code](https://claude.com/claude-code) skill for AI code review in the style of [Greptile](https://www.greptile.com). Before judging a change, it traces every changed function, type, and route through the **whole repository**. That catches bugs that reading the diff alone misses: a rename that leaves callers broken, a unit change (cents → dollars) that some callers never picked up, or a new endpoint missing the auth check that its sibling endpoints all have.

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
```

Accepted targets are a PR number or URL (needs the `gh` CLI), a branch (compared against main/master), the working tree, or a `.diff`/`.patch` file.

## Output

- **Summary**: what the change does and its main risk, in plain language
- **Confidence score**: 0–5 (5 = merge, 3 = fix first, 0–1 = rethink)
- **Findings table**: each finding's severity (P0 critical / P1 high / P2 medium), type (logic / syntax / style), and location
- **Diagram**: mermaid sequence, ER, class, or flow diagram, chosen to fit the change; skipped for trivial diffs
- **Inline comments**: the concrete failure scenario plus a suggested-fix diff

Posting to GitHub happens only when you ask (`post it`, `--post`). The review is posted as a single `COMMENT` review and never approves or requests changes.

## Configuration

You can add an optional `.invertebrate/` folder to your repo, at the root or in any subdirectory. Invertebrate only reads it and never creates or changes it. Settings in a subfolder's `.invertebrate/` apply to changes in that part of the repo.

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

`evals/` contains 6 seeded-bug sample projects: a cross-file rename, a semantic unit change, a missing auth check under strictness 3, an async race, a PR that claims a security fix it doesn't deliver, and a clean PR that should get no findings. To run them:

```bash
git clone https://github.com/sedricedwards/invertebrate && cd invertebrate
claude plugin eval . --allow-tools Write,Edit,Bash --scaffold
```

These are real, billed model runs.

In our runs (3 per case, each with and without the skill), both configurations found every planted bug. What the skill added was a consistent report format and correct handling of config strictness. Its known weakness: at default strictness it tends to drop small but useful remarks, such as a test that doesn't actually exercise the change.

## Not included

- Learning from 👍/👎 reactions
- Automatic review of every PR (it runs on request only)

## License

MIT
