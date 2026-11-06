"""Self-check for skills/invertebrate/scripts/report.py. Run: python tests/test_report.py"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "skills", "invertebrate", "scripts", "report.py")
DATA = {
    "title": "Hostile </script><script>alert(1)</script> title",
    "score": 2,
    "scores": [1, 2],
    "summary": "<!-- comment opener and `code`",
    "findings": [{"n": 1, "sev": "P0", "type": "logic", "proof": "repro", "location": "a.py:1", "title": "t", "body": "b", "diff": "-x\n+y"}],
}

with tempfile.TemporaryDirectory() as d:
    src = os.path.join(d, "review.json")
    with open(src, "w", encoding="utf-8") as f:
        json.dump(DATA, f)
    out = subprocess.run([sys.executable, SCRIPT, src], capture_output=True, text=True, check=True).stdout.strip()
    assert out == os.path.join(d, "review.html"), out
    with open(out, encoding="utf-8") as f:
        html = f.read()

assert "__REVIEW_DATA__" not in html, "placeholder left in output"
assert "http" not in html.replace("http://www.w3.org/2000/svg", ""), "report must not load anything from the network"
start = html.index('id="review-data">') + len('id="review-data">')
block = html[start:html.index("</script>", start)]
assert json.loads(block) == DATA, "data block truncated or altered: " + block[:200]
assert "<!--" not in block, block[:200]

# Diagram layout (pure JS between the layout markers), run under node when it's installed.
LAYOUT_CHECK = """
const vm = require('vm');
const ctx = {};
vm.runInNewContext(require('fs').readFileSync(0, 'utf8') + ';this.graphLayers = graphLayers; this.graphRows = graphRows; this.graphChains = graphChains;', ctx);
const assert = require('assert');
const E = (from, to) => ({ from, to });
// Cycle A->B->C->A: C->A is the back edge and must not push A down.
let edges = [E('A', 'B'), E('B', 'C'), E('C', 'A')];
let { layer, back } = ctx.graphLayers(['A', 'B', 'C'], edges);
assert.deepStrictEqual([...layer.values()], [0, 1, 2]);
assert.deepStrictEqual([...back], [2]);
// The back edge C->A gets a waypoint in B's row and its chain still runs C -> A.
let chained = ctx.graphChains(edges, layer, back);
assert.strictEqual(JSON.stringify(chained.chains[2]), '["C","~2.1","A"]');
assert.strictEqual(layer.get('~2.1'), 1);
assert.ok(chained.segments.every(s => layer.get(s.to) === layer.get(s.from) + 1), 'every segment spans one row');
// Longest path: A->C directly and A->B->C puts C below B; A->C gets a waypoint beside B.
edges = [E('A', 'C'), E('A', 'B'), E('B', 'C')];
({ layer, back } = ctx.graphLayers(['A', 'B', 'C'], edges));
assert.strictEqual(layer.get('C'), 2);
chained = ctx.graphChains(edges, layer, back);
assert.strictEqual(JSON.stringify(ctx.graphRows(['A', 'B', 'C', ...chained.waypoints], chained.segments, layer)), '[["A"],["B","~0.1"],["C"]]');
// Barycenter: children are reordered under their parents (P2's child listed first).
edges = [E('P1', 'K1'), E('P2', 'K2')];
({ layer, back } = ctx.graphLayers(['P1', 'P2', 'K2', 'K1'], edges));
chained = ctx.graphChains(edges, layer, back);
assert.strictEqual(JSON.stringify(ctx.graphRows(['P1', 'P2', 'K2', 'K1'], chained.segments, layer)), '[["P1","P2"],["K1","K2"]]');
"""
node = shutil.which("node")
if node:
    template = open(os.path.join(os.path.dirname(SCRIPT), "report.html"), encoding="utf-8").read()
    layout = template.split("// layout:start")[1].split("// layout:end")[0]
    with tempfile.TemporaryDirectory() as d:
        check = os.path.join(d, "check.js")
        with open(check, "w", encoding="utf-8") as f:
            f.write(LAYOUT_CHECK)
        subprocess.run([node, check], input=layout, text=True, check=True)
else:
    print("node not found: skipped diagram layout check")
print("ok")
