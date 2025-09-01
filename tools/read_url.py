#!/usr/bin/env python3
"""
Read a URL from an NFC tag (ACS ACR1252) and capture a simple log
for inclusion in the repo. Intended to pair with tools/write_url.py
using https://example.com.

Usage:
  python tools/read_url.py            # waits for a tag, dumps URL
  python tools/read_url.py --timeout 60
"""

import argparse
import datetime
import os
import sys
import threading
import time

# Ensure local imports work when run from repo root
REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(REPO_ROOT, os.pardir))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from nfc_handler import NFCHandler  # noqa: E402


def ensure_dirs():
    os.makedirs("debug", exist_ok=True)
    os.makedirs("examples", exist_ok=True)


def main():
    parser = argparse.ArgumentParser(description="Read URL from NFC tag (NTAG213/215/216)")
    parser.add_argument("--timeout", type=int, default=60, help="Timeout in seconds waiting for a tag (default: 60)")
    args = parser.parse_args()

    ensure_dirs()
    ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    debug_log_path = os.path.join("debug", f"ndef_read_{ts}.log")
    example_log_path = os.path.join("examples", f"ndef_read_example_{ts}.txt")

    debug_log = open(debug_log_path, "w", encoding="utf-8")
    repo_log = open(example_log_path, "w", encoding="utf-8")

    def log(msg: str):
        line = f"{datetime.datetime.now().isoformat(timespec='seconds')} | {msg}\n"
        sys.stdout.write(line)
        sys.stdout.flush()
        debug_log.write(line)
        debug_log.flush()
        repo_log.write(line)
        repo_log.flush()

    log("=== NFC Read Example (NTAG213) ===")
    log("Hint: Present the tag written with tools/write_url.py")

    handler = NFCHandler(debug_mode=True)
    handler.log_callback = log

    if not handler.initialize_reader():
        log("ERROR: NFC reader not found. Ensure ACR1252 is connected and pcscd is running.")
        debug_log.close(); repo_log.close()
        return 1

    done = threading.Event()

    read_url_holder = {"url": None}

    def on_read(url: str):
        read_url_holder["url"] = url
        log(f"READ URL: {url}")
        try:
            handler.stop_monitoring()
        finally:
            done.set()

    handler.set_read_mode()
    handler.start_monitoring(read_callback=on_read, write_callback=None, log_callback=log)

    log(f"Monitoring started on reader: {handler.reader}")
    log("Please present the tag now...")

    timeout_at = time.time() + args.timeout
    while time.time() < timeout_at:
        if done.wait(timeout=0.2):
            break
    else:
        log("TIMEOUT: No tag detected within timeout window")
        try:
            handler.stop_monitoring()
        except Exception:
            pass
        debug_log.close(); repo_log.close()
        return 2

    log("=== Read session finished ===")
    debug_log.close(); repo_log.close()
    print(f"Saved debug log: {debug_log_path}")
    print(f"Saved example log: {example_log_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

