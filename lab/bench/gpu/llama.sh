#!/bin/bash
# llama.sh PART ARGS -- runs of llama.cpp (commit 61dbf4922, build 12376)
# on the rented machine. Records go to rec/isa (llama-bench, in the layout
# of lab/bench/isa), rec/validate and rec/llama.
L=/tmp/scratch; M=$L/models; SRC=$L/llama.cpp
export PATH=/usr/local/cuda/bin:$PATH
cd $L; mkdir -p rec/isa rec/validate rec/llama

bench() {   # bench LABEL BINDIR THREADS PIN EXTRA...: as the lab's driver
  local label=$1 bd=$2 t=$3 pin=$4; shift 4
  local o=rec/isa/$label
  echo "label=$label bindir=$bd threads=$t pin=$pin extra=$*" | sed "s|$L|/home/labuser|" > $o.env
  { echo "start $(date +%FT%T%z)"; uptime; } >> $o.env
  $pin $bd/llama-completion -m $M/google_gemma-3-1b-it-Q4_0.gguf -p Hello -n 1 \
      -no-cnv -t $t --temp 0 $CEXTRA </dev/null >/dev/null 2> $o.completion.log
  $pin $bd/llama-bench -m $M/google_gemma-3-1b-it-Q4_0.gguf \
      -m $M/google_gemma-3-1b-it-Q8_0.gguf -m $M/google_gemma-3-1b-it-Q4_K_M.gguf \
      -p 512 -n 128 -r 5 -t $t -o csv -oe md "$@" > $o.csv 2> $o.stderr
  local rc=$?
  grep '^|' $o.stderr > $o.md; { echo "rc=$rc end $(date +%FT%T%z)"; uptime; } >> $o.env
  cat $o.md
}

case $1 in
cuda)       # all layers on one H100
  export CUDA_VISIBLE_DEVICES=${2:-7}
  CEXTRA="-ngl 99" bench cuda-t8 $SRC/build-cuda/bin 8 "" -ngl 99 ;;
validate)   # the runs that code/ch07/validate/fit.py reads
  export CUDA_VISIBLE_DEVICES=${2:-7}
  B=$SRC/build-cuda/bin
  for run in 1 2 3; do
    echo "## gemma run $run"; $B/llama-batched-bench -m $M/gemma-3-1b-it-Q4_K_M.gguf \
        -c 4608 -npp 128,2048 -ntg 128 -npl 1 -ngl 99
    echo "## qwen run $run"; $B/llama-batched-bench -m $M/Qwen3-8B-Q8_0.gguf \
        -c 36864 -b 2048 -ub 512 -npp 128,2048 -ntg 128 -npl 1,2,4,8,16 -ngl 99
  done > rec/validate/batched-bench-h100.txt 2>&1
  grep -E '^## |^\|' rec/validate/batched-bench-h100.txt | head -60 ;;
splits)     # Algorithm H on the CUDA backend (Chapter 8)
  export CUDA_VISIBLE_DEVICES=${2:-6} PATH=$SRC/build-cuda/bin:$PATH
  S8=$L/supplement/code/ch08
  for ngl in 28 14; do
    { echo "# python3 splits.py Qwen3-1.7B-Q4_K_M.gguf -ngl $ngl"
      python3 $S8/splits.py $M/Qwen3-1.7B-Q4_K_M.gguf -ngl $ngl; } > rec/llama/splits-cuda-ngl$ngl.txt 2>&1
  done
  # a prompt of 64 tokens and one of 16, half of the layers on the GPU:
  # the raw trace of the scheduler for the graph of the prompt
  for n in 16 64; do
    words=$(python3 -c "print(' '.join(['seven'] * ($n - 1)))")
    GGML_SCHED_DEBUG=2 llama-completion -m $M/Qwen3-1.7B-Q4_K_M.gguf -p "$words" \
        -n 1 -no-cnv --no-warmup -v -ngl 14 </dev/null > rec/llama/sched-ngl14-p$n.raw.txt 2>&1
    echo "p$n: $(grep -c '## SPLIT' rec/llama/sched-ngl14-p$n.raw.txt) split lines"
  done
  head -30 rec/llama/splits-cuda-ngl28.txt ;;
load)       # time from start to /health 200, file in and out of the page cache
  export CUDA_VISIBLE_DEVICES=${2:-6}
  f=$M/Qwen3-8B-Q8_0.gguf; out=rec/llama/load-qwen3-8b-q8.txt
  echo "# llama-server -m Qwen3-8B-Q8_0.gguf (8,709,518,656 bytes) -ngl N: seconds to /health 200" > $out
  for ngl in 99 0; do for cache in cold warm warm; do
    [ $cache = cold ] && dd if=$f iflag=nocache count=0 2>/dev/null
    cached=$(fincore -b -n -o RES $f 2>/dev/null | tr -d ' ')
    t0=$(date +%s.%N)
    $SRC/build-cuda/bin/llama-server -m $f -ngl $ngl --host 127.0.0.1 --port 8091 \
        -c 4096 -t 8 > rec/llama/load-ngl$ngl-$cache.server.log 2>&1 &
    pid=$!
    until [ "$(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8091/health)" = 200 ]; do sleep 0.02; done
    t1=$(date +%s.%N)
    echo "ngl $ngl  $cache (bytes of the file in the page cache before: $cached)  $(echo "$t1 - $t0" | bc) s" >> $out
    kill $pid; wait $pid 2>/dev/null
  done; done
  cat $out; grep -h -E "offloaded|model buffer size|load time" rec/llama/load-ngl99-warm.server.log | cut -c1-160 | head ;;
isa-build)  # CPU builds for successive instruction-set levels (x86-64)
  COMMON="-DCMAKE_BUILD_TYPE=Release -DGGML_CCACHE=OFF -DLLAMA_BUILD_TESTS=OFF -DLLAMA_BUILD_EXAMPLES=OFF -DLLAMA_BUILD_SERVER=OFF"
  OFF="-DGGML_NATIVE=OFF -DGGML_SSE42=OFF -DGGML_AVX=OFF -DGGML_AVX2=OFF -DGGML_FMA=OFF -DGGML_F16C=OFF -DGGML_BMI2=OFF -DGGML_AVX512=OFF"
  H="-DGGML_SSE42=ON -DGGML_AVX=ON -DGGML_F16C=ON -DGGML_FMA=ON -DGGML_AVX2=ON -DGGML_BMI2=ON"
  build() { n=$1; shift
    cmake -S $SRC -B $SRC/build-isa-$n $COMMON "$@" > log/isa-$n.configure.log 2>&1 &&
    cmake --build $SRC/build-isa-$n --target llama-bench llama-completion -j 64 > log/isa-$n.build.log 2>&1
    echo "build $n rc=$?"; }
  build x64    $OFF
  build sse42  $OFF -DGGML_SSE42=ON
  build avx    $OFF -DGGML_SSE42=ON -DGGML_AVX=ON
  build avx2   $OFF $H
  build avx512 $OFF $H -DGGML_AVX512=ON
  build icelake $OFF $H -DGGML_AVX512=ON -DGGML_AVX512_VBMI=ON -DGGML_AVX512_VNNI=ON
  build zen4   $OFF $H -DGGML_AVX512=ON -DGGML_AVX512_VBMI=ON -DGGML_AVX512_VNNI=ON -DGGML_AVX512_BF16=ON
  build native -DGGML_NATIVE=ON
  build dl     -DGGML_NATIVE=OFF -DGGML_BACKEND_DL=ON -DGGML_CPU_ALL_VARIANTS=ON -DBUILD_SHARED_LIBS=ON ;;
isa-bench)  # 32 threads on the second socket, memory from that socket
  T=${2:-32}; PIN="numactl --cpunodebind=1 --membind=1"
  for v in x64 sse42 avx avx2 avx512 icelake zen4 dl; do
    bench $v-t$T $SRC/build-isa-$v/bin $T "$PIN" > /dev/null; echo "bench $v done"
  done
  bench native-t$T $SRC/build-isa-native/bin $T "$PIN" --repack 1,0 > /dev/null
  grep -h -E "pp512|tg128" rec/isa/*-t$T.md | head -3; ls rec/isa | wc -l ;;
esac
