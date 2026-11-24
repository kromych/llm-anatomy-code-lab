# events.py -- count the kinds of stream events of the Responses API in
# OpenAI's OpenAPI specification (openapi.json from
# https://github.com/openai/openai-openapi).
# Usage: python3 events.py openapi.json   (standard library only)
import hashlib, json, sys

raw = open(sys.argv[1], "rb").read()
spec = json.loads(raw)
schemas = spec["components"]["schemas"]
names = []
for member in schemas["ResponseStreamEvent"]["anyOf"]:
    kind = schemas[member["$ref"].split("/")[-1]]["properties"]["type"]
    names.append(kind["const"] if "const" in kind else kind["enum"][0])
print("file: %d bytes, sha256 %s" % (len(raw),
                                     hashlib.sha256(raw).hexdigest()))
print("info.version:", spec["info"]["version"])
for name in sorted(names):
    print(name)
print(len(names), "kinds of stream events")
