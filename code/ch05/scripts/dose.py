# dose.py MODEL.gguf VECTOR.gguf [PORT] -- how much steering, and where:
# starts llama-server with a control vector at several weights, and then
# on several ranges of layers, and prints for each start the probability
# of the first token and the greedy continuation of one prompt. First it
# checks that the GGUF file holds the model of forward.py.
import contextlib, json, math, subprocess, sys, time, urllib.request

MODEL, VECTOR = sys.argv[1], sys.argv[2]
PORT = int(sys.argv[3]) if len(sys.argv) > 3 else 8105
BASE = f"http://127.0.0.1:{PORT}"
PROMPT = "The movie was"
KNOWN = [504, 3575, 282, 4649, 314]      # the prompt of forward.py and
EIGHT = [260, 3575, 282, 260, 1798, 30, 198, 198]    # what follows it

def post(path, body):
    req = urllib.request.Request(BASE + path, json.dumps(body).encode(),
                                 {"Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(req))

@contextlib.contextmanager
def server(options):
    child = subprocess.Popen(
        ["llama-server", "-m", MODEL, "--host", "127.0.0.1", "--port",
         str(PORT)] + options,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        while True:
            try:
                urllib.request.urlopen(BASE + "/health").close()
                break
            except OSError:              # no listener yet, or status 503
                assert child.poll() is None, "the server has exited"
                time.sleep(0.05)
        yield
    finally:
        child.terminate()
        child.wait()

def show(label, weight, layers=None):
    options = ["--control-vector-scaled", f"{VECTOR}:{weight}"]
    if layers:
        options += ["--control-vector-layer-range", *map(str, layers)]
    with server(options if weight else []):
        ids = post("/tokenize", {"content": PROMPT})["tokens"]
        r = post("/completion", {"prompt": ids, "n_predict": 10,
                                 "temperature": 0, "n_probs": 1})
    p = math.exp(r["completion_probabilities"][0]["logprob"])
    print(f"  {label:10} {p:.3f}  {r['content'][:54]!r}")

with server([]):
    r = post("/completion", {"prompt": KNOWN, "n_predict": 8,
                             "temperature": 0, "return_tokens": True})
print("the file continues the prompt of forward.py as forward.py does:",
      r["tokens"] == EIGHT)
print(f"the continuation of {PROMPT!r}, by the weight of the vector:")
for w in (0, 0.5, 1, 2, -1):
    show(f"{w:+g}", w)
print("on some of the layers, by the layers and the weight:")
for lo, hi, w in ((1, 9, 1), (10, 19, 1), (20, 29, 1), (10, 19, -1)):
    show(f"{lo}-{hi} {w:+g}", w, (lo, hi))
