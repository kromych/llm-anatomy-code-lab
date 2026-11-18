#!/bin/sh
# record_sdk.sh PY2 PY1: the runs of Chapter 13 against the official SDK.
# PY2 is the Python of an environment with mcp 2.3.0, PY1 that of one with
# mcp 1.30.0 (pip install "mcp==2.3.0" and "mcp==1.30.0" in two virtual
# environments).  Writes, under results/,
#   sdk_client_test.txt    the SDK's Client in three modes, our server
#   mcp_client-sdk.txt     our client with the servers of both SDKs
#   sdk1-tap.log           the probe that SDK 1.30.0 refuses (tap.py)
#   sdk-tap-auto.log, sdk-tap-legacy.log   the SDK's Client, our server
#   sdk_http_client.txt    the SDK's Client and http_server.py (port 8765)
#   close_test.txt         four requests, then the input closes
set -e
cd "$(dirname "$0")"
PY2=$1; PY1=$2

"$PY2" sdk_client_test.py > results/sdk_client_test.txt 2>&1
{
    echo "## python3 mcp_client.py PY2 sdk_server.py sample"
    python3 mcp_client.py "$PY2" sdk_server.py sample
    echo
    echo "## python3 mcp_client.py python3 tap.py results/sdk1-tap.log" \
         "PY1 sdk1_server.py sample"
    python3 mcp_client.py python3 tap.py results/sdk1-tap.log \
        "$PY1" sdk1_server.py sample
} > results/mcp_client-sdk.txt 2>&1
"$PY2" sdk_tap.py auto
"$PY2" sdk_tap.py legacy

python3 http_server.py sample 8765 & pid=$!
sleep 1
"$PY2" sdk_http_client.py http://127.0.0.1:8765/mcp \
    > results/sdk_http_client.txt 2>&1 || true
kill $pid; wait $pid 2>/dev/null || true

{
    echo "## python3 close_test.py 3 python3 files_server.py sample"
    python3 close_test.py 3 python3 files_server.py sample
    echo
    echo "## python3 close_test.py 3 PY2 sdk_server.py sample"
    python3 close_test.py 3 "$PY2" sdk_server.py sample
} > results/close_test.txt 2>&1
echo recorded
