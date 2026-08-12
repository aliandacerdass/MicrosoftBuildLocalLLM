"""Prove (or disprove) the offline claim without a human watching.

The problem: while the network is off, nobody can drive the test interactively. So
this script waits for the network to go away by itself, runs a cold question the
moment it does, and writes everything it saw to a log file.

    python tests/offline_check.py            # then turn Wi-Fi off for ~2 minutes

Read the log afterwards: tests/offline_check.log
"""

from __future__ import annotations

import socket
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOG = Path(__file__).with_suffix(".log")
QUESTION = "What is cosine similarity?"
WAIT_FOR_OFFLINE_SECONDS = 900
ANSWER_TIMEOUT_SECONDS = 300


def online(host: str = "1.1.1.1", port: int = 443, timeout: float = 2.0) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def log(handle, message: str) -> None:
    line = f"[{datetime.now():%H:%M:%S}] {message}"
    print(line, flush=True)
    handle.write(line + "\n")
    handle.flush()


def main() -> int:
    with LOG.open("w", encoding="utf-8") as handle:
        log(handle, "waiting for the network to go down (turn Wi-Fi off now)...")

        deadline = time.time() + WAIT_FOR_OFFLINE_SECONDS
        while online():
            if time.time() > deadline:
                log(handle, "RESULT: gave up - the network never went down.")
                return 1
            time.sleep(3)

        log(handle, "network is down. Waiting 5s to be sure, then asking a cold question.")
        time.sleep(5)
        if online():
            log(handle, "network came back before the test started - run this again.")
            return 1

        started = time.time()
        try:
            proc = subprocess.run(
                [sys.executable, "-m", "localrag.cli", QUESTION],
                cwd=ROOT,
                capture_output=True,
                text=True,
                timeout=ANSWER_TIMEOUT_SECONDS,
            )
            elapsed = time.time() - started
            log(handle, f"process finished in {elapsed:.1f}s with exit code {proc.returncode}")
            log(handle, "--- stdout ---\n" + (proc.stdout or "(empty)"))
            log(handle, "--- stderr ---\n" + (proc.stderr.strip() or "(empty)"))

            answered = proc.returncode == 0 and "similarity" in proc.stdout.lower()
            log(handle, f"still offline at the end: {not online()}")
            log(handle, "RESULT: WORKS OFFLINE" if answered else "RESULT: FAILED OFFLINE")
            return 0 if answered else 2
        except subprocess.TimeoutExpired as error:
            log(handle, f"RESULT: TIMED OUT after {ANSWER_TIMEOUT_SECONDS}s")
            log(handle, "--- partial stdout ---\n" + (error.stdout or b"").decode(errors="replace"))
            return 3


if __name__ == "__main__":
    sys.exit(main())
