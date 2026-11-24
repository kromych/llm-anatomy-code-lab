#!/bin/bash
# requests_probe.sh -- inside the instance image of psf__requests-2317: the
# certificates that the client trusts, the chain that httpbin.org presents
# today, and the service's replies to requests of the kind the tests make.
# usage: docker run --rm -v $PWD/requests_probe.sh:/probe.sh:ro \
#          swebench/sweb.eval.x86_64.psf_1776_requests-2317 bash /probe.sh
source /opt/miniconda3/bin/activate
conda activate testbed
cd /testbed
set -x
head -2 /etc/os-release
python --version
python -c "import ssl; print(ssl.OPENSSL_VERSION)"
python -c "import requests, requests.certs as c; print(requests.__version__, c.where())"
git log -2 --format="%h %ad %s" --date=short
grep -c "BEGIN CERTIFICATE" requests/cacert.pem
grep -c -i "ISRG\|Internet Security Research" requests/cacert.pem
grep -c "BEGIN CERTIFICATE" /etc/ssl/certs/ca-certificates.crt
ls /usr/share/ca-certificates/mozilla | grep -i isrg
getent ahosts httpbin.org | grep STREAM
cat /proc/sys/net/ipv4/tcp_syn_retries
echo | openssl s_client -connect httpbin.org:443 -servername httpbin.org \
    2>/dev/null | sed -n "/Certificate chain/,/---/p"
python - <<"PY"
import requests

for verify in (True, "/etc/ssl/certs/ca-certificates.crt"):
    try:
        r = requests.get("https://httpbin.org/get", verify=verify)
        print("verify =", verify, "->", r.status_code)
    except Exception as e:
        print("verify =", verify, "->", type(e).__name__, e)
r = requests.get("http://httpbin.org/redirect-to",
                 params={"url": "http://www.google.co.uk"},
                 auth=("user", "pass"))
print("redirect-to:", r.status_code, [h.status_code for h in r.history])
print(r.text)
PY
python - <<"PY"
import socket, time

address = socket.gethostbyname("httpbin.org")
start = time.time()
try:
    socket.create_connection((address, 1))
    print("port 1 of", address, "-> connected")
except OSError as e:
    print("port 1 of", address, "->", type(e).__name__, e,
          "after %.1f s" % (time.time() - start))
PY
