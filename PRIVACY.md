# Privacy Policy

Effective: November 5, 2026

Invertebrate is a Claude Code plugin made up of written instructions for reviewing code. It has no servers, no analytics and no database, and its author receives no data from it.

## What it reads

When you ask for a review, Invertebrate reads, on your computer:

- the code change (a pull request, branch or diff)
- other files in your repository that the change affects
- the pull request's title and description, through the GitHub CLI (`gh`)
- on a re-review, earlier Invertebrate reviews already posted to that pull request, through `gh`
- in learn mode (`invertebrate learn`), review comments on your repository's recent merged pull requests, through `gh`
- the title and body of issues a pull request closes, through `gh`
- optional config files in `.invertebrate/` or `.greptile/`

These files may happen to contain personal data, such as names or emails in code, test data or PR descriptions. Invertebrate doesn't look for personal data and doesn't treat it any differently from other content.

## What it stores

Nothing of its own. Invertebrate keeps no memory between reviews; a re-review reads the previous review from the pull request or from a file you point to. The review appears in your Claude Code session, and is saved to a file only if you ask for one. In learn mode, proposed rules are written to `.invertebrate/` in your repository only if you say `save them`.

To prove findings, Invertebrate may run your project's existing build or typecheck and short test scripts it writes, on your computer. It deletes those scripts afterwards, never installs dependencies, and asks before running code from a pull request opened by someone else.

## What it sends

- **To GitHub:** only when you explicitly ask it to post a review. The review goes to that pull request under your own GitHub account, through `gh`.
- **To Anthropic:** Claude Code sends the conversation, including the files read during the review, to Anthropic's model to produce the review. That happens for any Claude Code task and is covered by [Anthropic's privacy policy](https://www.anthropic.com/legal/privacy), not by this plugin.

Invertebrate sends nothing anywhere else, including to its author.

## Contact

Questions: open an issue at https://github.com/sedricedwards/invertebrate/issues
