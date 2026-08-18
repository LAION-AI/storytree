#!/usr/bin/env bash
# usage: launch_one.sh <gpu> <port> [extra vllm args...]
# Winning config for Qwen3.8-27B-Uncensored-FP8 on A100-80GB (SM80).
GPU=$1; PORT=$2; shift 2
export CUDA_VISIBLE_DEVICES=$GPU
# A100 driver is 550 (CUDA 12.4) but torch in this venv is cu130 -> NVIDIA forward-compat libs
export LD_LIBRARY_PATH=/home/deployer/models/cuda-compat:$LD_LIBRARY_PATH
# venv bin must be on PATH: vLLM JIT-compiles the FlashInfer sampler and needs `ninja`
export PATH=/home/deployer/models/vllm-venv/bin:/usr/local/cuda-12.8/bin:$PATH
export HF_HUB_OFFLINE=1
export VLLM_LOGGING_LEVEL=INFO
exec /home/deployer/models/vllm-venv/bin/vllm serve /home/deployer/models/Qwen3.8-27B-Unc-FP8 \
  --served-model-name qwen3.8-27b \
  --port $PORT --host 127.0.0.1 \
  --tensor-parallel-size 1 \
  --max-model-len 131072 \
  --gpu-memory-utilization 0.92 \
  --enable-prefix-caching \
  --mamba-cache-mode align \
  --speculative-config '{"method":"qwen3_5_mtp","num_speculative_tokens":4}' \
  --trust-remote-code \
  "$@"
