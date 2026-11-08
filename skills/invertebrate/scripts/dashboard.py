#!/usr/bin/env python3
"""Team dashboard from the Invertebrate reviews posted on a repo's PRs (stdlib + `gh`).

usage: dashboard.py [--repo OWNER/NAME] [--since YYYY-MM-DD] [--limit N] [--from-json FILE] [OUT.html]
  --repo       default: the current directory's GitHub repo
  --limit      most recently updated PRs to read (default 100)
  --from-json  read PRs from a file shaped like the GraphQL nodes below, instead of calling gh
Prints the absolute path of the written HTML file.
"""
import datetime as dt
import html
import json
import os
import re
import statistics
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
MARKER = re.compile(r"<!--\s*invertebrate:sha=([0-9a-f]+)(.*?)-->", re.S)
OLD_SCORE = re.compile(r"Confidence Score:\D{0,16}(\d)/5")
SEVS = ("P0", "P1", "P2")
PROOFS = (("repro", "Proven by test"), ("build", "Proven by build"), ("trace", "Found by search"), ("none", "Unproven"))
SEV_LABEL = {"P0": ("🔴 P0 Critical", "crit"), "P1": ("🟠 P1 High", "high"), "P2": ("🟡 P2 Medium", "med")}
QUERY = """query($owner:String!,$name:String!,$n:Int!){repository(owner:$owner,name:$name){
pullRequests(last:$n,orderBy:{field:UPDATED_AT,direction:ASC}){nodes{
number title url state author{login} reviews(last:50){nodes{body submittedAt}}}}}}"""


def counts(text):
    """'P0:1,P1:2' -> {'P0': 1, 'P1': 2}; malformed parts are skipped."""
    out = {}
    for part in text.split(","):
        k, _, v = part.partition(":")
        if v.isdigit():
            out[k] = int(v)
    return out


def parse(body):
    """Review body -> marker fields, or None if it isn't an Invertebrate review."""
    m = MARKER.search(body or "")
    if not m:
        return None
    fields = dict(f.split("=", 1) for f in m[2].split() if "=" in f)
    scores = [int(s) for s in fields.get("scores", "").split(",") if s.isdigit()]
    old = OLD_SCORE.search(body)
    score = scores[-1] if scores else int(old[1]) if old else None
    fixed = fields.get("fixed", "")
    return {"sha": m[1], "score": score, "new": counts(fields.get("new", "")), "open": counts(fields.get("open", "")),
            "proof": counts(fields.get("proof", "")), "fixed": int(fixed) if fixed.isdigit() else None,
            "has_counts": "new" in fields}


def fetch(repo, limit):
    if not repo:
        repo = subprocess.run(["gh", "repo", "view", "--json", "nameWithOwner", "-q", ".nameWithOwner"],
                              capture_output=True, text=True, check=True).stdout.strip()
    owner, name = repo.split("/")
    out = subprocess.run(["gh", "api", "graphql", "-f", f"query={QUERY}", "-F", f"owner={owner}", "-F", f"name={name}",
                          "-F", f"n={limit}"], capture_output=True, text=True, encoding="utf-8", check=True).stdout
    # ponytail: one page of PRs (GitHub caps it at 100); paginate with pageInfo if teams need more history.
    return repo, json.loads(out)["data"]["repository"]["pullRequests"]["nodes"]


def review_rows(prs, since=None):
    rows = []
    for pr in prs:
        for rv in pr.get("reviews", {}).get("nodes", []):
            fields = parse(rv.get("body"))
            if not fields or (since and rv["submittedAt"][:10] < since):
                continue
            rows.append({"pr": pr["number"], "title": pr["title"], "url": pr["url"], "state": pr["state"],
                         "author": (pr.get("author") or {}).get("login", "?"), "date": rv["submittedAt"], **fields})
    return sorted(rows, key=lambda r: r["date"])


def week(date):
    d = dt.date.fromisoformat(date[:10])
    return (d - dt.timedelta(days=d.weekday())).isoformat()


def summarize(rows):
    latest = {}
    for r in rows:
        latest[r["pr"]] = r  # rows are date-sorted: the last one per PR wins
    counted = [r for r in rows if r["has_counts"]]
    new_total = sum(sum(r["new"].get(s, 0) for s in SEVS) for r in counted)
    fixed_total = sum(r["fixed"] or 0 for r in counted)
    weeks = {}
    for r in rows:
        w = weeks.setdefault(week(r["date"]), {"scores": [], **{s: 0 for s in SEVS}})
        if r["score"] is not None:
            w["scores"].append(r["score"])
        for s in SEVS:
            w[s] += r["new"].get(s, 0)
    open_prs = [r for r in latest.values() if r["state"] == "OPEN"]
    merged_p0 = [r for r in latest.values() if r["state"] == "MERGED" and r["open"].get("P0", 0) > 0]
    scores = [r["score"] for r in latest.values() if r["score"] is not None]
    return {
        "reviews": len(rows), "prs": len(latest),
        "median_score": statistics.median(scores) if scores else None,
        "fix_rate": fixed_total / new_total if new_total else None, "fixed": fixed_total, "found": new_total,
        "weeks": dict(sorted(weeks.items())),
        "proof": {k: sum(r["proof"].get(k, 0) for r in counted) for k, _ in PROOFS},
        "open_prs": sorted(open_prs, key=lambda r: (-r["open"].get("P0", 0), r["score"] if r["score"] is not None else 9)),
        "merged_p0": merged_p0,
        "old_only": len(counted) < len(rows),
    }


def esc(x):
    return html.escape(str(x))


def tone(score):
    return "none" if score is None else "ok" if score >= 4 else "med" if score == 3 else "high" if score == 2 else "crit"


def tile(label, value, note=""):
    return f'<div class="tile"><p class="eyebrow">{esc(label)}</p><p class="big">{esc(value)}</p><p class="muted">{esc(note)}</p></div>'


def score_chart(weeks):
    pts = [(w, statistics.mean(v["scores"])) for w, v in weeks.items() if v["scores"]]
    if not pts:
        return '<p class="muted">No scores yet.</p>'
    W, H, pad = 640, 180, 28
    step = (W - 2 * pad) / max(len(pts) - 1, 1)
    xy = [(pad + i * step, H - pad - s / 5 * (H - 2 * pad)) for i, (_, s) in enumerate(pts)]
    grid = "".join(f'<line class="grid" x1="{pad}" x2="{W - pad}" y1="{H - pad - g / 5 * (H - 2 * pad):.1f}" y2="{H - pad - g / 5 * (H - 2 * pad):.1f}"/>'
                   f'<text class="axis" x="{pad - 8}" y="{H - pad - g / 5 * (H - 2 * pad) + 4:.1f}">{g}</text>' for g in (0, 1, 2, 3, 4, 5))
    line = f'<polyline class="line" points="{" ".join(f"{x:.1f},{y:.1f}" for x, y in xy)}"/>'
    dots = "".join(f'<g class="hit"><circle r="12" cx="{x:.1f}" cy="{y:.1f}" class="halo-hit"/><circle r="5" cx="{x:.1f}" cy="{y:.1f}" class="dot"/>'
                   f'<title>Week of {esc(w)}: average score {s:.1f}/5</title></g>' for (x, y), (w, s) in zip(xy, pts))
    ends = f'<text class="axis start" x="{pad}" y="{H - 6}">{esc(pts[0][0])}</text><text class="axis end" x="{W - pad}" y="{H - 6}">{esc(pts[-1][0])}</text>'
    return f'<div class="scroll"><svg class="chart" viewBox="0 0 {W} {H}" role="img" aria-label="Average confidence score per week">{grid}{line}{dots}{ends}</svg></div>'


def findings_rows(weeks):
    peak = max([v[s] for v in weeks.values() for s in SEVS] + [1])
    out = []
    for s in SEVS:
        label, t = SEV_LABEL[s]
        bars = "".join(f'<span class="col" style="--h:{v[s] / peak * 100:.0f}%" title="Week of {esc(w)}: {v[s]} new {s}"><i></i></span>'
                       for w, v in weeks.items())
        out.append(f'<div class="sm" style="--c:var(--{t})"><span class="sm-label">{label}</span><span class="cols">{bars}</span>'
                   f'<span class="n">{sum(v[s] for v in weeks.values())}</span></div>')
    return "".join(out)


def proof_bars(proof):
    peak = max(list(proof.values()) + [1])
    return "".join(f'<div class="bar-row"><span>{esc(label)}</span><span class="bar-track"><span class="bar-fill" style="width:{proof[k] / peak * 100:.0f}%"></span></span>'
                   f'<span class="bar-n">{proof[k]}</span></div>' for k, label in PROOFS)


def pr_table(rows, empty):
    if not rows:
        return f'<p class="none">{esc(empty)}</p>'
    body = "".join(
        f'<tr><td><a href="{esc(r["url"])}">#{r["pr"]}</a></td><td>{esc(r["title"])}</td><td>{esc(r["author"])}</td>'
        f'<td><span class="chip" style="--c:var(--{tone(r["score"])});--cb:var(--{tone(r["score"])}-bg)">{"?" if r["score"] is None else r["score"]}/5</span></td>'
        + "".join(f'<td class="n">{r["open"].get(s, "–") if r["has_counts"] else "–"}</td>' for s in SEVS) + "</tr>"
        for r in rows)
    return ('<div class="scroll"><table><thead><tr><th>PR</th><th>Title</th><th>Author</th><th>Score</th>'
            '<th>Open P0</th><th>Open P1</th><th>Open P2</th></tr></thead><tbody>' + body + "</tbody></table></div>")


def render(repo, s):
    with open(os.path.join(HERE, "report.html"), encoding="utf-8") as f:
        style = re.search(r"<style>.*?</style>", f.read(), re.S)[0]  # same palette and type as the review report
    with open(os.path.join(HERE, "dashboard.css"), encoding="utf-8") as f:
        style += "<style>" + f.read() + "</style>"
    if not s["reviews"]:
        content = f'<h1>{esc(repo)}</h1><p>No Invertebrate reviews found on these PRs. Post one with <code>invertebrate review PR #n and post it</code>.</p>'
    else:
        rate = "–" if s["fix_rate"] is None else f'{s["fix_rate"]:.0%}'
        med = "–" if s["median_score"] is None else f'{s["median_score"]:g}/5'
        content = (
            f'<p class="eyebrow">Invertebrate dashboard</p><h1>{esc(repo)}</h1>'
            '<div class="tiles">'
            + tile("PRs reviewed", s["prs"], f'{s["reviews"]} reviews')
            + tile("Median latest score", med, "per PR, out of 5")
            + tile("Fix rate", rate, f'{s["fixed"]} of {s["found"]} findings fixed on a later push')
            + tile("Merged with a P0 open", len(s["merged_p0"]), "PRs merged while a critical finding was open")
            + "</div>"
            + "<section><h2>Open PRs, worst first</h2>" + pr_table(s["open_prs"], "No open reviewed PRs.") + "</section>"
            + "<section><h2>Confidence score, weekly average</h2>" + score_chart(s["weeks"]) + "</section>"
            + "<section><h2>New findings per week</h2>" + findings_rows(s["weeks"]) + "</section>"
            + "<section><h2>How findings were proven</h2><div class=\"bars\">" + proof_bars(s["proof"]) + "</div></section>"
            + ("<section><h2>Merged with a P0 open</h2>" + pr_table(s["merged_p0"], "") + "</section>" if s["merged_p0"] else "")
            + ('<p class="muted">Some reviews come from Invertebrate before 1.5 and only carry a score, so counts leave them out.</p>' if s["old_only"] else "")
        )
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">'
            f'<title>Invertebrate Dashboard</title>{style}</head><body><main>{content}<footer>Generated {stamp} from PR review markers.</footer></main></body></html>')


def main(argv):
    opt, out = {"--repo": None, "--since": None, "--limit": "100", "--from-json": None}, None
    while argv:
        a = argv.pop(0)
        if a in opt:
            opt[a] = argv.pop(0)
        else:
            out = a
    repo, since, limit, src = opt["--repo"], opt["--since"], int(opt["--limit"]), opt["--from-json"]
    if src:
        with open(src, encoding="utf-8") as f:
            prs = json.load(f)
        repo = repo or "local"
    else:
        repo, prs = fetch(repo, limit)
    out = out or os.path.join(tempfile.gettempdir(), f"invertebrate-dashboard-{repo.replace('/', '-')}.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(render(repo, summarize(review_rows(prs, since))))
    print(os.path.abspath(out))


if __name__ == "__main__":
    main(sys.argv[1:])
