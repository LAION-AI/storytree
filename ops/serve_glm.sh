#!/bin/bash
exec $SCRATCH/glm/src/llama.cpp/build/bin/llama-server \
  -m /home/deployer/models/GLM-5.2-abliterated/UD-Q3_K_M/GLM-5.2-UD-Q3_K_M-00001-of-00009.gguf \
  --host 127.0.0.1 --port 8099 \
  --device CUDA0,CUDA1,CUDA2,CUDA3,CUDA4,CUDA5,CUDA6,CUDA7 \
  -sm layer -ngl 999 -c 262144 -np 1 -fa on -b 4096 -ub 2048 -fit off \
  --jinja --spec-type draft-mtp --alias glm-5.2-abliterated-q3km
