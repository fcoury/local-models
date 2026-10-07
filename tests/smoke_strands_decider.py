"""Check the decision profile; pass --live with its server running."""

import json
from pathlib import Path
import subprocess
import sys
import urllib.request


ROOT = Path(__file__).resolve().parents[1]
PROFILE = "strands-decider-2b-v21"


def modelctl(*args):
    return subprocess.check_output([str(ROOT / "bin/modelctl"), *args], text=True)


endpoint = json.loads(modelctl("endpoint", PROFILE, "--json"))
assert endpoint == {
    "id": PROFILE,
    "protocol": "systemone",
    "base_url": "http://127.0.0.1:8010/v1",
    "decision_url": "http://127.0.0.1:8010/v1/systemone",
    "api_model": "strands-decider-2b-hobson-v21",
    "context": 4096,
    "output": None,
}
for scope in ("models", "services", "runnable"):
    assert PROFILE in [line.split("\t")[0] for line in modelctl("__complete", scope).splitlines()]
assert PROFILE not in modelctl("__complete", "omp")
print("Strands Decider profile metadata and completion scopes passed.")

if "--live" not in sys.argv:
    sys.exit(0)


with urllib.request.urlopen("http://127.0.0.1:8010/health", timeout=10) as response:
    health = json.load(response)
assert health["status"] == "ok" and health["model"] == endpoint["api_model"]
assert health["device"] == "mlx" and health["max_length"] == 4096

payload = {
    "state": "Help! My payouts have been failing for 3 days!",
    "questions": {
        "team": {
            "type": "choice",
            "instructions": "Which team should handle this?",
            "criteria": {
                "billing": "payment and account problems",
                "sales": "pricing and purchases",
                "retail": "store visits",
            },
        },
        "urgent": {"type": "noul", "instructions": "Does this convey urgency?"},
        "frustration": {
            "type": "score",
            "instructions": "How frustrated is the writer?",
            "criteria": ["calm", "frustrated", "very angry"],
        },
    },
}
request = urllib.request.Request(
    endpoint["decision_url"],
    data=json.dumps(payload).encode(),
    headers={"Content-Type": "application/json"},
)
with urllib.request.urlopen(request, timeout=120) as response:
    result = json.load(response)
assert result["model"] == endpoint["api_model"]
answers = result["answers"]
assert answers["team"]["choice"] == "billing", answers["team"]
assert 0 <= answers["team"]["confidence"] <= 1
assert abs(sum(answers["team"]["probabilities"].values()) - 1) < 0.01
assert answers["urgent"]["noul"] > 0.5, answers["urgent"]
assert 0 <= answers["frustration"]["score"] <= 2
assert result["usage"]["input_tokens"] > 0
print("Strands Decider choice, noul, and score requests passed.")
