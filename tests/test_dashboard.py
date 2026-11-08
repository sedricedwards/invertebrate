"""Self-check for skills/invertebrate/scripts/dashboard.py. Run: python tests/test_dashboard.py"""
import json
import os
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "skills", "invertebrate", "scripts"))
sys.dont_write_bytecode = True  # keep __pycache__ out of the shipped skill folder
import dashboard  # noqa: E402

SCRIPT = dashboard.__file__
NEW = "<!-- invertebrate:sha=aaa111 scores=1 new=P0:1,P1:1,P2:0 open=P0:1,P1:1,P2:0 fixed=0 proof=repro:1,build:0,trace:1,none:0 -->"
RE = "<!-- invertebrate:sha=bbb222 scores=1,4 new=P0:0,P1:0,P2:1 open=P0:0,P1:0,P2:1 fixed=2 proof=repro:0,build:0,trace:0,none:1 -->"
PRS = [
    {"number": 1, "title": "<script>alert(1)</script> payments", "url": "https://github.com/o/r/pull/1", "state": "OPEN",
     "author": {"login": "ana"}, "reviews": {"nodes": [
         {"body": "## Invertebrate Review\n" + NEW, "submittedAt": "2026-11-02T10:00:00Z"},
         {"body": "LGTM from a human", "submittedAt": "2026-11-03T10:00:00Z"},  # no marker: ignored
         {"body": "## Invertebrate Review\n" + RE, "submittedAt": "2026-11-04T10:00:00Z"}]}},
    {"number": 2, "title": "old review", "url": "https://github.com/o/r/pull/2", "state": "MERGED", "author": None,
     "reviews": {"nodes": [{"body": "### Confidence Score: 🟡 3/5 ●●●○○\n<!-- invertebrate:sha=ccc333 -->",
                            "submittedAt": "2026-10-20T10:00:00Z"}]}},
    {"number": 3, "title": "shipped a hole", "url": "https://github.com/o/r/pull/3", "state": "MERGED", "author": {"login": "bo"},
     "reviews": {"nodes": [{"body": "<!-- invertebrate:sha=ddd444 scores=0 new=P0:2,P1:x open=P0:2 fixed=? -->",
                            "submittedAt": "2026-10-28T10:00:00Z"}]}},
]

rows = dashboard.review_rows(PRS)
assert [r["pr"] for r in rows] == [2, 3, 1, 1], rows
assert rows[0]["score"] == 3 and not rows[0]["has_counts"], "old marker: score from 'Confidence Score' line"
assert rows[1]["new"] == {"P0": 2} and rows[1]["fixed"] is None, "malformed parts dropped, valid ones kept"
s = dashboard.summarize(rows)
assert (s["prs"], s["reviews"]) == (3, 4), s
assert s["found"] == 1 + 1 + 1 + 2 and s["fixed"] == 2, s  # new findings across counted reviews
assert [r["pr"] for r in s["open_prs"]] == [1] and s["open_prs"][0]["score"] == 4, "open PR shows its latest review"
assert [r["pr"] for r in s["merged_p0"]] == [3], s["merged_p0"]
assert s["proof"] == {"repro": 1, "build": 0, "trace": 1, "none": 1}, s["proof"]
assert s["median_score"] == 3 and s["old_only"], s
assert list(s["weeks"]) == ["2026-10-19", "2026-10-26", "2026-11-02"], s["weeks"]
assert dashboard.review_rows(PRS, since="2026-11-01")[0]["pr"] == 1, "--since filter"

with tempfile.TemporaryDirectory() as d:
    src, out = os.path.join(d, "prs.json"), os.path.join(d, "dash.html")
    with open(src, "w", encoding="utf-8") as f:
        json.dump(PRS, f)
    printed = subprocess.run([sys.executable, SCRIPT, "--repo", "o/r", "--from-json", src, out],
                             capture_output=True, text=True, check=True).stdout.strip()
    assert os.path.samefile(printed, out), printed
    with open(out, encoding="utf-8") as f:
        page = f.read()
    assert "<script>alert" not in page and "&lt;script&gt;alert(1)" in page, "PR titles must be escaped"
    assert "Merged with a P0 open" in page and 'href="https://github.com/o/r/pull/3"' in page, "merged-with-P0 table"
    assert "40%" in page, "fix rate = 2 fixed / 5 found"
    with open(src, "w", encoding="utf-8") as f:
        json.dump([], f)
    subprocess.run([sys.executable, SCRIPT, "--from-json", src, out], check=True, capture_output=True)
    with open(out, encoding="utf-8") as f:
        assert "No Invertebrate reviews found" in f.read()
print("ok")
