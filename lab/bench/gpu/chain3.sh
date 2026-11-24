#!/bin/bash
# chain3.sh -- after chain2: tensor parallelism with vLLM's fused
# all-reduce switched off, so that NCCL carries the all-reduces, on a pair
# of GPUs joined by NVLink and on a pair joined through PCIe alone.
cd /tmp/scratch
while ! grep -q "chain2 done" log/chain2.log 2>/dev/null; do sleep 10; done
OFF='{"pass_config": {"fuse_allreduce_rms": false}}'
Q8="Qwen/Qwen3-8B qwen3-8b"
bin/tp.sh q8-tp2-nvlink-nccl 0,1 2 $Q8 --compilation-config "$OFF"
bin/tp.sh q8-tp2-pcie-nccl   0,2 2 $Q8 --compilation-config "$OFF"
bin/tp.sh q8-tp4-pcie-nccl   0,2,4,6 4 $Q8 --compilation-config "$OFF"
Q72="Qwen/Qwen2.5-72B-Instruct qwen72b"
bin/tp.sh q72-tp2-nvlink-nccl 0,1 2 $Q72 --max-model-len 8192 --compilation-config "$OFF"
bin/tp.sh q72-tp2-pcie-nccl   0,2 2 $Q72 --max-model-len 8192 --compilation-config "$OFF"
echo "chain3 done $(date -u +%T)"
