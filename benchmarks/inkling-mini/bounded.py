#!/usr/bin/env python3
"""Record a command's output and exit status under a hard process-group deadline."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import signal
import subprocess
import time


def stop_group(process):
    for sig, delay in ((signal.SIGTERM, 2), (signal.SIGKILL, 0)):
        try:
            os.killpg(process.pid, sig)
        except ProcessLookupError:
            break
        if delay:
            time.sleep(delay)
            # Reap an exited group leader before signaling again. On macOS a
            # group containing only that zombie can reject killpg with EPERM.
            process.poll()
    process.wait()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seconds", type=float, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    if not command or args.seconds <= 0:
        parser.error("Provide a positive deadline and a command after --")
    output = args.output.expanduser().resolve()
    repository = next((path for path in Path(__file__).resolve().parents
                       if (path / "models.toml").is_file() and (path / ".git").exists()), None)
    if repository and (output == repository or repository in output.parents):
        parser.error("Keep raw output outside this repository")
    output.mkdir(parents=True, exist_ok=False)
    record = {"command": command, "cwd": os.getcwd(), "timeout_seconds": args.seconds,
              "started_at": datetime.now(timezone.utc).isoformat(), "status": "running"}
    metadata = output / "command.json"
    metadata.write_text(json.dumps(record, indent=2) + "\n")
    started = time.monotonic()
    process = None
    try:
        with (output / "command.log").open("wb") as log:
            process = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
            try:
                code = process.wait(timeout=args.seconds)
                record["status"] = "exited"
            except subprocess.TimeoutExpired:
                stop_group(process)
                code = 124
                record["status"] = "timeout"
            except KeyboardInterrupt:
                stop_group(process)
                code = 130
                record["status"] = "interrupted"
    except OSError as error:
        code = 125 if process else 127
        record.update(status="cleanup_failed" if process else "launch_failed", error=str(error))
    record.update(exit_code=code, elapsed_seconds=round(time.monotonic() - started, 3),
                  child_returncode=process.returncode if process else None)
    metadata.write_text(json.dumps(record, indent=2) + "\n")
    print("{}: {} (exit {})".format(output, record["status"], code))
    raise SystemExit(code if code >= 0 else 128 - code)


if __name__ == "__main__":
    main()
