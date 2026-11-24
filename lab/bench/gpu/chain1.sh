#!/bin/bash
# chain1.sh -- tensor parallelism with vLLM, one configuration after another
cd /tmp/scratch
Q8="Qwen/Qwen3-8B qwen3-8b"
bin/tp.sh q8-tp1         0               1 $Q8
bin/tp.sh q8-tp2-nvlink  0,1             2 $Q8
bin/tp.sh q8-tp2-pcie    0,2             2 $Q8
bin/tp.sh q8-tp4         0,1,2,3         4 $Q8
bin/tp.sh q8-tp8         0,1,2,3,4,5,6,7 8 $Q8
Q72="Qwen/Qwen2.5-72B-Instruct qwen72b"
bin/tp.sh q72-tp2-nvlink 0,1             2 $Q72 --max-model-len 8192
bin/tp.sh q72-tp2-pcie   0,2             2 $Q72 --max-model-len 8192
bin/tp.sh q72-tp4        0,1,2,3         4 $Q72 --max-model-len 8192
bin/tp.sh q72-tp8        0,1,2,3,4,5,6,7 8 $Q72 --max-model-len 8192
echo "chain1 done $(date -u +%T)"
