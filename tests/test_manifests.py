"""Every agent manifest points at skills/ and carries the Claude manifest's version. Run: python tests/test_manifests.py"""
import glob
import json
import os

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
MANIFESTS = [".codex-plugin/plugin.json", ".github/plugin/plugin.json", ".devin-plugin/plugin.json",
             ".qoder-plugin/plugin.json", "gemini-extension.json", "package.json"]


def load(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as f:
        return json.load(f)


version = load(".claude-plugin/plugin.json")["version"]
for rel in MANIFESTS:
    m = load(rel)
    assert m["name"] == "invertebrate", rel
    assert m["version"] == version, f"{rel} has {m['version']}, .claude-plugin/plugin.json has {version}"
assert glob.glob(os.path.join(ROOT, "skills", "*", "SKILL.md")), "no skills/<name>/SKILL.md"
print(f"ok: {len(MANIFESTS)} manifests at {version}")
