"""Turn `claude plugin eval --ablation with-without` runs into the README numbers.

Run: python evals/summarize.py [results dir]   (default: evals/results)
Prints a markdown summary and writes assets/benchmark.svg. Uses the newest
with/without run of each case, so re-running one case updates only that case.
"""
import glob
import json
import os
import statistics
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Grader number per case -> what it checks. Every grader is listed, so a new one fails loudly.
FIND, QUIET, SEV, PROOF, FORMAT = "Finds the bug", "No false alarms", "Right severity", "Proof and fix", "Report format"
CATEGORY = {
    "alias-reexport-distractors": [FIND, FIND, QUIET, QUIET, SEV],
    "async-lost-update": [FIND, FIND, FIND, FORMAT, FORMAT, PROOF],
    "claimed-fix-missing": [FIND, FIND, SEV, PROOF, FORMAT, FORMAT],
    "clean-pr-no-issues": [QUIET, FORMAT, FIND, QUIET],
    "cross-file-rename": [FIND, FIND, SEV, FORMAT, FORMAT, PROOF],
    "incremental-rereview": [FORMAT, FIND, FIND, QUIET, FORMAT],
    "invertebrate-config-wins": [SEV, FIND, QUIET, FORMAT, FORMAT],
    "repro-then-fix": [FIND, PROOF, QUIET, PROOF, PROOF, PROOF],
    "reverted-fix": [FIND, FIND, SEV, FIND, FORMAT],
    "unauthed-endpoint-strict": [FIND, FIND, QUIET, FIND, FORMAT, PROOF],
    "unit-change-callers": [FIND, FIND, SEV, FORMAT, FORMAT, PROOF],
}
ORDER = [FIND, QUIET, SEV, PROOF, FORMAT]


def latest_cases(results_dir):
    cases = {}
    for path in sorted(glob.glob(os.path.join(results_dir, "*", "aggregate-result.json"))):
        with open(path, encoding="utf-8") as f:
            run = json.load(f)
        if run["suite"].get("ablation") != "with-without":
            continue
        for case in run["cases"]:
            arms = case["arms"]
            if all(r.get("error") is None and r["turns"] > 0 for arm in ("with", "without") for r in arms.get(arm, [])):
                case["_version"] = run["suite"]["plugins"][0]["version"]
                cases[case["name"]] = case  # sorted paths: newest wins
    return cases


def tally(cases):
    """{category: {arm: [passed, total]}} plus per-arm cost/time/turn lists."""
    counts = {c: {"with": [0, 0], "without": [0, 0]} for c in ORDER}
    runs = {"with": [], "without": []}
    for name, case in cases.items():
        cats = CATEGORY[name]
        assert len(cats) == len(case["graders"]), f"{name}: update CATEGORY for its graders"
        for arm in ("with", "without"):
            for r in case["arms"][arm]:
                runs[arm].append(r)
                for i, g in enumerate(r["graders"]):
                    counts[cats[i]][arm][0] += bool(g.get("passed"))
                    counts[cats[i]][arm][1] += 1
    return counts, runs


def pct(p):
    return round(100 * p[0] / p[1]) if p[1] else 0


def svg(counts):
    bar_h, gap, label_w, width = 18, 14, 150, 640
    scale = (width - label_w - 60) / 100
    rows, y = [], 34
    for cat in ORDER:
        rows.append(f'<text x="0" y="{y + bar_h + 4}" class="l">{cat}</text>')
        for arm, cls, dy in (("with", "w", 0), ("without", "o", bar_h + 2)):
            v = pct(counts[cat][arm])
            rows.append(f'<rect x="{label_w}" y="{y + dy}" width="{max(v * scale, 1):.1f}" height="{bar_h}" class="{cls}"/>')
            rows.append(f'<text x="{label_w + v * scale + 6:.1f}" y="{y + dy + 13}" class="v">{v}%</text>')
        y += 2 * bar_h + 2 + gap
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{y + 6}" viewBox="0 0 {width} {y + 6}" font-family="ui-monospace, Menlo, Consolas, monospace" font-size="13">
<style>.l{{fill:#57606a}}.v{{fill:#24292f}}.w{{fill:#1a7f37}}.o{{fill:#afb8c1}}
@media (prefers-color-scheme: dark){{.l{{fill:#8b949e}}.v{{fill:#e6edf3}}.w{{fill:#3fb950}}.o{{fill:#484f58}}}}</style>
<rect x="{label_w}" y="6" width="12" height="12" class="w"/><text x="{label_w + 18}" y="16" class="v">with invertebrate</text>
<rect x="{label_w + 170}" y="6" width="12" height="12" class="o"/><text x="{label_w + 188}" y="16" class="v">same model, no skill</text>
{chr(10).join(rows)}
</svg>
"""


def main():
    results_dir = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "evals", "results")
    cases = latest_cases(results_dir)
    counts, runs = tally(cases)
    med = lambda arm, k: statistics.median(r[k] for r in runs[arm])
    passed = lambda arm: sum(1 for c in cases.values() if c["aggregates"]["passRate" if arm == "with" else "passRateWithout"] == 1)
    versions = sorted({c["_version"] for c in cases.values()})
    print(f"{len(cases)} cases, {len(runs['with'])} runs per arm, invertebrate {', '.join(versions)}\n")
    print("| check | with invertebrate | no skill |\n|---|--:|--:|")
    for cat in ORDER:
        w, o = counts[cat]["with"], counts[cat]["without"]
        print(f"| {cat} | {pct(w)}% ({w[0]}/{w[1]}) | {pct(o)}% ({o[0]}/{o[1]}) |")
    print(f"| Cases where every run passed every check | {passed('with')}/{len(cases)} | {passed('without')}/{len(cases)} |")
    print(f"| Median cost per review | ${med('with', 'costUsd'):.2f} | ${med('without', 'costUsd'):.2f} |")
    print(f"| Median time per review | {med('with', 'durationSeconds'):.0f}s | {med('without', 'durationSeconds'):.0f}s |")
    print(f"| Median agent turns | {med('with', 'turns'):.0f} | {med('without', 'turns'):.0f} |")
    os.makedirs(os.path.join(ROOT, "assets"), exist_ok=True)
    with open(os.path.join(ROOT, "assets", "benchmark.svg"), "w", encoding="utf-8", newline="\n") as f:
        f.write(svg(counts))


if __name__ == "__main__":
    main()
