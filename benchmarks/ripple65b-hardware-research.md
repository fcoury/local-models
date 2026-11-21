# Ripple 65B version selection for the M5 Max

**Retired locally on 2026-11-05.** The user requested removal after the bounded
Rust screen. Weights, isolated runtime and catalog entry are gone; this page
preserves the original selection research and recovery pins.

The subsequent [local qualification and bounded Rust screen](ripple65b-local-pilot.md)
records the verified download and measured outcome. The original selection
research below does not establish a coding-quality winner.

**2026-11-05 — research and proposed evaluation; no local model run.**
Hardware inspection confirms Apple M5 Max and 128 GiB unified memory.
The initial selection was [araysuter/Ripple-65B-Preview-MLX-mixed-4bit](https://huggingface.co/araysuter/Ripple-65B-Preview-MLX-mixed-4bit):
39.05 GB of weights, protected 8-bit tensors and a published M5 Max integration
path. This is a practical first candidate, not an independently established
quality or speed winner. See the [evaluation index](README.md) for measured results.

## Available versions and tradeoffs

Ripple-65B Preview is the instruction-tuned, text-only dense model. The separate
Base checkpoint is pretrained only. Ricursive's published coding scores use
BF16 and maximum effort; they do not establish quantized Mac performance.
[Official model card](https://huggingface.co/ricursiveAI/Ripple-65B-Preview).

Sizes below sum weight files from publisher metadata at the recorded revisions.
GB means decimal bytes; these figures exclude KV cache, runtime allocations and
the operating system. The GGUF repository contains many alternatives; download
only the selected file or split-file parts.

| Candidate | Weight size | Role on this Mac |
|---|---:|---|
| [araysuter mixed 4-bit MLX](https://huggingface.co/araysuter/Ripple-65B-Preview-MLX-mixed-4bit) | 39.05 GB / 36.37 GiB | Recommended first candidate. Most matrices are 4-bit; attention gates, embeddings and output head are 8-bit. Same-chip capacity and optional drafting evidence. |
| [frogggias uniform 4-bit MLX](https://huggingface.co/frogggias/Ripple-65B-Preview-MLX-4bit) | 36.44 GB / 33.94 GiB | Simpler alternative with its own adapter, PyTorch parity diagnostics and OpenAI-compatible server instructions. No controlled quality comparison against mixed 4-bit. |
| [AtomicChat AD-Q6_K GGUF](https://huggingface.co/AtomicChat/Ripple-65B-Preview-GGUF) | 57.67 GB / 53.71 GiB, two parts | Higher-precision alternative through current llama.cpp. Publisher reports calibrated distribution-fidelity diagnostics; Mac throughput remains unmeasured here. |
| [frogggias 8-bit MLX](https://huggingface.co/frogggias/Ripple-65B-Preview-MLX-8bit) / [AtomicChat Q8_0 GGUF](https://huggingface.co/AtomicChat/Ripple-65B-Preview-GGUF) | 68.83 / 68.84 GB, about 64.1 GiB | Higher-precision reference candidates. Expected to fit at moderate context with desktop headroom, but read more weight data per generated token. |
| [Official BF16](https://huggingface.co/ricursiveAI/Ripple-65B-Preview) | 129.57 GB / 120.67 GiB | Leaves insufficient practical headroom for this desktop and inference overhead. |
| [Official NVFP4](https://huggingface.co/ricursiveAI/Ripple-65B-Preview-NVFP4) | 57.21 GB / 53.28 GiB | NVIDIA-oriented release. No verified native Metal loading path in this research; file size alone does not make it a Mac candidate. |

The conversion authors use different parity prompts and diagnostic methods.
Their token agreement and KL figures are not comparable task-quality scores.
Selecting mixed 4-bit prioritizes a documented M5 Max path and a small resident
footprint. Our Rust evaluation must establish whether its quality is sufficient.

## Runtime support and expected performance

Both reviewed MLX conversions ship custom `ricursive` adapters and require
`trust_remote_code`. The mixed conversion reports MLX 0.32.4 and MLX-LM 0.32.2;
the locally inspected general MLX environment has MLX 0.31.2 / MLX-LM 0.31.3.
Prepare an isolated pinned environment and review the adapter before loading.
Compatibility with the existing mlx-serve binary is unqualified.

The mixed conversion author reports roughly 12.2–12.3 tokens/s without drafting
and 16.1–22.3 with DFlash2 on a 64 GiB M5 Max in short matched prose/code probes.
The 128K capacity probe reports 49.10 GiB peak MLX allocation with target,
drafter and caches. These are author measurements, not measurements of our
128 GiB machine or a sustained coding evaluation.
[Pinned DFlash2 runbook and limitations](https://github.com/araysuter/TensorFold/blob/ff4ed431eb6203f1ff5c0fd1150c641c38fc3553/tools/ripple/DFLASH2.md).

DFlash2 adds a separate approximately 2.48 GB quantized drafter and needs a
temporary TensorFold fork plus isolated MLX dispatcher changes. It is not
enabled by loading the target in stock MLX-LM. Qualify plain decoding first;
treat drafting as a separate runtime condition and verify token/output parity.
Ripple is dense, so do not extrapolate our MoE models' generation speed to it.

llama.cpp support merged on 2026-11-05 at 18:55 UTC, merge commit
`fecdc81eec0922b229e7e6f4069cea603e10d6a7`. The reviewed AtomicChat card still
describes it as unmerged. Use a pinned build containing the merge for GGUF;
neither that merge nor the file format establishes local Metal acceptance.
[Upstream PR #31692](https://github.com/ggml-org/llama.cpp/pull/31692).

## Proposed evaluation scope

Start the infrastructure smoke with one model process and a 32K context. Verify chat, streaming, tool
calls, reasoning separation, effective sampling controls, cancellation and a
bounded edit/build task before scoring. The reviewed templates do not expose
an `enable_thinking` or `reasoning_effort` switch; `clear_thinking` controls
retained assistant reasoning. Do not label a run thinking-off without a live
request/template qualification.

Before scoring, qualify the existing protocol's 65,536-token context and
8,192-token response cap, including reasoning. Then use the frozen five-exercise
Aider Rust pilot and independent acceptance checks. Keep temperature 0,
whole-file editing, one worker, two attempts and the frozen budgets.
If reasoning mode differs from DS4/Flash
Next, report it as a separate condition. Record native token counts, caps,
wall time, prompt/decode rates, peak memory and swap changes. Expand to all
30 exercises only after the pilot; test DFlash2 separately after plain decoding.

No weights were downloaded, runtime installed, services started or benchmark
scores produced by this research. Future acquisition uses the agreed resumable
60 MB/s transfer and one separate OpenSSL checksum pass against pinned LFS
digests before loading. No existing checkpoint needs removal.

## Pins and retained evidence

| Artifact | Reviewed Hugging Face revision |
|---|---|
| Official instruct BF16 | `e27e171792f303d74c048184e8259ba663cfa0d5` |
| Official NVFP4 | `99eea4477a001a41b86914e41feb4b2ed86105e5` |
| Official DFlash2 | `35609b3be3dd08a822b3ba1257c1ea5dd6f87632` |
| araysuter mixed 4-bit MLX | `d7725b5226eaca300a2ec842660aa1392c63f250` |
| frogggias 4-bit MLX | `4a33b33f043f41a51ae7236edd440d64cfa7cc94` |
| frogggias 8-bit MLX | `dd672246374fa2a3829fcc42c3ad02409098909f` |
| AtomicChat GGUF collection | `265a516b077309363590b9ca8e29d6d414050135` |

Retained public model cards, configs, file sizes/LFS metadata, selected adapter
source and the upstream PR response are under
`~/Library/Application Support/local-models/benchmarks/ripple65b-research-20261105/`.
This is research evidence; artifact verification, infrastructure qualification
and independent model acceptance remain pending.
