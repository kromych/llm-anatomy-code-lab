#!/bin/bash
# setup.sh -- prepare the rented machine: tools, engines, models. Each part
# runs in its own tmux window and logs to /tmp/scratch/log.
set -u
L=/tmp/scratch; mkdir -p $L/log $L/rec $L/models; cd $L
export PATH=$HOME/.local/bin:/usr/local/cuda/bin:$PATH
export HF_HOME=/tmp/scratch/hf

part_tools() {
  date -u +"start %FT%TZ"
  sudo DEBIAN_FRONTEND=noninteractive apt-get update -qq
  sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq cmake build-essential \
      libcurl4-openssl-dev pkg-config numactl pciutils jq
  curl -LsSf https://astral.sh/uv/install.sh | sh
  cmake --version | head -1; uv --version; nvcc --version | tail -1
  date -u +"end %FT%TZ"; touch $L/log/tools.done
}
part_llama() {
  while [ ! -f $L/log/tools.done ]; do sleep 2; done
  date -u +"start %FT%TZ"
  git clone -q https://github.com/ggml-org/llama.cpp $L/llama.cpp && cd $L/llama.cpp
  git checkout -q 61dbf4922 && git log -1 --format='%H %cI'
  cmake -B build-cuda -DGGML_CUDA=ON -DCMAKE_BUILD_TYPE=Release > $L/log/cmake-cuda.txt 2>&1
  /usr/bin/time -v cmake --build build-cuda --config Release -j 96 > $L/log/build-cuda.txt 2>&1
  ls build-cuda/bin | head -40; du -sh build-cuda
  date -u +"end %FT%TZ"; touch $L/log/llama.done
}
part_vllm() {
  while [ ! -f $L/log/tools.done ]; do sleep 2; done
  date -u +"start %FT%TZ"
  uv venv -q --python 3.12 $L/venv-vllm
  /usr/bin/time -v uv pip install -p $L/venv-vllm/bin/python vllm==0.32.0 --torch-backend=auto 2>&1 | tail -40
  $L/venv-vllm/bin/python -c "import vllm, torch; print('vllm', vllm.__version__, 'torch', torch.__version__, 'cuda', torch.version.cuda, torch.cuda.device_count())"
  du -sh $L/venv-vllm
  date -u +"end %FT%TZ"; touch $L/log/vllm.done
}
part_models() {
  while [ ! -f $L/log/tools.done ]; do sleep 2; done
  date -u +"start %FT%TZ"
  uv tool install -q huggingface_hub
  cd $L/models
  REV=116f76234503685a98f572982177b11d44ec8ff1
  for q in Q4_0 Q8_0 Q4_K_M; do
    fn=google_gemma-3-1b-it-$q.gguf
    curl -fsSL -o $fn "https://huggingface.co/bartowski/google_gemma-3-1b-it-GGUF/resolve/$REV/$fn"
  done
  hf download -q ggml-org/gemma-3-1b-it-GGUF gemma-3-1b-it-Q4_K_M.gguf --local-dir .
  hf download -q ggml-org/Qwen3-8B-GGUF Qwen3-8B-Q8_0.gguf --local-dir .
  hf download -q ggml-org/Qwen3-1.7B-GGUF Qwen3-1.7B-Q4_K_M.gguf --local-dir .
  date -u +"gguf done %FT%TZ"; touch $L/log/gguf.done
  hf download -q Qwen/Qwen3-8B
  date -u +"qwen3-8b done %FT%TZ"; touch $L/log/qwen3-8b.done
  /usr/bin/time -v hf download -q Qwen/Qwen2.5-72B-Instruct 2>&1 | tail -20
  date -u +"qwen2.5-72b done %FT%TZ"; touch $L/log/qwen72.done
  ls -l $L/models; du -sh /tmp/scratch/hf/hub/*
  date -u +"end %FT%TZ"
}
part_code() {
  git clone -q https://github.com/kromych/llm-anatomy-code-lab $L/supplement
  git -C $L/supplement log -1 --format='%h %s'
}
"part_$1" > $L/log/$1.log 2>&1
