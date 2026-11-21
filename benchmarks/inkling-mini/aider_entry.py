#!/usr/bin/env python3
"""Run pinned Aider with a fixed order and retain pre-test candidate snapshots."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import random
import socket
import subprocess
import sys
import time


def main():
    Path.home().mkdir(parents=True, exist_ok=True)
    Path(os.environ["CARGO_HOME"]).mkdir(parents=True, exist_ok=True)
    bridge = subprocess.Popen(["socat", "TCP-LISTEN:18490,bind=127.0.0.1,reuseaddr,fork",
                               "UNIX-CONNECT:/bridge/api.sock"])
    attempts = []
    coders = []
    lifecycle = []
    try:
        for _ in range(100):
            if bridge.poll() is not None:
                raise RuntimeError("Local API bridge exited")
            try:
                with socket.create_connection(("127.0.0.1", 18490), timeout=.1):
                    break
            except OSError:
                time.sleep(.05)
        else:
            raise RuntimeError("Local API bridge did not start")
        sys.path.insert(0, "/aider/benchmark")
        from aider import models
        models.register_litellm_models(["/harness/aider-model-metadata.json"])
        spec = importlib.util.spec_from_file_location("upstream_benchmark", "/aider/benchmark/benchmark.py")
        benchmark = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(benchmark)
        original = benchmark.run_unit_tests
        original_run = benchmark.run_test
        original_create = benchmark.Coder.create

        def retain_coder(*args, **kwargs):
            coder = original_create(*args, **kwargs)
            coders.append(coder)
            return coder

        def fresh_home(original_dname, testdir, *args, **kwargs):
            home = Path('/tmp/task-homes') / Path(testdir).name
            home.mkdir(parents=True, exist_ok=False)
            os.environ.update(HOME=str(home), XDG_CONFIG_HOME=str(home / 'config'),
                              XDG_CACHE_HOME=str(home / 'cache'), CARGO_HOME=str(home / 'cargo'))
            first = len(coders)
            try:
                return original_run(original_dname, testdir, *args, **kwargs)
            finally:
                # Coder can start a non-daemon summary after its final edit. Keep
                # the API available until that work ends, before the next task.
                for coder in coders[first:]:
                    pending = bool(coder.summarizer_thread and coder.summarizer_thread.is_alive())
                    started = time.monotonic()
                    coder.summarize_end()
                    coder.ok_to_warm_cache = False
                    lifecycle.append(dict(exercise=Path(testdir).name, pending_summary=pending,
                                          summary_join_seconds=time.monotonic() - started))

        def retain_and_test(original_dname, testdir, history_fname, test_files):
            # Preserve the actual candidate before test execution or second-try edits.
            # Receipts stay in this Python process until all model/test work ends.
            index = 1 + sum(a["exercise"] == testdir.name for a in attempts)
            destination = Path("/benchmarks/attempt-snapshots") / testdir.name / str(index)
            source_root = testdir / "src"
            files = {}
            for source in sorted(source_root.rglob("*")):
                if source.is_file():
                    data = source.read_bytes()
                    relative = source.relative_to(testdir)
                    target = destination / relative
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(data)
                    files[str(relative)] = hashlib.sha256(data).hexdigest()
            receipt = {"exercise": testdir.name, "attempt": index, "files": files}
            attempts.append(receipt)
            try:
                errors = original(original_dname, testdir, history_fname, test_files)
                receipt["upstream_passed"] = not bool(errors)
                return errors
            except subprocess.TimeoutExpired:
                receipt["upstream_passed"] = False
                receipt["test_timeout"] = True
                raise

        benchmark.run_unit_tests = retain_and_test
        benchmark.run_test = fresh_home
        benchmark.Coder.create = staticmethod(retain_coder)
        random.seed(0)
        benchmark.app()
    finally:
        if attempts:
            Path("/benchmarks/attempt-manifest.json").write_text(json.dumps(attempts, indent=2) + "\n")
        Path('/benchmarks/coder-lifecycle.json').write_text(json.dumps(lifecycle, indent=2) + '\n')
        bridge.terminate()
        bridge.wait(timeout=5)


if __name__ == "__main__":
    main()
