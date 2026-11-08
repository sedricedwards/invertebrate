"""Guards on examples/invertebrate.yml that a casual edit could break. Run: python tests/test_workflow.py"""
import os

PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "examples", "invertebrate.yml")
with open(PATH, encoding="utf-8") as f:
    # drop comments (they mention pull_request_target on purpose), keep `PR #${{ ... }}`
    lines = ["" if l.lstrip().startswith("#") else l.split(" # ")[0].rstrip() for l in f]
text = "\n".join(lines)

assert "pull_request_target" not in text, "pull_request_target hands secrets to fork code"
assert "fetch-depth: 0" in text, "shallow clone breaks removed-line history and re-review ancestry"
assert "head.repo.full_name == github.repository" in text, "fork PRs must be skipped"
assert "anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}" in text, text
assert "claude_code_oauth_token: ${{ secrets.CLAUDE_CODE_OAUTH_TOKEN }}" in text, text
assert "plugins: invertebrate@sedricedwards" in text, text
assert "invertebrate review PR #" in text and "post it" in text, "prompt must contain 'invertebrate' to trigger the skill"
print("ok")
