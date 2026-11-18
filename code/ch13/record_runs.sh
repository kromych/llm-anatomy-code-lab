#!/bin/sh
# record_runs.sh: the loopback runs of Chapter 13 that need no model.
#   results/confirm-tap.log     a request for input, as tap.py saw it
#   results/confirm-client.txt  the same call answered y, n, and q
#   results/http-curl.txt       three POSTs to http_server.py (port 8765)
#   results/auth-curl.txt       auth_server.py (port 8766) with and
#                               without a token
set -e
cd "$(dirname "$0")"
U=http://127.0.0.1:8765/mcp
A=http://127.0.0.1:8766

echo y | python3 confirm_client.py garden.py \
    python3 tap.py results/confirm-tap.log \
    python3 confirm_server.py sample > /dev/null 2>&1
for reply in y n q; do
    echo "## echo $reply | python3 confirm_client.py garden.py" \
         "python3 confirm_server.py sample"
    echo $reply | python3 confirm_client.py garden.py \
        python3 confirm_server.py sample 2>&1
    echo
done > results/confirm-client.txt

post() {                # post NAME URL [more curl options]
    name=$1; url=$2; shift 2
    curl -s -i -d "@call.json" -H "Content-Type: application/json" \
        -H "Accept: application/json, text/event-stream" \
        -H "MCP-Protocol-Version: 2026-07-28" \
        -H "Mcp-Method: tools/call" -H "Mcp-Name: $name" "$@" "$url"
    echo; echo
}

python3 http_server.py sample 8765 & pid=$!
sleep 1
{
    echo "## Mcp-Name: read_file (the headers agree with call.json)"
    post read_file $U
    echo "## Mcp-Name: list_files (the header contradicts the body)"
    post list_files $U
    echo "## Mcp-Name: read_file, Origin: http://evil.example"
    post read_file $U -H "Origin: http://evil.example"
} | tr -d '\r' > results/http-curl.txt
kill $pid; wait $pid 2>/dev/null || true

MCP_TOKEN=demo-token python3 auth_server.py sample 8766 & pid=$!
sleep 1
{
    echo "## POST without a token"
    post read_file $A/mcp
    echo "## GET of the protected resource metadata"
    curl -s -i $A/.well-known/oauth-protected-resource/mcp
    echo; echo
    echo "## POST with a wrong token"
    post read_file $A/mcp -H "Authorization: Bearer wrong"
    echo "## POST with the token of MCP_TOKEN"
    post read_file $A/mcp -H "Authorization: Bearer demo-token"
} | tr -d '\r' > results/auth-curl.txt
kill $pid; wait $pid 2>/dev/null || true
echo recorded
