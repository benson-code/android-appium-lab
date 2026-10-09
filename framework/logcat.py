"""Find crashes and ANRs of one app in logcat output (`adb logcat -v threadtime`).

Three kinds of problem, each with the lines Android writes for it:

    Java crash     E AndroidRuntime: FATAL EXCEPTION: main
                   E AndroidRuntime: Process: <package>, PID: <pid>
                   E AndroidRuntime: java.lang.RuntimeException: ...      (stack trace follows)
    Native crash   F libc    : Fatal signal 11 (SIGSEGV), ... pid <pid> (<package>)
    ANR            E ActivityManager: ANR in <package> (<package>/.Activity)

Only problems of the given package count: other apps on the device may crash too, and the
"FATAL EXCEPTION" line alone does not say which app crashed; the "Process:" line after it does.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

# 10-09 08:53:18.521 28666 28666 E AndroidRuntime: FATAL EXCEPTION: main
LINE = re.compile(r"^\d\d-\d\d \d\d:\d\d:\d\d\.\d+\s+\d+\s+\d+\s+(?P<level>[VDIWEF])\s+"
                  r"(?P<tag>[^:]*?)\s*: (?P<message>.*)$")

STACK_LINES = 30          # stack trace lines kept per Java crash


@dataclass
class Problem:
    kind: str                                   # "crash", "native crash" or "ANR"
    lines: list[str] = field(default_factory=list)

    def __str__(self) -> str:
        return f"{self.kind}:\n    " + "\n    ".join(self.lines)


def find_problems(log: str, package: str) -> list[Problem]:
    entries = []
    for raw in log.splitlines():
        m = LINE.match(raw)
        if m:
            entries.append((m["level"], m["tag"], m["message"], raw))

    problems = []
    for i, (level, tag, message, raw) in enumerate(entries):
        if tag == "AndroidRuntime" and message.startswith("FATAL EXCEPTION"):
            # The next AndroidRuntime lines name the process; keep the stack trace that follows,
            # up to the next crash report (which may belong to another app).
            following = []
            for e in entries[i + 1:i + 1 + STACK_LINES * 2]:
                if e[1] != "AndroidRuntime":
                    continue
                if e[2].startswith("FATAL EXCEPTION"):
                    break
                following.append(e)
            names_app = any(e[2].startswith(f"Process: {package},") for e in following[:3])
            if names_app:
                problems.append(Problem("crash", [raw] + [e[3] for e in following[:STACK_LINES]]))
        elif tag == "ActivityManager" and message.startswith(f"ANR in {package}"):
            problems.append(Problem("ANR", [raw]))
        elif level == "F" and "Fatal signal" in message and f"({package})" in message:
            problems.append(Problem("native crash", [raw]))
    return problems
