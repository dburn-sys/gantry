"""Verify Gantry's hash-chained logs. Used by /gantry:audit and in CI."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _gantry import chain_verify  # noqa: E402


def main(root: Path) -> int:
    broken = 0
    for name in ("overrides.log", "approvals.jsonl", "accepted-findings.log"):
        line = chain_verify(root / ".gantry" / name)
        if line is None:
            print(f"{name}: ok")
        else:
            print(f"{name}: chain broken at line {line}")
            broken += 1
    return 1 if broken else 0


if __name__ == "__main__":
    sys.exit(main(Path(sys.argv[1] if len(sys.argv) > 1 else ".")))
