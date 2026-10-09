"""Check a saved logcat file for crashes and ANRs of the app under test.

    python tools/logcat_check.py reports/evidence/<test>/logcat.txt
    adb logcat -d -v threadtime | python tools/logcat_check.py -

Exit status 1 when the app crashed or stopped responding, 0 otherwise.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from framework import config  # noqa: E402
from framework.logcat import find_problems  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("logcat", help="logcat file (threadtime format), or - for stdin")
    parser.add_argument("--package", default=config.load("local").app_package)
    args = parser.parse_args()

    log = sys.stdin.read() if args.logcat == "-" else Path(args.logcat).read_text(errors="replace")
    problems = find_problems(log, args.package)
    for p in problems:
        print(p)
    print(f"{len(problems)} crash(es)/ANR(s) of {args.package}")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
