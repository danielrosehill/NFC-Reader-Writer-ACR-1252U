#!/usr/bin/env python3
"""
Write a URL (default: https://example.com) to an NFC tag using the
ACS ACR1252 reader, and capture a detailed log suitable for committing
as an example (no sensitive URLs included).

Usage:
  python tools/write_url.py               # writes https://example.com
  python tools/write_url.py --url URL     # custom URL
  python tools/write_url.py --lock        # lock tag after write (irreversible)

Outputs:
  - debug/ndef_write_<timestamp>.log      (verbose runtime log; .gitignored)
  - examples/ndef_write_example_<timestamp>.txt (sanitized log for repo)
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
    parser = argparse.ArgumentParser(description="Write a URL to an NFC tag (NTAG213/215/216)")
    parser.add_argument("--url", default="https://example.com", help="URL to write (default: https://example.com)")
    parser.add_argument("--lock", action="store_true", help="Permanently lock tag after write (irreversible)")
    parser.add_argument("--timeout", type=int, default=60, help="Timeout in seconds waiting for a tag (default: 60)")
    args = parser.parse_args()

    ensure_dirs()
    ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    debug_log_path = os.path.join("debug", f"ndef_write_{ts}.log")
    example_log_path = os.path.join("examples", f"ndef_write_example_{ts}.txt")

    # Open log files
    debug_log = open(debug_log_path, "w", encoding="utf-8")
    repo_log = open(example_log_path, "w", encoding="utf-8")

    def log(msg: str):
        line = f"{datetime.datetime.now().isoformat(timespec='seconds')} | {msg}\n"
        # Console
        sys.stdout.write(line)
        sys.stdout.flush()
        # Debug file (ignored by git)
        debug_log.write(line)
        debug_log.flush()
        # Repo-safe example log
        repo_log.write(line)
        repo_log.flush()

    log("=== NFC Write Example (NTAG213) ===")
    log(f"URL: {args.url}")
    log(f"Lock after write: {args.lock}")
    log("Hint: Present a blank or rewritable NTAG213 tag to the reader")

    handler = NFCHandler(debug_mode=True)
    handler.log_callback = log

    # Prepare message ahead of time and log its structure
    ndef_message = handler.create_ndef_record(args.url)
    log(f"Prepared NDEF TLV bytes: {len(ndef_message)} bytes")
    log(f"TLV (hex, first 64): {ndef_message.hex()[:128]}{'...' if len(ndef_message.hex())>128 else ''}")

    if not handler.initialize_reader():
        log("ERROR: NFC reader not found. Ensure ACR1252 is connected and pcscd is running.")
        debug_log.close(); repo_log.close()
        return 1

    done = threading.Event()

    def on_write(msg: str):
        log(f"WRITE: {msg}")
        # Stop monitoring and signal completion
        try:
            handler.stop_monitoring()
        finally:
            done.set()

    # Switch to write mode and start async monitoring
    handler.set_write_mode(args.url, lock_after_write=args.lock)
    handler.start_monitoring(read_callback=None, write_callback=on_write, log_callback=log)

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

    log("=== Write session finished ===")
    debug_log.close(); repo_log.close()
    print(f"Saved debug log: {debug_log_path}")
    print(f"Saved example log: {example_log_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

