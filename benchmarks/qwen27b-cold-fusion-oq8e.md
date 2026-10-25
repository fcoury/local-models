# Qwen 27B: Cold Fusion GGUF and abliterated oQ8e MLX

Experiment: 2026-10-23, Apple M5 Max, 128 GiB unified memory, macOS 27.0,
AC power. These are bounded local coding experiments, not a reproduction of
either publisher's benchmarks. One attempt per task and serving configuration.

oQ8e with oMLX MTP is the more promising general interactive setup in this
sample: 5/6 full passes in 9.1 minutes of agent time. Cold Fusion MTP completed
4/6 in 13.1 minutes, and uniquely passed Rust test writing. Keep the result
provisional: both produced 5/6 passing artifacts, they failed different tasks,
and early Cold Fusion trials had extra host load.

| Setup | Full passes | Passing artifacts | Agent time |
|---|---:|---:|---:|
| Cold Fusion Q8 GGUF, MTP off | 2/6 | 3/6 | 16.0 min |
| Cold Fusion Q8 GGUF, MTP depth 3 | 4/6 | 5/6 | 13.1 min |
| oQ8e MLX, MTP off | 3/6 | 4/6 | 13.6 min |
| oQ8e MLX, MTP depth 3 | 5/6 | 5/6 | 9.1 min |

Agent time includes model calls and public checks, excluding loading, separate
probes, independent grading and restarts. Deadline-capped attempts remain in
the totals. All 24 attempts were independently graded and all owned servers
and audit proxies were stopped afterward.

## Artifacts and runtimes

| Artifact | Pinned revision | Storage |
|---|---|---:|
| `DavidAU/Qwen3.8-27B-Cold-Fusion-GAIN-V1.1-NM-DAU-NEO-MAX-MTP-GGUF`, `NEO-MTP-Q8_0.gguf` | `cc38588bfb355c23e790db6cb98e26ac4aa53e62` | 30.24 GB / 28.16 GiB |
| `windowsxp811203/Qwen3.8-27B-Abliterated-MLX-oQ8e-mtp` | `4d4c0a483592ffbff0190573276054f2ad962a70` | 30.03 GB / 27.97 GiB |
| `ARC4NUM/Qwen3.8-Flash-Next-Uncensored-MLX-Serve-4bit` | `9ebf9993b1eaec96aec938bf883601b51a90393b` | 107.33 GB logical; 28.44 GB newly downloaded |

All downloads used aria2c. File lengths and published LFS SHA-256 hashes were
verified. The MLX tensor indexes were checked for missing shards; the oQ8e
checkpoint includes 29 MTP tensor entries. Cold Fusion's SHA-256 is
`e78d3087059cc7280fbae60b551f6be0a2fdcd0afea8d5d28283b06878172a81`.
Its optional vision projector was not downloaded.

Cold Fusion uses the existing Homebrew llama.cpp b10360 (`48d22e295`), Metal,
all GPU layers, Flash Attention, F16 KV, one slot, and a 65,536-token context.
The same GGUF is used with `--spec-type none` and with
`--spec-type draft-mtp --spec-draft-n-max 3`.

oQ8e uses oMLX 0.7.2, source commit prefix `e3bcfb5`, installed into a private
Python 3.13.14 venv with MLX 0.32.4 and the upstream-pinned dependencies.
The four native kernel extensions load successfully. The initial native build
failed because Xcode's optional Metal Toolchain was uninstalled. A previously
downloaded Apple toolchain image was temporarily mounted, and a private build
wrapper routed Metal compilation to it. The image was unmounted afterward;
no Xcode component installation or global Python package installation was needed.

The oMLX experiment uses its own state/model directories and localhost ports,
forces the text engine for both arms, disables paged SSD caching, sets one
concurrent request and 64K context, and explicitly sets MTP off or fixed depth 3.
It does not modify `~/.omlx`, register a service, or scan the other model folders.
This runtime is newer than the publisher's oMLX 0.6.4 measurements.

## Common task protocol

The frozen `small-coding` suite fingerprint is
`246c7ab0132517e1eb5c6be42ff6f034fe09632463cc2e5520085f8b0f5a131b`.
Rust/Cargo 1.99.0, Node 24.22.1 and TypeScript 6.0.3 are pinned by resolved
tool paths. Calibration verified all six references pass and all unchanged
seeds fail. All seven runner integration tests passed before scoring.

Each task uses 180 seconds of agent time, 24 model requests, 40 tool calls,
32,768 maximum output tokens per request, temperature 1, top-p 0.95, top-k 20,
and medium reasoning. Both rendered prompts were checked: the xhigh instruction
is absent, and oMLX's tokenizer endpoint reports the configured 65,536 context.
There is no repair coaching or grader feedback.

The model can only read relative task files, replace allowlisted files and run
fixed public checks. Each attempt has a fresh workspace/HOME. Model-authored
code and independent grading run under macOS Seatbelt without network or
access to sibling projects, benchmark references, hidden graders or credentials.
Trusted orchestration reads grading evidence only after the model's attempt.

The six tasks run independently so a timeout can be recorded, abandoned server
inference stopped, and the next fresh task started. Full passes require a clean
agent finish within budget plus passing independent checks. Artifact passes
are retained separately, even after a timeout. API audit files retain request
times and responses; token accounting must exclude responses abandoned after
the parent deadline when reporting tokens actually received by the agent.

## Cold Fusion results

| Task | MTP off | MTP depth 3 |
|---|---|---|
| Rust UTF-8 repair | Timeout; artifact fails; 180s | Pass; 76s |
| Rust test writing | Timeout; no submitted tests; 180s | Pass; all four mutants caught; 142s |
| Rust API migration | Pass; 96s | Pass; 44s |
| Rust explanation | Format failure; 159s | Timeout and format failure; 180s |
| TypeScript exact money parsing | Pass; 163s | Pass; 165s |
| TypeScript JSON-lines aggregation | Passing artifact, timeout; 180s | Passing artifact, timeout; 180s |

MTP off: 2/6 full passes, 3/6 passing artifacts, 957.7 seconds of agent time.
MTP depth 3: 4/6 full passes, 5/6 passing artifacts, 787.4 seconds.
The capped total is about 18% lower, with different sampled tool sequences.
This does not isolate a causal quality improvement from MTP.

The non-MTP explanation has all six structured facts correct, but its prose
is 275 words against the explicit 250-word limit. The frozen automatic grade
remains a failure; it should not be described as incorrect structured reasoning.
The UTF-8 timeout left the original buggy slicing implementation while working
through a regression demonstration. The test-writing timeout had not submitted
tests. Neither timeout proves inability to solve the task with a longer budget.

## oQ8e / oMLX results

| Task | MTP off | MTP depth 3 |
|---|---|---|
| Rust UTF-8 repair | Pass; 66s | Pass; 65s |
| Rust test writing | Timeout; no passing artifact; 180s | Timeout; submitted tests fail compilation; 180s |
| Rust API migration | Pass; 80s | Pass; 46s |
| Rust explanation | Timeout; required output files missing; 180s | Pass; all six facts and prose limit; 135s |
| TypeScript exact money parsing | Passing artifact, timeout; 180s | Pass; 67s |
| TypeScript JSON-lines aggregation | Pass; 127s | Pass; 53s |

MTP off: 3/6 full passes, 4/6 passing artifacts, 813.7 seconds of agent time.
MTP depth 3: 5/6 full passes, 5/6 passing artifacts, 544.8 seconds.
The capped total is about 33% lower. The money-parser artifact already passed
without MTP; the MTP attempt also finished within budget.

The MTP test-writing candidate includes `Some(99999) % 100000` in an assertion.
Rust rejects applying remainder to an `Option`, so the tests cannot pass on
the correct implementation, let alone establish mutation coverage. The model
had not repaired this by the deadline. This is a concrete failing submission,
not a server-loading or tool-transport error.

Both MTP setups passed the same two Rust implementation tasks, while Cold Fusion
also passed test writing and oQ8e also completed the explanation. oQ8e completed
both TypeScript tasks; Cold Fusion's aggregation artifact passed but its agent
timed out. This supports keeping both candidates for further Rust comparison,
rather than declaring either universally stronger.

## Decode probes

Separate warmed, greedy 512-token Rust-code probes use the same prompt, seed,
thinking disabled and prompt caching disabled in the request. The truncated
code is not a compiled-code quality test.

Cold Fusion's native decode timing was 15.73 tok/s without MTP and 25.83 tok/s
with MTP (1.64x). Wall time was 32.82s and 20.38s respectively. The MTP response
reports 374 accepted draft tokens out of 411 proposed (91.0%). The two returned
texts match exactly on this one probe; that is not universal equivalence proof.

oMLX reports 12.81 tok/s without MTP and 25.53 tok/s at fixed depth 3 (1.99x).
Wall time was 40.53s and 20.55s. Its native log reports 362 accepted proposals
out of 409 (88.5%), excluding bonus tokens; all three draft positions were used.
Its two returned texts also match exactly on this one probe. These matches
do not qualify all prompts or prove distributional equivalence.

The native decode counters exclude prefill; wall throughput includes it.
These short, warmed probes do not predict every agent request. For example,
oQ8e's UTF-8 task took about 65 seconds in both arms despite its 2x probe ratio.

## ARC4NUM download and shared storage

This is a download/structure check only, not an inference qualification.
Its 113 files form a different checkpoint from the existing standard
`ddalcu` Flash Next MLX pack at revision `ef5b919...`.
Fresh hashes verified 52 identical files totaling 78.88 GB; those were hard-linked
into the new folder. Only the 61 remaining files, 28.44 GB, were downloaded.
All 101 indexed weight shards and the 32.00 GB n-gram table are present.
Shared weight files should not be edited in place. Deleting one folder's links
does not remove the files from the other folder.

## Interpretation limits

Early Cold Fusion non-MTP tasks overlapped background downloading and native
oMLX compilation. Later trials ran after that setup work completed. Host load,
thermals and caches were not controlled across the entire experiment. Do not
attribute all timing or pass-count differences to MTP or rank model intelligence
from these single attempts. Runtime, quantization, chat-template and cache paths
also differ between GGUF and oMLX; this compares deployed setups.

The earlier Flint/MiMo suite used a different explanation prompt and Node version.
Historical outcomes are useful context, not a matched head-to-head comparison.
Cold Fusion's reduced-thinking and broad benchmark claims were not tested against
an otherwise identical base-model run. Long-context behavior and vision were not
tested here.

## Evidence

Paths are under `~/Library/Application Support/local-models/evaluations/`:

- `cold-fusion-q8-20261023/`: frozen suite/protocol, calibration, download hash,
  source documentation, native server commands/logs, probes and per-task results.
- `qwen-oq8e-omlx-20261023/`: model/tensor verification, runtime build logs,
  native-kernel status, isolated server state and per-task results.
- `flash-next-uncensored-download-20261023/`: source manifest, shared-file plan,
  fresh verification receipt, download log and tensor-index check.

The experiment launch scripts and API audit files remain outside Git alongside
the evidence. No production profile was replaced and no persistent service added.

## Try the retained setups

Run one foreground server at a time, and use Ctrl-C to stop it. Start oQ8e MTP:

```sh
"$HOME/Library/Application Support/local-models/evaluations/qwen-oq8e-omlx-20261023/launch-mtp3.sh"
```

Its OpenAI-compatible base URL is `http://127.0.0.1:18320/v1`, model `qwen-oq8e`.
To try Cold Fusion MTP instead:

```sh
"$HOME/Library/Application Support/local-models/evaluations/cold-fusion-q8-20261023/launch-mtp3.sh"
```

Its base URL is `http://127.0.0.1:18310/v1`, model `cold-fusion-v1.1-q8-mtp`.
`launch-dense.sh` alongside each launcher selects the recorded non-MTP setup.
These are retained experiment launchers, not registered `modelctl` profiles.
