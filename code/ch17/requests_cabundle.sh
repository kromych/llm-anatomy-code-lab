#!/bin/bash
# requests_cabundle.sh -- inside the instance image of psf__requests-2317:
# the gold patch and the harness's script eval.sh, after the certificate
# file of the repository (2014) has been replaced by that of the image's
# operating system, and with pytest reporting its slowest tests.
# usage: docker run --rm -v $PWD/requests_cabundle.sh:/run.sh:ro \
#          -v LOGDIR/patch.diff:/patch.diff:ro -v LOGDIR/eval.sh:/eval.sh:ro \
#          swebench/sweb.eval.x86_64.psf_1776_requests-2317 bash /run.sh
# (LOGDIR: logs/run_evaluation/gold/gold/psf__requests-2317 of a gold run)
cd /testbed
git apply -v /patch.diff
cp /etc/ssl/certs/ca-certificates.crt requests/cacert.pem
git update-index --assume-unchanged requests/cacert.pem
sed 's/^pytest -rA /pytest -rA --durations=8 /' /eval.sh > /tmp/eval.sh
grep -n "^pytest" /tmp/eval.sh
bash /tmp/eval.sh
