set -e
mkdir -p ~/models/gemma-3-1b-it && cd ~/models/gemma-3-1b-it
REV=116f76234503685a98f572982177b11d44ec8ff1
for q in Q4_0 Q8_0 Q4_K_M; do
  fn=google_gemma-3-1b-it-$q.gguf
  if [ ! -f $fn ]; then curl -fsSL -o $fn.part "https://huggingface.co/bartowski/google_gemma-3-1b-it-GGUF/resolve/$REV/$fn" && mv $fn.part $fn; fi
done
ls -l; sha256sum *.gguf
