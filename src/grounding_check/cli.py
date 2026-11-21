from __future__ import annotations

import argparse
import json
import sys

from .check import check_answer, render_markdown, split_sentences


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="rag-grounding-check")
    p.add_argument("case", help="JSON file: {\"sources\": {id: text}, \"answer\": \"...\"}")
    p.add_argument("--json", action="store_true", help="print findings as JSON")
    a = p.parse_args(argv)
    with open(a.case, encoding="utf-8") as fh:
        case = json.load(fh)
    findings = check_answer(case["answer"], case["sources"])
    if a.json:
        print(json.dumps([f.__dict__ for f in findings], indent=2, ensure_ascii=False))
    else:
        print(render_markdown(findings, len(split_sentences(case["answer"]))), end="")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
