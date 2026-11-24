"""auth_server.py: http_server.py as an OAuth protected resource.

  MCP_TOKEN=secret python3 auth_server.py ROOT [PORT]

A POST without the token receives status 401 and, in WWW-Authenticate,
the URL of the protected resource metadata (RFC 9728), which a GET
returns.  The comparison with MCP_TOKEN stands in for the validation of
a token that an authorization server issued; no such server runs here,
and the one that the metadata names (MCP_ISSUER) is an example.
"""
import hmac, os
from http.server import ThreadingHTTPServer
import http_server as hs

BASE = "http://127.0.0.1:%d" % hs.PORT
WELL_KNOWN = "/.well-known/oauth-protected-resource/mcp"
METADATA = {
    "resource": BASE + "/mcp",
    "authorization_servers": [
        os.environ.get("MCP_ISSUER", "https://auth.example.com")],
    "scopes_supported": ["files:read"],
    "bearer_methods_supported": ["header"]}
CHALLENGE = ('Bearer resource_metadata="%s", scope="files:read"'
             % (BASE + WELL_KNOWN))
TOKEN = os.environ.get("MCP_TOKEN")

class Handler(hs.Handler):
    def do_POST(self):
        given = self.headers.get("Authorization")
        if TOKEN and given is not None and hmac.compare_digest(
                given.encode(), b"Bearer " + TOKEN.encode()):
            return super().do_POST()
        challenge = CHALLENGE           # RFC 6750: name the error only
        if given is not None:           # when the request had a token
            challenge += ', error="invalid_token"'
        self.rfile.read(int(self.headers.get("Content-Length") or 0))
        self.send_response(401)
        self.send_header("WWW-Authenticate", challenge)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_GET(self):
        if self.path == WELL_KNOWN:
            return self.reply(200, METADATA)
        self.reply(405)

if __name__ == "__main__":
    ThreadingHTTPServer(("127.0.0.1", hs.PORT), Handler).serve_forever()
