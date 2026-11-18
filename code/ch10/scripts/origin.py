# origin.py -- who may connect to a server: does it answer a request
# without a key, with a key, and with the Origin header that a browser
# adds to a request made by a web page?
# Usage: python3 origin.py ROOT_URL [KEY]   (standard library only)
import sys, urllib.request, urllib.error

ROOT = sys.argv[1]
KEY = sys.argv[2] if len(sys.argv) > 2 else None
CASES = [("no key, no origin", {}),
         ("foreign origin", {"Origin": "http://example.com"})]
if KEY:
    CASES.append(("with the key", {"Authorization": "Bearer " + KEY}))

for path in ("/v1/models", "/health"):
    for label, headers in CASES:
        req = urllib.request.Request(ROOT + path, headers=headers)
        try:
            resp = urllib.request.urlopen(req, timeout=30)
        except urllib.error.HTTPError as e:
            resp = e
        except OSError as e:
            print("%-11s %-18s no connection (%s)" % (path, label, e))
            continue
        allow = resp.headers.get("Access-Control-Allow-Origin")
        print("%-11s %-18s status %d, Access-Control-Allow-Origin=%s"
              % (path, label, resp.status, allow))
