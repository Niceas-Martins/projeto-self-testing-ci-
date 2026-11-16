import json
import sys
from pathlib import Path


def main():
    report = json.loads(Path("coverage.json").read_text(encoding="utf-8"))
    totals = report["totals"]
    lines = totals["covered_lines"] / totals["num_statements"] * 100
    branches = totals["covered_branches"] / totals["num_branches"] * 100
    print(f"Cobertura: linhas={lines:.2f}% (meta 85%), branches={branches:.2f}% (meta 80%)")
    return 0 if lines >= 85 and branches >= 80 else 1


if __name__ == "__main__":
    sys.exit(main())
