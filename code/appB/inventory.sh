#!/usr/bin/env bash
# inventory.sh -- list what the tools of "Anatomy of the Open-Source LLM
# Stack" have left on this machine (macOS or Linux): directories with their
# sizes, credential files (presence only, never contents), binaries,
# processes, listening sockets, services and service users.  Appendix B.
#
#   ./inventory.sh                 all tools
#   ./inventory.sh ollama codex    only these tools
#   ./inventory.sh --remove codex  list, then offer to delete each user-owned
#                                  path of these tools, asking every time
#
# The script deletes nothing unless --remove is given and you answer "y" for
# that path.  It never uses sudo; system-wide paths are listed with the
# command that removes them, for you to run yourself.
set -u
OS=$(uname -s)
C=${XDG_CACHE_HOME:-$HOME/.cache}
CF=${XDG_CONFIG_HOME:-$HOME/.config}
D=${XDG_DATA_HOME:-$HOME/.local/share}
S=${XDG_STATE_HOME:-$HOME/.local/state}
T=${TMPDIR:-/tmp}; T=${T%/}
AS="$HOME/Library/Application Support"
LC="$HOME/Library/Caches"
HF=${HF_HOME:-$C/huggingface}
REMOVE=0
[ "${1:-}" = "--remove" ] && { REMOVE=1; shift; }
ALL="llama.cpp ollama vllm sglang lmstudio huggingface torch shaders docker
podman searxng codex opencode goose aider openhands claude cline
mini-swe-agent mcp-inspector inspect python node"
TOOLS=${*:-$ALL}

# paths TOOL: one "kind path" per line; kind is dir, cred, bin or sys
paths() {
  case $1 in
  llama.cpp) echo "dir ${LLAMA_CACHE:-$C/llama.cpp}"; echo "dir $LC/llama.cpp"
    echo "sys /opt/homebrew/Cellar/llama.cpp"; echo "sys /opt/homebrew/Cellar/ggml"
    echo "dir $HOME/src/llama.cpp" ;;
  ollama) echo "dir ${OLLAMA_MODELS:-$HOME/.ollama}"; echo "dir $HOME/.ollama"
    echo "cred $HOME/.ollama/id_ed25519"; echo "dir $HOME/.local/ollama"
    echo "dir $AS/Ollama"; echo "dir $LC/com.electron.ollama"
    echo "sys /Applications/Ollama.app"; echo "sys /opt/homebrew/Cellar/ollama"
    echo "sys /usr/local/lib/ollama"; echo "sys /usr/local/bin/ollama"
    echo "sys /usr/share/ollama"; echo "sys /etc/systemd/system/ollama.service" ;;
  huggingface) echo "dir $HF/hub"; echo "dir $HF/datasets"; echo "dir $HF/xet"
    echo "cred $HF/token"; echo "cred $HF/stored_tokens" ;;
  torch) echo "dir ${TORCHINDUCTOR_CACHE_DIR:-$T/torchinductor_$(id -un)}"
    echo "dir ${TORCH_HOME:-$C/torch}"; echo "dir ${TRITON_CACHE_DIR:-${TRITON_HOME:-$HOME}/.triton}"
    echo "dir $HOME/.nv/ComputeCache" ;;
  shaders) echo "dir $C/mesa_shader_cache"; echo "dir $C/mesa_shader_cache_db"
    [ "$OS" = Darwin ] && echo "dir $(getconf DARWIN_USER_CACHE_DIR)com.apple.metal" ;;
  docker) echo "dir $HOME/.docker"; echo "dir $HOME/Library/Containers/com.docker.docker"
    echo "sys /var/lib/docker"; echo "sys /var/lib/containerd" ;;
  podman) echo "dir $D/containers"; echo "dir $CF/containers" ;;
  codex) echo "dir ${CODEX_HOME:-$HOME/.codex}"; echo "cred ${CODEX_HOME:-$HOME/.codex}/auth.json" ;;
  opencode) echo "dir $D/opencode"; echo "dir $C/opencode"; echo "dir $CF/opencode"
    echo "dir $S/opencode"; echo "cred $D/opencode/opencode.db"
    echo "cred $D/opencode/auth.json" ;;
  goose) echo "dir $CF/goose"; echo "dir $D/goose"; echo "dir $S/goose"; echo "dir $AS/Goose"
    echo "cred $CF/goose/secrets.yaml" ;;
  aider) echo "dir $HOME/.aider"; echo "cred $HOME/.aider.conf.yml"; echo "cred $HOME/.env" ;;
  openhands) echo "dir $HOME/.openhands"; echo "dir $D/uv/tools/openhands"
    echo "cred $HOME/.openhands/agent_settings.json" ;;
  claude) echo "dir $HOME/.claude"; echo "dir ${CLAUDE_CONFIG_DIR:-$HOME/.claude}"
    echo "dir $HOME/.claude.json"
    echo "cred ${CLAUDE_CONFIG_DIR:-$HOME/.claude}/.credentials.json"
    # the installer script's program, link, state and cache; the uninstall
    # instructions of the documentation name the first two only
    echo "dir $HOME/.local/share/claude"; echo "dir $D/claude"
    echo "dir $HOME/.local/bin/claude"
    echo "dir $HOME/.local/state/claude"; echo "dir $S/claude"
    echo "dir $HOME/.cache/claude"; echo "dir $C/claude" ;;
  cline) echo "dir $HOME/.cline"
    echo "cred $HOME/.cline/data/settings/providers.json"
    for d in /opt/homebrew/lib /usr/local/lib /usr/lib; do   # npm install -g
      echo "sys $d/node_modules/cline"; done
    echo "dir $AS/Code/User/globalStorage/saoudrizwan.claude-dev"
    echo "dir $CF/Code/User/globalStorage/saoudrizwan.claude-dev" ;;
  mini-swe-agent) echo "dir $AS/mini-swe-agent"; echo "dir $CF/mini-swe-agent" ;;
  # the Inspector's catalog, its OAuth state and, where the system has no
  # keyring, its secrets file; the packages themselves are under `node`
  mcp-inspector) echo "dir $HOME/.mcp-inspector"
    echo "cred ${MCP_INSPECTOR_SECRET_FILE:-$HOME/.mcp-inspector/secrets.json}" ;;
  inspect) echo "dir $AS/inspect_ai"; echo "dir $LC/inspect_ai"
    echo "dir $D/inspect_ai"; echo "dir $C/inspect_ai" ;;
  python) echo "dir $C/pip"; echo "dir $LC/pip"; echo "dir $C/uv"; echo "dir $D/uv" ;;
  # npm's download cache, and the packages that npx unpacked (MCP servers,
  # the MCP Inspector); `npm uninstall -g` leaves both
  node) echo "dir ${npm_config_cache:-$HOME/.npm}/_cacache"
    echo "dir ${npm_config_cache:-$HOME/.npm}/_npx" ;;
  vllm) echo "dir ${VLLM_CACHE_ROOT:-$C/vllm}"; echo "dir ${VLLM_CONFIG_ROOT:-$CF/vllm}"
    echo "dir $C/flashinfer"; echo "dir $HOME/vllm-cpu" ;;
  sglang) ;;   # the CPU route is a Docker image; see extra()
  lmstudio) echo "dir $HOME/.lmstudio"; echo "dir $HOME/.lmstudio-home-pointer"
    echo "cred $HOME/.lmstudio/.internal/lms-key-2"
    echo "dir $AS/LM Studio"; echo "dir $LC/ai.elementlabs.lmstudio"
    echo "dir $LC/ai.elementlabs.lmstudio.ShipIt"; echo "dir $HOME/Library/Logs/LM Studio"
    echo "dir $HOME/Library/HTTPStorages/ai.elementlabs.lmstudio"
    echo "dir $CF/LM Studio"; echo "dir $C/lm-studio-updater"
    echo "sys /Applications/LM Studio.app" ;;
  searxng) echo "sys $HOME/searxng"   # owned by the container's user: sudo to remove
    echo "cred $HOME/searxng/config/settings.yml" ;;
  esac
}
# process and service name patterns (extended regular expressions)
pattern() {
  case $1 in
  llama.cpp) echo 'llama-(server|cli|bench)' ;;  ollama) echo 'ollama' ;;
  docker) echo 'docker|containerd' ;; podman) echo 'podman|conmon' ;;
  codex) echo 'codex' ;; opencode) echo 'opencode' ;; goose) echo 'goose' ;;
  aider) echo 'aider' ;; openhands) echo 'openhands' ;; claude) echo 'claude' ;;
  cline) echo 'cline' ;;   # the hub daemon runs as ".cline"
  vllm) echo 'vllm|VLLM::' ;; sglang) echo 'sglang' ;;
  lmstudio) echo 'llmster|LM Studio|lmstudio' ;; searxng) echo 'searxng' ;;
  mcp-inspector) echo 'mcp-inspector' ;;   # runs as "node": found by its ports
  *) echo '' ;;
  esac
}
# extra TOOL: findings that are neither paths nor processes
extra() {
  case $1 in
  vllm) local d=${VLLM_RPC_BASE_PATH:-$T} n
    n=$(find "$d" -maxdepth 1 -type s -name '????????-????-????-????-????????????' \
          2>/dev/null | wc -l | tr -d ' ')
    [ "$n" -gt 0 ] && echo "  file  $n ZeroMQ socket files of past runs in $(short "$d")" ;;
  claude) local d n   # one Unix socket per process; some outlive theirs
    for d in ${XDG_RUNTIME_DIR:+"$XDG_RUNTIME_DIR/cc-socks"} /tmp/cc-socks; do
      n=$(find "$d" -maxdepth 1 -type s 2>/dev/null | wc -l | tr -d ' ')
      [ "$n" -gt 0 ] && echo "  file  $n session sockets in $d"; done ;;
  lmstudio) for f in .profile .zshrc .bashrc .bash_profile; do
      grep -q 'Added by LM Studio CLI tool' "$HOME/$f" 2>/dev/null &&
        echo "  prof  ~/$f (PATH line of lms)"; done ;;
  sglang|searxng) command -v docker >/dev/null 2>&1 &&
      docker image ls --format '{{.Repository}}:{{.Tag}} {{.Size}}' 2>/dev/null |
      grep -E "$( [ "$1" = sglang ] && echo 'lmsysorg/sglang' || echo 'searxng/searxng')" |
      sed 's/^/  image /' ;;
  esac
  return 0
}
# well-known listening ports, matched whatever the owning process
ports() {
  case $1 in llama.cpp) echo '9931|8080' ;; ollama) echo '11434' ;;
  vllm) echo '8000' ;; sglang) echo '30000' ;; lmstudio) echo '1234|41343' ;;
  searxng) echo '8888' ;; cline) echo "${CLINE_HUB_PORT:-25463}" ;;
  # web page and API, MCP Apps sandbox, app origin (web mode only)
  mcp-inspector) local a=${CLIENT_PORT:-6274} b=${MCP_SANDBOX_PORT:-6275}
    echo "$a|$b|${MCP_APP_ORIGIN_PORT:-6278}" ;;
  *) echo '' ;; esac
}
DUC=$( [ "$OS" = Darwin ] && getconf DARWIN_USER_CACHE_DIR )
short() { local p=$1
  case $p in "$DUC"?*) [ -n "$DUC" ] && p="\$DARWIN_USER_CACHE_DIR/${p#"$DUC"}" ;; esac
  case $p in "$HOME"/*) p="~${p#"$HOME"}" ;; esac
  printf '%s' "$p"; }
size() { if [ -d "$1" ] && ! { [ -r "$1" ] && [ -x "$1" ]; }; then echo root
  else du -sh "$1" 2>/dev/null | cut -f1; fi; }
mode() { if [ "$OS" = Darwin ]; then stat -f %Lp "$1"; else stat -c %a "$1"; fi; }

for t in $TOOLS; do
  printf '== %s\n' "$t"; mine=""
  while read -r kind p; do
    [ -e "$p" ] || [ -L "$p" ] || continue
    case $kind in
    cred) printf '  cred  %-6s %s (present; contents not read)\n' \
            "$(mode "$p")" "$(short "$p")" ;;
    sys)  printf '  sys   %-6s %s\n' "$(size "$p" || echo '?')" "$p" ;;
    *)    printf '  dir   %-6s %s\n' "$(size "$p")" "$(short "$p")"
          mine="$mine$p"$'\n' ;;
    esac
  done < <(paths "$t" | awk '!seen[$0]++')
  pat=$(pattern "$t"); pp=$(ports "$t")
  if [ -n "$pat" ]; then
    ps -axo pid=,comm= 2>/dev/null | awk -v p="$pat" '$0 ~ p' |
      grep -v -E 'inventory|grep|awk' | while read -r pid comm; do
        printf '  proc  %-6s %s\n' "$pid" "${comm##*/}"; done
    if [ "$OS" = Darwin ]; then
      lsof -nP -iTCP -sTCP:LISTEN 2>/dev/null | awk -v p="$pat" -v q=":(${pp:-none})\$" \
        'NR > 1 && (tolower($1) ~ p || $9 ~ q) { print "  port  " $9 " (" $1 ")" }' | sort -u
      launchctl list 2>/dev/null | awk -v p="$pat" '$3 ~ p { print "  svc   launchd " $3 }'
      for d in "$HOME/Library/LaunchAgents" /Library/LaunchAgents /Library/LaunchDaemons; do
        ls "$d" 2>/dev/null | grep -iE "$pat" | sed "s#^#  svc   $(short "$d")/#"
      done
    else
      ss -ltnpH 2>/dev/null | awk -v p="$pat" -v q=":(${pp:-none})\$" \
        '$0 ~ p || $4 ~ q { print "  port  " $4 }' | sort -u
      for scope in --system --user; do
        systemctl $scope list-unit-files --no-legend 2>/dev/null | awk -v p="$pat" \
          -v s="${scope#--}" '$1 ~ p { if ($2 ~ /^(enabled|linked|alias)/)
            print "  svc   " s " " $1 " " $2; else n++ }
          END { if (n) print "  svc   " s ": " n " more unit files, not enabled" }'
        systemctl $scope list-units --no-legend --state=active 2>/dev/null |
          awk -v p="$pat" -v s="${scope#--}" '$1 ~ p { print "  svc   " s " " $1 " active" }'
      done
      getent passwd 2>/dev/null | awk -F: -v p="$pat" \
        '$1 ~ p { print "  user  " $1 " (uid " $3 ", home " $6 ")" }'
    fi
  fi
  extra "$t"
  if [ "$REMOVE" = 1 ] && [ -n "$mine" ]; then
    while IFS= read -r p; do
      [ -n "$p" ] || continue
      printf 'delete %s ? [y/N] ' "$(short "$p")"; read -r a < /dev/tty
      [ "$a" = y ] && rm -rf -- "$p" && echo "  deleted"
    done <<< "$mine"
  fi
done
