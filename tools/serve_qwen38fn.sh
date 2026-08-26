#!/usr/bin/env bash
# Serve Qwen3.8-Flash-Next-FP8 on this A100 box with vLLM (PR #53896 branch).
#
# Engine: /home/deployer/models/vllm-q38-venv (vLLM built from
# peakcrosser7/vllm@release/qwen38next, precompiled wheel — the arch is not
# in any vLLM release yet). FP8 weights run on Ampere via marlin weight-only
# dequant; QSA full-attention layers use FlashAttention-varlen, GDN linear
# layers use triton/fused-CUDA — all SM80-capable, unlike GLM-5.3's DSA.
#
# ~180 GB weights / TP4 = ~45 GB per GPU. 2 GPUs would need the PLE-offload
# PR (#53899, n-gram embeddings to CPU) — not in this branch.
#
# --enable-expert-parallel is REQUIRED on Ampere: the MoE intermediate dim
# (640) sharded by TP4 (=160) does not divide the 128er quant blocks, which
# forces the triton block-fp8 MoE kernel — and triton has no fp8e4nv on
# SM80. EP keeps experts whole (512/TP), so the marlin w8a16 path stays.
#
# Env: PORT (default 8130), GPUS (default 4,5,6,7), CTX (default 65536).
set -euo pipefail
# Driver is 550 (CUDA 12.4) but the precompiled wheel is torch+cu130. The
# forward-compat libcuda 590.48.01 in models/cuda-compat bridges that gap
# (datacenter GPUs only - fine, these are A100s).
export LD_LIBRARY_PATH="/home/deployer/models/cuda-compat${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
# Hybrid model: linear-attn state pages and QSA pages have different sizes;
# only a block-outermost layout can express that (the error message says so).
export VLLM_KV_CACHE_LAYOUT=BLHNC
# FlashInfer JIT-builds its sampling module with `ninja` (looked up on PATH);
# the venv is never "activated", so put its bin dir on PATH explicitly.
export PATH="/home/deployer/models/vllm-q38-venv/bin:$PATH"
PORT="${PORT:-8130}"
GPUS="${GPUS:-4,5,6,7}"
CTX="${CTX:-65536}"
TP=$(awk -F, '{print NF}' <<<"$GPUS")
exec env CUDA_VISIBLE_DEVICES="$GPUS" \
  /home/deployer/models/vllm-q38-venv/bin/vllm serve \
  /home/deployer/models/Qwen3.8-Flash-Next-FP8 \
  --served-model-name qwen38-flash-next \
  --host 127.0.0.1 --port "$PORT" \
  --tensor-parallel-size "$TP" \
  --enable-expert-parallel \
  --max-model-len "$CTX" \
  --gpu-memory-utilization 0.92
