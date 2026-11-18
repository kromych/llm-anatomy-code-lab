# child_env.py -- the environment that step W3 hands to a command, the
# answer to an exercise of Chapter 16: an allowlist, then a filter on names.
import re

KEEP = {"PATH", "HOME", "USER", "LOGNAME", "SHELL", "LANG", "LC_ALL",
        "LC_CTYPE", "TERM", "TZ", "TMPDIR"}
SECRET = re.compile(r"KEY|SECRET|TOKEN|PASS|CRED|AUTH|COOKIE", re.I)

def child_env(env, proxy=None):
    out = {k: v for k, v in env.items()
           if k in KEEP and not SECRET.search(k)}
    if proxy:
        for k in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY"):
            out[k] = out[k.lower()] = proxy
    return out

env = {"PATH": "/usr/bin:/bin", "HOME": "/home/u", "TERM": "xterm",
       "OPENAI_API_KEY": "dummy", "GITHUB_TOKEN": "dummy",
       "DATABASE_URL": "postgres://u:dummy@db/x", "SSH_AUTH_SOCK": "/s"}
assert child_env(env) == {"PATH": "/usr/bin:/bin", "HOME": "/home/u",
                          "TERM": "xterm"}

if __name__ == "__main__":
    print("kept:", sorted(child_env(env)))
    print("with a proxy:", sorted(child_env(env, "http://127.0.0.1:3128")))
    for pattern in ("KEY|SECRET|TOKEN", SECRET.pattern):
        missed = [k for k in ("DATABASE_URL", "KUBECONFIG",
                              "GOOGLE_APPLICATION_CREDENTIALS",
                              "SSH_AUTH_SOCK")
                  if not re.search(pattern, k, re.I)]
        print("a filter on", pattern, "misses", missed)
