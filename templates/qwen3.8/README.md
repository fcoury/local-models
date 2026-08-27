# Qwen fixed chat template

This directory vendors Froggeric's universal Qwen 3.5, 3.6, and 3.8 chat
template for the `qwen3.8-27b-fixed-v22-4` server profile.

- Upstream: https://huggingface.co/froggeric/Qwen-Fixed-Chat-Templates
- Revision: `756cfb69d742355fd310b4ba9d50815a27d9d241`
- Template version: `qwen3.8-froggeric-v22.4`
- Upstream raw SHA-256: `c47c82b0544752d454f4e427228d9d9d8c3df64c9e446cbd0229362f67948009`
- Vendored SHA-256: `696c4f110ae05f349f381b9c7f3ef40172adc369e918f18738fec0036d14fc7b`
- License: Apache-2.0, inherited from Qwen

Do not replace the file from the upstream `main` branch in place. Add a new
versioned file and modelctl profile so historical benchmark configurations
remain reproducible.

The vendored file adds a conventional final newline to the upstream raw file;
the Jinja content is otherwise byte-for-byte identical. Runtime checks pin the
vendored hash shown above.
