"""mcp_client.py: an MCP client over stdio, standard library only.

  python3 mcp_client.py python3 files_server.py ROOT
starts the server, selects a protocol version (Algorithm I), lists the
tools and calls list_files.
"""
import itertools, json, queue, subprocess, sys, threading

MODERN = ["2026-07-28"]
LEGACY = ["2025-11-25", "2025-06-18", "2025-03-26"]
P = "io.modelcontextprotocol/"
INFO = {"name": "mcp_client.py", "version": "1.0"}

class RpcError(Exception):
    def __init__(self, error):
        super().__init__(error.get("message"))
        self.code, self.data = error.get("code"), error.get("data")

class Connection:
    def __init__(self, argv):
        self.proc = subprocess.Popen(argv, stdin=subprocess.PIPE,
                                     stdout=subprocess.PIPE, text=True)
        self.inbox = queue.Queue()
        threading.Thread(target=self.reader, daemon=True).start()
        self.ids = itertools.count(1)
        self.version, self.legacy = MODERN[0], False
        self.caps = {}                # the capabilities of this client

    def reader(self):                 # one thread reads the server
        for line in self.proc.stdout:
            self.inbox.put(json.loads(line))
        self.inbox.put(None)          # end of file: the server is gone

    def send(self, msg):
        self.proc.stdin.write(json.dumps(msg) + "\n")
        self.proc.stdin.flush()

    def request(self, method, params=None, timeout=30):
        params, rid = dict(params or {}), next(self.ids)
        if not self.legacy:           # every modern request says who
            params["_meta"] = {       # it is and what it can do
                P + "protocolVersion": self.version,
                P + "clientCapabilities": self.caps, P + "clientInfo": INFO}
        self.send({"jsonrpc": "2.0", "id": rid, "method": method,
                   "params": params})
        while True:
            msg = self.inbox.get(timeout=timeout)   # may raise Empty
            if msg is None:
                raise EOFError("the server closed its output")
            if "method" in msg and "id" in msg:     # a server request
                self.send({"jsonrpc": "2.0", "id": msg["id"], "error":
                           {"code": -32601, "message": "not supported"}})
            elif msg.get("id") == rid:
                break                 # skip notifications and the rest
        if "error" in msg:
            raise RpcError(msg["error"])
        return msg["result"]

    def open(self, timeout=5):
        """Algorithm I: select a protocol version for this server."""
        for attempt in range(2):
            try:                                                # I1
                r = self.request("server/discover", timeout=timeout)
            except RpcError as e:
                theirs = []
                if e.code == -32022:                            # I3
                    theirs = (e.data or {}).get("supported", [])
                common = [v for v in MODERN if v in theirs]
                if common and attempt == 0:
                    self.version = common[0]
                    continue
                if theirs and not set(theirs) & set(LEGACY):
                    raise             # modern, but nothing in common
                break
            except queue.Empty:
                break                 # silence: perhaps a legacy server
            theirs = r.get("supportedVersions", [])             # I2
            common = [v for v in MODERN if v in theirs]
            if common:
                self.version = common[0]
                return r
            break
        return self.handshake()       # I4: initialize, then initialized

    def handshake(self):                                        # I4
        self.legacy = True
        r = self.request("initialize", {"protocolVersion": LEGACY[0],
                         "capabilities": {}, "clientInfo": INFO})
        if r["protocolVersion"] not in LEGACY:
            self.close()
            raise RuntimeError("no common protocol version")
        self.version = r["protocolVersion"]
        self.send({"jsonrpc": "2.0",
                   "method": "notifications/initialized"})
        return r

    def close(self):                  # close stdin, then insist
        self.proc.stdin.close()
        try:
            self.proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.proc.terminate()
            self.proc.wait()

if __name__ == "__main__":
    c = Connection(sys.argv[1:])
    c.open()
    print("version", c.version, "legacy" if c.legacy else "modern")
    for t in c.request("tools/list")["tools"]:
        print("tool", t["name"], "-", t.get("description", ""))
    r = c.request("tools/call", {"name": "list_files",
                                 "arguments": {"path": "."}})
    print(r["content"][0]["text"])
    c.close()
