#!/bin/bash
set -e
cd /home/deployer/laion/bookwriter
while [ ! -f runs/meta_layer_v2b/meta.json ]; do sleep 60; done
sleep 5
python3 distill/plot_layer.py --meta runs/meta_layer_v2b/meta.json --events runs/events_build10_full/events.json --out runs/plot_layer --ports 8110,8111 >> runs/plot_layer.log 2>&1
echo "$(date -Is) PLOTS-DONE" >> runs/eval_ox/judging.log
