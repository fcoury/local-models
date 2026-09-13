#!/usr/bin/env python3
"""Run without model weights; exercise metadata, launch arguments and exclusion."""
import json
import os
from pathlib import Path
import subprocess
import tempfile

root = Path(__file__).resolve().parents[1]
source = (root / "bin/modelctl").read_text().split('command_name="${1:-}"')[0]
model = "deepseek-v4.1-flash-q2-32k"
with tempfile.TemporaryDirectory() as temp:
    env = dict(os.environ, LOCAL_MODEL_STATE_HOME=temp, MODELCTL_OMP_AGENT_DIR=temp,
               DEEPSEEK41_DS4_ROOT=temp, MODEL_HOME=temp)
    def run(command, ok=True):
        result = subprocess.run(["bash", "-c", source + "\n" + command], env=env,
                                text=True, capture_output=True)
        assert (result.returncode == 0) == ok, result.stderr
        return result.stdout
    endpoint = json.loads(run(f"endpoint {model} --json"))
    assert endpoint["api_model"] == "deepseek-v4.1-flash"
    assert (endpoint["context"], endpoint["output"]) == (32768, 16384)
    assert endpoint["base_url"] == "http://127.0.0.1:8009/v1"
    for target in [model, "deepseek-v4-flash"]:
        run(f"write_omp_models {target}")
        cfg = next(iter(json.loads((Path(temp) / "models.yml").read_text())["providers"].values()))
        assert cfg["api"] == "openai-responses"
        assert cfg["models"][0]["input"] == (["text"] if target == model else ["text", "image"])
        assert cfg["models"][0]["thinking"]["requiresEffort"] == (target != model)
        assert cfg["models"][0]["compat"]["reasoningEffortMap"] == ({"minimal": "none"} if target == model else {})
    mocks = 'healthy() { return 0; }; omp() { printf "%s\\n" "$@"; }; '
    for flags, expected in [("--thinking off", ["--thinking", "minimal"]),
                            ("--thinking=off", ["--thinking=minimal"]),
                            ("--thinking high", ["--thinking", "high"])]:
        actual = run(mocks + f"run_omp {model} {flags} prompt").splitlines()
        assert actual[2:] == expected + ["prompt"], actual
    assert len(run(mocks + f"run_omp {model}").splitlines()) == 2
    assert run(mocks + f"run_omp {model} -- --thinking off").splitlines()[2:] == ["--", "--thinking", "off"]
    server = Path(temp) / "ds4-server"
    server.write_text('#!/bin/sh\nprintf "%s\\n" "$@"\n')
    server.chmod(0o755)
    quiet = "service_loaded() { return 1; }; listening() { return 1; }; "
    args = run(quiet + f"run_model {model}").splitlines()
    assert "--ssd-streaming" in args and args[args.index("--backend") + 1] == "metal"
    for flag, value in [("--ctx", "32768"), ("--tokens", "16384"), ("--port", "8009")]:
        assert args[args.index(flag) + 1] == value
    run(quiet + f"require_deepseek41_exclusive {model}")
    run('service_loaded() { [[ "$1" == glm-5.3-flash-q2 ]]; }; listening() { return 1; }; '
        + f"require_deepseek41_exclusive {model}", ok=False)
    run('service_loaded() { return 1; }; listening() { [[ "$1" == ' + model + ' ]]; }; '
        + "require_deepseek41_exclusive glm-5.3-flash-q2", ok=False)
print("DeepSeek V4.1 profile checks passed")
