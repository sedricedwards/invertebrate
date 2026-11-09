# Install

Invertebrate is one skill folder, [`skills/invertebrate/`](skills/invertebrate/): `SKILL.md` alone, no scripts. Every agent below loads that same folder. It runs only when your message contains the word "invertebrate".

**Tested** means a review was run in that agent and checked. **Install checked** means the agent accepted the manifest and found the skill, but no review was run. **Untested** means the manifest follows the agent's documented format but has not been tried. Tell me (open an issue) if one fails.

| Agent | Status |
|---|---|
| Claude Code | Tested (the benchmark suite, see [Numbers](README.md#numbers)) |
| Antigravity CLI 1.4.5 | Install checked (`agy plugin validate --strict` and `agy plugin install`) |
| Everything else | Untested |

## What you need

- `git`, for every target except a `.diff` file
- `gh` (the GitHub CLI, signed in), for PR targets, posting, and learn mode

## Claude Code

```bash
claude plugin install invertebrate --marketplace sedricedwards/invertebrate
```

## Codex

```bash
codex plugin marketplace add sedricedwards/invertebrate
codex plugin add invertebrate@sedricedwards
```

Start a new thread. Say "invertebrate review my uncommitted changes", or call the skill directly with `$invertebrate:invertebrate`.

## GitHub Copilot CLI

```bash
copilot plugin marketplace add sedricedwards/invertebrate
copilot plugin install invertebrate@sedricedwards
```

## Gemini CLI

```bash
gemini extensions install https://github.com/sedricedwards/invertebrate
```

Gemini loads the skill from the extension's `skills/` folder.

**Qwen Code** installs the same extension: `qwen extensions install sedricedwards/invertebrate:invertebrate`.

## Antigravity CLI

```bash
agy plugin install https://github.com/sedricedwards/invertebrate
```

## Devin CLI

```bash
devin plugins install sedricedwards/invertebrate
```

## Grok Build

```bash
grok plugin install sedricedwards/invertebrate --trust
```

Plugins start disabled. To turn it on, open `/plugins` and press Space on `invertebrate`, then start a new session.

## Goose

```bash
goose plugin install https://github.com/sedricedwards/invertebrate.git
```

## Kimi Code

Inside Kimi Code, run `/plugins install https://github.com/sedricedwards/invertebrate`, then `/reload`.

## Qoder

Clone the repo, then point `qodercli plugins install` at the clone's folder. The manifest is [`.qoder-plugin/plugin.json`](.qoder-plugin/plugin.json).

## pi and Oh My Pi

pi: copy `skills/invertebrate/` into its skills folder (see the last section below).

Oh My Pi:

```bash
omp plugin marketplace add sedricedwards/invertebrate
omp plugin install invertebrate@sedricedwards
```

## OpenCode, Cursor, Cline, Windsurf, Factory Droid, and other skill-capable agents

Copy `skills/invertebrate/` (the whole folder) into your agent's skills folder. For example, that's `.opencode/skills/` for OpenCode, `~/.factory/skills/` for Factory Droid, `~/.openclaw/skills/` for OpenClaw, and `~/.agents/skills/` for agents that read that shared folder.

## Agents with only a rules file

This covers Copilot Chat in an editor, Aider, Zed, Jules, Amp, JetBrains Junie, and Kiro. Clone this repo somewhere permanent, then add this line to your project's `AGENTS.md` (or the agent's own rules file). Replace the path with the path to your clone:

```text
When my message contains the word "invertebrate", read /path/to/invertebrate/skills/invertebrate/SKILL.md and follow it exactly.
```

## What differs outside Claude Code

- **References:** Claude Code has an `LSP` tool that follows aliased imports precisely. Elsewhere the skill uses a batched `git grep` and follows `x as y` aliases by hand, so it can miss references that only a language server would find.
- **Triggering:** the skill is meant to load only on the word "invertebrate". Agents that match skills loosely may load it for other review requests. If that happens, call the skill by name.
- **Proof runs:** proving a finding means running a test. The agent needs permission to run shell commands, or every finding is marked Unproven.

## Uninstall

| Agent | Command |
|---|---|
| Claude Code | `claude plugin uninstall invertebrate` |
| Codex | `codex plugin remove invertebrate` |
| Gemini CLI | `gemini extensions uninstall invertebrate` |
| Antigravity CLI | `agy plugin uninstall invertebrate` |
| Devin CLI | `devin plugins remove invertebrate` |
| Grok Build | `grok plugin uninstall invertebrate` |
| Copied folder or rules line | Delete it |
