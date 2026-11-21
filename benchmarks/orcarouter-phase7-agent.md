# OrcaRouter Mix-256G: bounded native agent integration

Date: 2026-10-25. **Phase 7 bounded integration PASS, ready for review:** two
repaired, bootstrap-warm native-worker read/edit/build cases and fresh-process
resumes pass host acceptance. The exact 1843-token native-bootstrap
full/incremental control also matches all 129,280 logits bitwise. This is an
integration experiment, not a model-quality benchmark or independent
coordinator approval. Phase 6 still awaits coordinator review.

On the M5 Max / 128 GiB Mac (macOS 27.0, Xcode 27.1 / clang 21), the uncommitted
`feat/orcarouter-mix256-support` checkout at
`/Users/fcoury/code/ds4-orcarouter`, HEAD
`482710ec569db7cdd711581110c2e71adb3ccf7f`, now drives the actual native
`ds4-agent` worker, tokenizer/chat renderer, DSML41 parser, file read/edit,
Bash build, native KV save and session switch. A harness observes the ordinary
worker and production engine; this does not establish interactive TUI/PTY
acceptance.

Model: OrcaRouter DeepSeek V4.1 Flash 1017 **abliterated Mix-256G**, revision
`43fac7992b3d6e750b2e4a52569c1f097c67cd8f`, the unchanged seven downloaded
shards and Phase 3 lossless DwarfStar repack. The admitted artifact is
346,385,891,328 bytes / 1,044 tensors at
`~/models/gguf/deepseek/deepseek-v4.1-flash-1017-orcarouter-mix256g-dwarfstar-phase3-43fac799-20261024/DeepSeek-V4.1-Flash-1017-Mix-256G-DwarfStar-schema-only.gguf`.
Initial source/binary/evidence reconciliation found no Phase 6 drift. Eight
artifact identities and exact bounded header were checked without rehashing
the entire payload. This is not a new proof of every weight byte.

The normal 256-token admission guard remains. Experimental context expansion
requires an explicit agent/engine opt-in, capped at 8192, with a separate
256-row prefill workspace, one live session and a 4 GiB physical SSD cache.
A 257-token full/incremental failure exposed wide F32 router reduction drift;
reuse of the existing GPU decode-row reduction fixed it without relaxing
thresholds. Corrected context-512 / 257-token and context-2048/8192 /
769-token controls match bitwise. The raw KV window is 128; 769 also crosses
the compressed-selection boundary. This is not general 8192-token acceptance.
The exact 1843-token native bootstrap passes beyond the 1024-row sort branch:
all 129,280 logits match bitwise across two cold-produced native checkpoints
and a fresh incremental session; max error and relative L2 are zero. Selected real-router double-dot checks pass 771/771;
whole-model numerical uncertainty remains.

The final two cases use new confined projects and HOME paths, process-cold
and expert-cache-cold, seeded only with the same verified checkpoint-bound
native system/tool bootstrap KV. No task transcript or fix is copied.
Bootstrap KV is warm; OS page cache is uncontrolled. This condition was
recorded before those final attempts. It is not two fully cold runs.

Frozen prompts ask the model to read `calc.c`, change subtraction to addition
with native edit, and use Bash for `make test`. Greedy temperature 0, thinking
off; at most 512 generated tokens/round, 1536/turn and 12 tool calls.
The model actually generated and executed read/edit/bash in both cases. Host
acceptance independently reads resulting files, compiles a hidden eight-case
arithmetic driver, and checks unchanged test.c/Makefile and the allowed file
set; the agent's success assertion is insufficient.

| Final case | Initial task | Fresh-process resumed build |
|---|---|---|
| A | PASS, 203.174 s, 173 generated tokens | PASS, 78.109 s, 55 tokens |
| B | PASS, 205.400 s, 174 generated tokens | PASS, 77.925 s, 55 tokens |

Native save/switch restores exact transcript and all 129,280 F32 logits
bitwise. A copied KV with wrong checkpoint identity is rejected before
payload restoration. A foreign checkpoint namespace with the same session
filename cannot satisfy lookup. Both genuine model-generated follow-ups build
again, leave source unchanged, and pass the host eight-case check.
Checkpoint identity hashes opened-file device/inode/size/ns-mtime/ctime, not
full model contents. Identical copied/touched weights may conservatively
invalidate reuse; legacy unbound saved sessions are rejected. Old files remain.

All five native task starts are retained: earlier staging-temp failure,
headless harness drain-handshake stall, and Bash-temp failure, then the two
accepted repaired attempts. These are not an unqualified first-attempt 2/2
score. Native temporaries now honor `TMPDIR`; the harness performs the usual
frontend acknowledgement. A large KV-copy negative fixture now streams bytes
instead of misusing the 16 MiB file-tool reader. Earlier context and sandbox
pilot failures are also retained. No prompt, host grader or numerical threshold was changed to hide a
failure; the final bootstrap-warm condition is an explicit retained addendum. One earlier 8192 pilot stopped its own process when another matching
runtime appeared; that runtime exited before inspection and was never stopped.

Confinement denies network, repository/findings/graders/other-home reads and
outside writes; narrow read-only model/runtime, OS/compiler scratch, Metal
cache, metadata and native coordination-lock exceptions are documented.
An active local listener and file probes verify the relevant denials. Final
child environments use an explicit toolchain/locale allowlist. This is a
bounded macOS sandbox, not a general security qualification.

AC/headroom/ownership are checked before every invocation; large models run
serially. Limits: RSS 32 GiB, footprint 40 GiB, Metal 24 GiB, cache 4 GiB,
graph+scratch 1 GiB, available-memory floor 16 GiB; hard pressure/swap limits;
180 s engine startup, 300 s without progress, 2400 s/invocation and 7200 s
cumulative real work including failures. Owned process groups/descendants
are watchdog-cleaned; foreign services and global settings are untouched.
Cumulative real-model work, including failures and the final numerical control,
is 5864.618 seconds within the unchanged 7200-second budget. All owned
process groups/descendants are gone at completion.
The accepted task/resume processes peak at 11.37 GiB RSS, 4.56 GiB footprint,
11.46 GiB Metal allocation and zero observed swap-used growth; preexisting OS
swap is nonzero. Actual contexts reach about 2.45K tokens. Decode rounds are
about 1.42–1.50 tokens/s; native suffix prefill averages 3.36–3.49 tokens/s,
including the one-token final save sync. Initial tasks issue about 864–869 GB
of expert reads.
OS caching/background I/O and persistent expert-cache thrashing limit any
speed interpretation.

Clean Metal build, 37 regression commands including 13 baselines, prior
numerical/schema/Python checks, focused Phase 7 tests and CPU build/three help
checks pass. Metal binaries and the preexisting coordinator SSD-cache binary
are restored; final preservation/cleanup receipts accompany the result.

Practical conclusion: bounded native-worker tools and persistence pass under
the stated repaired/bootstrap-warm condition, with exact-prefix numerical
consistency and final preservation/cleanup verified.
General long-context/8K, compaction, concurrency, broad tool coverage, coding
quality, independent whole-model numerics and interactive TUI acceptance are
outstanding. Phase 8 packaging/optimization is untouched; there is no new
`modelctl` profile, default or operating recommendation.

Exact evidence root:

`/Users/fcoury/Library/Application Support/local-models/evaluations/ds4-orcarouter-phase7-20261025T160707/`

Start with `final-verification.json`, `preservation-final.json`,
`agent-trial-summary-verified-cases.json`, each `task-*-verified/` host
acceptance JSON/trace/project, `actual-native-bootstrap-repeat.json`,
`actual-native-prefix.log`, `*-watchdog.json`, `results.jsonl`, candidate/final
source/binary manifests and `evidence-sha256.json`. The full implementation
report is `/Users/fcoury/code/ds4-orcarouter/docs/ORCAROUTER_PHASE_7_RESULTS.md`;
its frozen scope, addendum, failures and exact commands remain with the evidence.
