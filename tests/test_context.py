"""Self-check for skills/invertebrate/scripts/context.py. Run: python tests/test_context.py"""
import os
import subprocess
import sys
import tempfile

SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "skills", "invertebrate", "scripts", "context.py")
FILES = {
    "src/money.ts": "export function format(cents: number, currency: string): string {\n  return String(cents) + currency;\n}\n",
    "src/index.ts": 'export { format as formatMoney } from "./money";\n',
    "src/invoice.ts": 'import { formatMoney } from "./index";\nexport const due = (c: number) => formatMoney(c);\n',
    "src/dates.ts": "export function format(d: Date): string {\n  return d.toISOString();\n}\n",
    "src/view.ts": 'import { format } from "./dates";\nexport const v = (d: Date) => format(d);\n',
}
DIFF = """diff --git a/src/money.ts b/src/money.ts
--- a/src/money.ts
+++ b/src/money.ts
@@ -1,3 +1,3 @@
-export function format(cents: number): string {
-  return String(cents);
+export function format(cents: number, currency: string): string {
+  return String(cents) + currency;
 }
"""


def git(*args):
    subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", *args], check=True, capture_output=True)


with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as d:  # cwd is inside d on Windows
    os.chdir(d)
    git("init", "-q")
    os.makedirs("src")
    with open("src/money.ts", "w") as f:
        f.write("export function format(cents: number): string {\n  return String(cents);\n}\n")
    git("add", "-A")
    git("commit", "-qm", "Fix currency rounding (#7)")
    for path, text in FILES.items():
        with open(path, "w") as f:
            f.write(text)
    with open("pr.diff", "w") as f:
        f.write(DIFF)
    out = subprocess.run([sys.executable, SCRIPT, "--diff", "pr.diff"], capture_output=True, text=True, check=True).stdout

    assert "format: removed def src/money.ts:1; added def src/money.ts:1" in out, out
    assert "src/invoice.ts:2:" in out, "alias through barrel file not followed\n" + out  # format -> formatMoney -> invoice
    assert "src/view.ts:" not in out.split("same name")[0], "same-name dates.format leaked into money refs\n" + out
    assert "same name, never mention a changed module (2 files): src/dates.ts, src/view.ts" in out, out
    assert "Fix currency rounding (#7)  FIX?" in out, out
    assert "pr.diff" not in out, out
print("ok")
