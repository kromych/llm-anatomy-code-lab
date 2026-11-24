#!/bin/sh
# run_repeat.sh OUT: do opencode and Goose stop a model that repeats one
# tool call?  repeat_server.py stands in for the model and asks for the
# same call twenty times (Exercise 15.7).  No engine is needed.
MOCK=${MOCK:-8195}
HERE=$(cd "$(dirname "$0")" && pwd)
mkdir -p "$1" && OUT=$(cd "$1" && pwd)
rm -rf "$OUT/work" && cp -R "$HERE/task" "$OUT/work" && cd "$OUT/work" &&
  git init -q && git add -A &&
  git -c user.name=t -c user.email=t@example.invalid commit -qm task

model() {    # tag, tool, arguments: start the stand-in for the model
  python3 "$HERE/repeat_server.py" "$MOCK" "$2" "$3" 20 \
    > "$OUT/$1.model" 2>&1 &
  pid=$!; sleep 1
}
report() {   # tag: how many calls arrived, and what the last one returned
  kill $pid; wait $pid 2> /dev/null
  printf '%-22s %2d calls; after the last: ' "$1" \
    "$(grep -c -e '-> call' "$OUT/$1.model")"
  grep '^request' "$OUT/$1.model" | grep 'message tool' | tail -1 |
    cut -d: -f3- | cut -c1-48
}
opencode_run() {    # tag, tool, arguments, options of the run
  model "$1" "$2" "$3"
  OPENCODE_CONFIG_CONTENT=$(printf '{"provider": {"mock": {
    "npm": "@ai-sdk/openai-compatible",
    "options": {"baseURL": "http://127.0.0.1:%s/v1"},
    "models": {"repeat": {"limit": {"context": 40960, "output": 8192}}}}},
    "autoupdate": false, "share": "disabled"}' "$MOCK") \
  timeout 300 opencode run --standalone $4 --archived --format json \
    -m mock/repeat "Read the file." > "$OUT/$1.out" 2> "$OUT/$1.err" \
    < /dev/null
  report "$1"
}
goose_run() {       # tag, tool, arguments, options of the run
  model "$1" "$2" "$3"
  GOOSE_PROVIDER=openai GOOSE_MODEL=repeat OPENAI_API_KEY=local \
  OPENAI_HOST=http://127.0.0.1:$MOCK OPENAI_BASE_PATH=v1/chat/completions \
  GOOSE_MODE=auto GOOSE_DISABLE_KEYRING=1 GOOSE_TELEMETRY_OFF=1 \
  GOOSE_CONTEXT_LIMIT=40960 \
  timeout 300 goose run --no-session --max-turns 30 $4 \
    --output-format stream-json -t "Read the file." \
    > "$OUT/$1.out" 2> "$OUT/$1.err" < /dev/null
  report "$1"
}

opencode_run opencode-same      read '{"path": "stats.py"}' ""
opencode_run opencode-same-auto read '{"path": "stats.py"}' --auto
opencode_run opencode-fail      read '{"path": "nofile.py"}' ""
opencode_run opencode-fail-auto read '{"path": "nofile.py"}' --auto
goose_run goose-same        shell '{"command": "cat stats.py"}' ""
goose_run goose-same-limit3 shell '{"command": "cat stats.py"}' \
  "--max-tool-repetitions 3"
