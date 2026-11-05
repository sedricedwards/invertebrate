#!/usr/bin/env python3
"""One-call context graph for an Invertebrate review (stdlib only).

usage: context.py [--diff FILE] [--base REV] [git-diff args...]
  --diff FILE   read the diff from FILE (else runs `git diff <args>`, default HEAD)
  --base REV    revision whose history explains removed lines (default HEAD)

Prints: changed files, changed symbols, every whole-word reference to them
(following `x as y` aliases), and the commits that last touched removed lines.
"""
import os
import re
import subprocess
import sys

DEF = re.compile(
    r"^(?P<ind>\s*)(?:export\s+)?(?:default\s+)?(?:pub(?:\([^)]*\))?\s+)?(?:async\s+)?"
    r"(?P<kw>def|class|function\*?|fn|func(?:\s*\([^)]*\))?|interface|type|struct|enum|trait|const|let|var)"
    r"\s+(?P<name>[A-Za-z_]\w*)"
)
CONST_ASSIGN = re.compile(r"^(?P<name>[A-Z_][A-Z0-9_]{2,})\s*[:=]")
FIX_WORDS = re.compile(r"\b(fix|bug|race|cve|revert|security|hotfix|#\d+)", re.I)
SKIP_DIRS = {".git", "node_modules", "dist", "build", "target", "__pycache__", ".venv", "venv"}
MAX_REFS = 25


def run(args):
    r = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return r.stdout if r.returncode == 0 else ""


def def_name(line, top_level_only_for_vars=True):
    m = DEF.match(line)
    if m:
        local_var = m["kw"] in ("const", "let", "var") and m["ind"]
        return None if local_var and top_level_only_for_vars else m["name"]
    m = CONST_ASSIGN.match(line)
    return m["name"] if m else None


def parse_diff(text):
    """-> list of {path, old_path, hunks:[{old_start, new_start, lines:[(tag, old_no, new_no, text)]}]}"""
    files, cur, hunk = [], None, None
    old_no = new_no = 0
    for line in text.splitlines():
        if line.startswith("diff --git"):
            cur = None
            continue
        if line.startswith("--- "):
            cur = {"old_path": line[4:].split("\t")[0].removeprefix("a/"), "path": None, "hunks": []}
            files.append(cur)
            continue
        if line.startswith("+++ ") and cur is not None:
            cur["path"] = line[4:].split("\t")[0].removeprefix("b/")
            continue
        m = re.match(r"@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@", line)
        if m and cur is not None:
            old_no, new_no = int(m[1]), int(m[2])
            hunk = {"old_start": old_no, "new_start": new_no, "lines": []}
            cur["hunks"].append(hunk)
            continue
        if hunk is None or not line or line[0] not in "+- ":
            continue
        tag = line[0]
        hunk["lines"].append((tag, old_no, new_no, line[1:]))
        old_no += tag != "+"
        new_no += tag != "-"
    return files


def read_lines(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            return f.read().splitlines()
    except OSError:
        return []


def enclosing_def(lines, line_no):
    """Nearest definition at or above line_no (1-based) in the post-change file."""
    for i in range(min(line_no, len(lines)) - 1, -1, -1):
        name = def_name(lines[i])
        if name:
            return name
    return None


def changed_symbols(files):
    """-> {name: [reason, ...]}"""
    syms = {}
    for f in files:
        path = f["path"] if f["path"] != "/dev/null" else f["old_path"]
        post = read_lines(path) if f["path"] != "/dev/null" else []
        for h in f["hunks"]:
            for tag, old_no, new_no, text in h["lines"]:
                name = def_name(text) if tag != " " else None
                if name:
                    where = f"{path}:{new_no if tag == '+' else old_no}"
                    syms.setdefault(name, []).append(f"{'added' if tag == '+' else 'removed'} def {where}")
            for new_no in sorted({n for t, _, n, text in h["lines"] if t != " " and text.strip()}):
                outer = enclosing_def(post, new_no)
                if outer:
                    syms.setdefault(outer, []).append(f"body changed in {path}")
    return syms


def repo_files(skip):
    listed = run(["git", "ls-files", "-co", "--exclude-standard"])
    if listed:
        paths = listed.splitlines()
    else:
        paths = []
        for root, dirs, names in os.walk("."):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
            paths += [os.path.relpath(os.path.join(root, n)).replace(os.sep, "/") for n in names]
    keep = []
    for p in paths:
        if p in skip or not os.path.isfile(p) or os.path.getsize(p) > 1_000_000:
            continue
        keep.append(p)
    return keep


def find_refs(names, paths):
    """Whole-word hits for each name; `name as alias` adds alias to the search. -> {name: [(path, no, text)]}"""
    contents = {p: read_lines(p) for p in paths}
    refs, queue, alias_of = {}, list(names), {}
    while queue:
        name = queue.pop(0)
        if name in refs:
            continue
        word = re.compile(rf"\b{re.escape(name)}\b")
        alias = re.compile(rf"\b{re.escape(name)}\s+as\s+([A-Za-z_]\w*)")
        refs[name] = []
        for p, lines in contents.items():
            for i, line in enumerate(lines, 1):
                if not word.search(line):
                    continue
                refs[name].append((p, i, line.strip()))
                for a in alias.findall(line):
                    if a not in refs and a not in queue:
                        alias_of[a] = name
                        queue.append(a)
    return refs, alias_of


def removed_runs(hunk):
    """Consecutive runs of removed old-line numbers -> [(start, end)]"""
    runs = []
    for tag, old_no, _, _ in hunk["lines"]:
        if tag != "-":
            continue
        if runs and runs[-1][1] == old_no - 1:
            runs[-1][1] = old_no
        else:
            runs.append([old_no, old_no])
    return runs


def history(files, base):
    out = []
    for f in files:
        if f["old_path"] == "/dev/null":
            continue
        for h in f["hunks"]:
            for start, end in removed_runs(h):
                log = run(["git", "log", "-s", "--format=%h %s", f"-L{start},{end}:{f['old_path']}", base])
                commits = [c for c in log.splitlines() if c.strip()]
                out.append((f["old_path"], start, end, commits))
    return out


def main(argv):
    diff_file, base, git_args = None, "HEAD", []
    while argv:
        a = argv.pop(0)
        if a == "--diff":
            diff_file = argv.pop(0)
        elif a == "--base":
            base = argv.pop(0)
        else:
            git_args.append(a)
    text = read_file_text(diff_file) if diff_file else run(["git", "diff", *(git_args or ["HEAD"])])
    files = parse_diff(text)
    if not files:
        print("no diff")
        return

    print("## files")
    for f in files:
        adds = sum(t == "+" for h in f["hunks"] for t, *_ in h["lines"])
        dels = sum(t == "-" for h in f["hunks"] for t, *_ in h["lines"])
        print(f"{f['path'] if f['path'] != '/dev/null' else f['old_path'] + ' (deleted)'}  +{adds} -{dels}")

    syms = changed_symbols(files)
    print("\n## changed symbols")
    for name, why in syms.items():
        print(f"{name}: {'; '.join(dict.fromkeys(why))}")

    skip = {os.path.normpath(diff_file).replace(os.sep, "/")} if diff_file else set()
    paths = repo_files(skip)
    refs, alias_of = find_refs(list(syms), paths)
    # A file that never names a changed module only shares the symbol's name: list it, don't print its lines.
    stems = {os.path.splitext(os.path.basename(f["old_path"] if f["path"] == "/dev/null" else f["path"]))[0] for f in files}
    stem_re = re.compile(r"\b(" + "|".join(map(re.escape, stems)) + r")\b")
    related = {p for p in paths if stem_re.search("\n".join(read_lines(p)))} | {f["path"] for f in files}
    print("\n## references (whole-word, `x as y` aliases followed)")
    for name, hits in refs.items():
        label = f"{name} (alias of {alias_of[name]})" if name in alias_of else name
        # An alias name is already specific to the changed symbol: show every hit.
        shown = hits if name in alias_of else [h for h in hits if h[0] in related]
        others = sorted({p for p, _, _ in hits} - {p for p, _, _ in shown})
        print(f"### {label}: {len(hits)} hits")
        for p, i, line in shown[:MAX_REFS]:
            print(f"{p}:{i}: {line[:160]}")
        if len(shown) > MAX_REFS:
            print(f"... {len(shown) - MAX_REFS} more lines")
        if others:
            print(f"same name, never mention a changed module ({len(others)} files): {', '.join(others)}")

    if not run(["git", "rev-parse", "--is-inside-work-tree"]):
        print("\n## history: not a git repo")
        return
    print(f"\n## history of removed lines (at {base}; FIX? = subject looks like a fix)")
    for path, start, end, commits in history(files, base):
        print(f"{path}:{start}-{end}")
        for c in commits or ["(no history)"]:
            print(f"  {c}{'  FIX?' if FIX_WORDS.search(c) else ''}")


def read_file_text(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        return f.read()


if __name__ == "__main__":
    main(sys.argv[1:])
