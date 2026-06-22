#!/usr/bin/env python3
"""Renumber the `#` column of the README paper table sequentially (1..N).

Run after inserting/removing rows so the numbering stays consistent:

    python3 scripts/renumber.py
"""
import re
from pathlib import Path

README = Path(__file__).resolve().parent.parent / "README.md"


def main():
    lines = README.read_text(encoding="utf-8").splitlines(keepends=True)
    n = 0
    out = []
    for line in lines:
        if re.match(r"^\|\s*\d+\s*\|", line):
            n += 1
            line = re.sub(r"^\|\s*\d+\s*\|", f"| {n} |", line)
        out.append(line)
    README.write_text("".join(out), encoding="utf-8")
    print(f"Renumbered {n} rows.")


if __name__ == "__main__":
    main()
