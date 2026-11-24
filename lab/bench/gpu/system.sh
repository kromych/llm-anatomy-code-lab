#!/bin/bash
# system.sh -- what the rented machine is: printed once, for the notes.
export PATH=/usr/local/cuda/bin:$PATH
run() { echo; echo "## $*"; "$@" 2>&1; }
run hostname
run uname -srm
run sh -c '. /etc/os-release; echo "$PRETTY_NAME"; ldd --version | head -1'
run sh -c 'lscpu | grep -E "Model name|Socket|Core|Thread|^CPU\(s\)|NUMA|Flags" | cut -c1-2000'
run numactl -H
run free -g
run sh -c 'lsblk -o NAME,SIZE,TYPE,MOUNTPOINT; df -h / /ephemeral'
run nvidia-smi
run nvidia-smi --query-gpu=index,name,memory.total,driver_version,pci.bus_id,pcie.link.gen.current,pcie.link.width.current --format=csv
run nvidia-smi topo -m
run nvidia-smi nvlink -s
run nvidia-smi nvlink -c
run sh -c 'sudo lspci -vv 2>/dev/null | grep -E "^[0-9a-f:.]+ .*NVIDIA|LnkCap:|LnkSta:" | grep -A2 NVIDIA | head -40'
run nvcc --version
run sh -c 'cat /proc/driver/nvidia/version'
run docker --version
run sh -c 'nvidia-ctk --version; docker info 2>/dev/null | grep -i -A3 runtimes'
run sh -c 'cmake --version | head -1; gcc --version | head -1; python3 --version; ~/.local/bin/uv --version'
