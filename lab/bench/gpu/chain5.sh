#!/bin/bash
# chain5.sh -- the model of 72 billion parameters on two cards with NCCL
# carrying the all-reduces, over NVLink and through PCIe; a shorter
# context, so that the cache fits beside the weights.
cd /tmp/scratch
OFF='{"pass_config": {"fuse_allreduce_rms": false}}'
Q72="Qwen/Qwen2.5-72B-Instruct qwen72b"
CS="1 8" bin/tp.sh q72-tp2-nvlink-4k 0,1 2 $Q72 --max-model-len 4096 --compilation-config "$OFF"
CS="1 8" bin/tp.sh q72-tp2-pcie-4k   0,2 2 $Q72 --max-model-len 4096 --compilation-config "$OFF"
echo "chain5 done $(date -u +%T)"
