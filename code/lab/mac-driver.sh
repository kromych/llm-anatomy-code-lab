#!/bin/bash
# Mac ISA benchmark driver (run when the Mac is quiet)
SP=/tmp/scratch/mac
SRC=$SP/llama.cpp; W=$SP/work; M=~/models/gemma-3-1b-it
MODELS=$M/google_gemma-3-1b-it-Q4_0.gguf,$M/google_gemma-3-1b-it-Q8_0.gguf,$M/google_gemma-3-1b-it-Q4_K_M.gguf
mkdir -p $W/logs $W/out
log() { echo "$(date +%FT%T%z) $*" | tee -a $W/logs/driver.log; }
COMMON="-DCMAKE_BUILD_TYPE=Release -DGGML_CCACHE=OFF -DGGML_METAL=OFF -DGGML_BLAS=OFF -DLLAMA_BUILD_TESTS=OFF -DLLAMA_BUILD_EXAMPLES=OFF -DLLAMA_BUILD_SERVER=OFF -DLLAMA_BUILD_APP=OFF -DLLAMA_USE_PREBUILT_UI=OFF"
build() {
  local name=$1; shift; local B=$SRC/build-isa-$name t0=$(date +%s)
  log "configure $name: $COMMON $*"
  cmake -S $SRC -B $B $COMMON "$@" > $W/logs/build-$name.configure.log 2>&1 || { log "configure $name FAILED"; return 1; }
  python3 -I $SP/lockrun.py shared cmake --build $B --target llama-bench llama-completion -j 16 > $W/logs/build-$name.build.log 2>&1 || { log "build $name FAILED"; return 1; }
  log "build $name done in $(( $(date +%s) - t0 )) s"
  for f in $(find $B/ggml/src -path '*ggml-cpu*.dir/flags.make'); do echo "== $f"; grep -E '^(C_FLAGS|C_DEFINES|CXX_FLAGS)' $f; done > $W/logs/build-$name.flags.txt
}
if [ "$1" = build ]; then
  { date; sw_vers; uname -a; clang --version | head -1; cmake --version | head -1; git -C $SRC rev-parse HEAD; sysctl -n machdep.cpu.brand_string hw.perflevel0.physicalcpu hw.perflevel1.physicalcpu hw.memsize; sysctl hw.optional.arm | grep -E 'FEAT_(DotProd|I8MM|BF16|FP16|SME|SVE)'; llama-bench --version 2>&1; } > $W/logs/system.txt 2>&1
  build armv8a  -DGGML_NATIVE=OFF -DGGML_CPU_ARM_ARCH=armv8-a
  build dotprod -DGGML_NATIVE=OFF -DGGML_CPU_ARM_ARCH=armv8.2-a+dotprod
  build native  -DGGML_NATIVE=ON
  log "builds done"; exit 0
fi
quiet() {   # prints busy% ; returns 0 when no llama-server/ollama/python/latexmk uses >5% CPU and total busy < 15%
  local busy hog
  busy=$(top -l 2 -n 0 -s 3 | awk '/^CPU usage/ {gsub("%","",$7); b=100-$7} END {printf "%.0f", b}')
  hog=$(ps -Ao pcpu=,comm= | awk '$1 > 5 && $0 ~ /llama-server|ollama|[Pp]ython|latexmk|llama-bench|cargo|rustc|badc-/ {print $1":"$NF}' | tr '\n' ' ')
  echo "busy=${busy}% hogs=[$hog]"
  [ "$busy" -lt 15 ] && [ -z "$hog" ]
}
bench() {   # bench <label> <llama-bench path> <threads> [extra]
  local label=$1 lb=$2 t=$3; shift 3
  local o=$W/out/$label n=0 q
  echo "label=$label bin=$lb threads=$t extra=$*" > $o.env
  while :; do q=$(quiet) && break; n=$((n+1)); [ $n -ge 360 ] && { echo "quiet check: GAVE UP after ~1 h: $q" >> $o.env; break; }; sleep 7; done
  echo "quiet check ($n retries): $q" >> $o.env; echo "start $(date +%FT%T%z)" >> $o.env; uptime >> $o.env
  top -l 1 -n 10 -o cpu -stats pid,cpu,command | tail -11 >> $o.env
  "$(dirname $lb)/llama-completion" -m $M/google_gemma-3-1b-it-Q4_0.gguf -p Hello -n 1 -no-cnv -t $t --temp 0 $CEXTRA </dev/null >/dev/null 2> $o.completion.log
  : > $o.interference; bash $SP/sampler.sh $o.interference & local sp=$!
  log "bench $label start"
  python3 -I $SP/lockrun.py exclusive $lb -m $MODELS -p 512 -n 128 -r 5 -t $t -o csv -oe md "$@" > $o.csv 2> $o.stderr
  local rc=$?; kill $sp; pkill -f "sampler.sh $o.interference"; wait $sp 2>/dev/null
  grep '^|' $o.stderr > $o.md; { echo "rc=$rc end $(date +%FT%T%z)"; uptime; } >> $o.env
  log "bench $label rc=$rc"
}
case "$1" in
  src)   for v in armv8a dotprod; do bench src-$v-t16 $SRC/build-isa-$v/bin/llama-bench 16; done
         bench src-native-t16 $SRC/build-isa-native/bin/llama-bench 16 --repack 1,0 ;;
  brew)  CEXTRA="-ngl 0 -dev none" bench brew-cpu-t16 /opt/homebrew/bin/llama-bench 16 -ngl 0 -dev none
         CEXTRA="-ngl 99" bench brew-metal-t16 /opt/homebrew/bin/llama-bench 16 -ngl 99 ;;
esac
log "$1 DONE"
