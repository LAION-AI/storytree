#!/usr/bin/env bash
# Ornith-1.5-397B Q4_K_M (qwen35moe, 512x11B MoE) on 4x A100-80GB via llama.cpp.
# -np 1: aggregate throughput on a sparse MoE is flat across concurrent slots, and the
# context window is divided between slots, so one slot with the full window is strictly
# better. Same finding as GLM-5.2 in ops/README.md.
export LD_LIBRARY_PATH=/usr/local/cuda-12.8/lib64:$LD_LIBRARY_PATH
GPUS=${GPUS:-CUDA0,CUDA1,CUDA2,CUDA3}
PORT=${PORT:-8110}
exec /home/deployer/models/llama.cpp.build/build/bin/llama-server \
  -m /home/deployer/models/Ornith-1.5-397B/Ornith-1.5-397B-Q4_K_M.gguf \
  --host 127.0.0.1 --port $PORT \
  --device $GPUS -sm layer -ngl 999 \
  -c 32768 -np 1 -fa on -b 2048 -ub 512 \
  --jinja --alias ornith-1.5-397b
