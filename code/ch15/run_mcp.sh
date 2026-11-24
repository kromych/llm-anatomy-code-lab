#!/bin/sh
# run_mcp.sh OUT: attach files_server.py of Chapter 13 to Codex and to
# opencode (Exercise 15.13).  The first part runs each harness through the
# logging proxy, without the server and with it; composition.py then gives
# the tokens of each first request.  The second part puts repeat_server.py
# in the place of the model, so that the same tool call arrives each time,
# and shows what opencode's permission gate does with it.
#   python3 proxy.py 8184 http://127.0.0.1:8084 log.jsonl dumps/
PROXY=${PROXY:-http://127.0.0.1:8184}
MODEL=${MODEL:-qwen3-8b}
MOCK=${MOCK:-8195}
HERE=$(cd "$(dirname "$0")" && pwd)
SERVER=$HERE/../ch13/files_server.py
mkdir -p "$1" && OUT=$(cd "$1" && pwd)
PROMPT='Call the tool read_file of the files server to read stats.py.'
PROMPT="$PROMPT Then name the functions that the file defines."

fresh() {    # a new git repository holding the task, and a file to protect
  rm -rf "$1" && cp -R "$HERE/task" "$1" && cd "$1" && git init -q &&
  printf '__pycache__/\n' > .git/info/exclude && git add -A &&
  git -c user.name=t -c user.email=t@example.invalid commit -qm task &&
  printf 'TOKEN=secret-value\n' > .env
}

codex_run() {    # tag, then further options of codex
  tag=$1; shift; fresh "$OUT/$tag" || exit 1
  CODEX_HOME=$OUT/codex-home timeout 600 codex exec -s workspace-write \
    -c model_provider=local -c model="$MODEL" \
    -c 'model_providers.local.name="local"' \
    -c "model_providers.local.base_url=\"$PROXY/$tag/v1\"" \
    -c 'model_providers.local.wire_api="responses"' "$@" "$PROMPT" \
    > "$OUT/$tag.out" 2> "$OUT/$tag.err" < /dev/null
  echo "$tag rc=$?"
}

opencode_run() {    # tag, base URL, model, run options, opencode.json
  tag=$1; fresh "$OUT/$tag" || exit 1
  [ -n "$5" ] && printf '%s\n' "$5" > opencode.json
  OPENCODE_CONFIG_CONTENT=$(printf '{"provider": {"p%s": {
    "npm": "@ai-sdk/openai-compatible", "options": {"baseURL": "%s"},
    "models": {"%s": {"limit": {"context": 40960, "output": 8192}}}}},
    "autoupdate": false, "share": "disabled"}' "$tag" "$2" "$3") \
  timeout 600 opencode run --standalone $4 --archived --format json \
    -m "p$tag/$3" "$PROMPT" > "$OUT/$tag.out" 2> "$OUT/$tag.err" < /dev/null
  echo "$tag rc=$?"
}

mcp() {    # the entry for opencode.json: server file, extra keys, rules
  printf '{"mcp": {"servers": {"files": {"type": "local"%s,
    "command": ["python3", "%s", "."]}}}%s}' "$2" "$1" "$3"
}

if [ -z "$GATE_ONLY" ]; then    # GATE_ONLY=1 skips the runs with the engine
mkdir -p "$OUT/codex-home"
codex_run codex-mcp0
codex_run codex-mcp1 -c 'mcp_servers.files.command="python3"' \
  -c "mcp_servers.files.args=[\"$SERVER\", \".\"]"
opencode_run opencode-mcp0 "$PROXY/opencode-mcp0/v1" "$MODEL" --auto ""
opencode_run opencode-mcp1 "$PROXY/opencode-mcp1/v1" "$MODEL" --auto \
  "$(mcp "$SERVER" "" "")"
opencode_run opencode-mcp2 "$PROXY/opencode-mcp2/v1" "$MODEL" --auto \
  "$(mcp "$SERVER" ', "codemode": false' "")"
fi

# The gate.  A copy of the server without readOnlyHint, and a model that
# asks for one call and then says "done".
sed -e 's/, "annotations": {"readOnlyHint": True}}/}/' \
    -e 's/^     "annotations": {"readOnlyHint": True}},$/     },/' \
    "$SERVER" > "$OUT/files_nohint.py"
ASK=', "permissions": [{"action": "*", "resource": "*", "effect": "ask"}]'
gate() {    # tag, server file, rules, tool, arguments, run options
  python3 "$HERE/repeat_server.py" "$MOCK" "$4" "$5" 1 \
    > "$OUT/$1.model" 2>&1 &
  pid=$!; sleep 1
  opencode_run "$1" "http://127.0.0.1:$MOCK/v1" repeat "$6" \
    "$(mcp "$2" ', "codemode": false' "$3")" > /dev/null
  kill $pid; wait $pid 2> /dev/null
  printf '%-16s %-15s %-20s -> ' "$1" "$4" "$5"
  grep '^request 3' "$OUT/$1.model" | cut -d: -f3- | cut -c1-74
}
gate gate-hint   "$SERVER" "" files_read_file '{"path": "stats.py"}'
gate gate-nohint "$OUT/files_nohint.py" "" files_read_file \
  '{"path": "stats.py"}'
gate gate-own    "$SERVER" "" read '{"path": "stats.py"}'
gate gate-env    "$SERVER" "" files_read_file '{"path": ".env"}'
gate gate-ownenv "$SERVER" "" read '{"path": ".env"}'
gate auto-env    "$SERVER" "" files_read_file '{"path": ".env"}' --auto
gate auto-ownenv "$SERVER" "" read '{"path": ".env"}' --auto
gate ask-hint    "$SERVER" "$ASK" files_read_file '{"path": "stats.py"}'
gate ask-nohint  "$OUT/files_nohint.py" "$ASK" files_read_file \
  '{"path": "stats.py"}'
gate ask-own     "$SERVER" "$ASK" read '{"path": "stats.py"}'
