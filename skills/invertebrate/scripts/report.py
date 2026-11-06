"""Render an Invertebrate review (JSON) into a self-contained HTML report.

Usage: report.py review.json [out.html]   (default out: review.html next to the JSON)
Prints the absolute path of the written file.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(HERE, "report.html")


def render(data):
    with open(TEMPLATE, encoding="utf-8") as f:
        template = f.read()
    # "<" escaped so review text like "</script>" can't break out of the data block.
    payload = json.dumps(data, ensure_ascii=False).replace("<", "\\u003c")
    return template.replace("__REVIEW_DATA__", payload, 1)


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    src = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else os.path.splitext(src)[0] + ".html"
    with open(src, encoding="utf-8") as f:
        data = json.load(f)
    with open(out, "w", encoding="utf-8") as f:
        f.write(render(data))
    print(os.path.abspath(out))


if __name__ == "__main__":
    main()
