# imgtokens.py -- the positions an image costs in the prompt of a vision
# model: prompt tokens of one text part, alone and after an image
#   python3 imgtokens.py BASE [WIDTH HEIGHT]     (default 512 by 512)
import base64, json, struct, sys, urllib.request, zlib

def png(w, h):
    """A w-by-h RGB picture, a gradient of colors, as a PNG file."""
    def chunk(kind, data):
        body = kind + data
        return (struct.pack(">I", len(data)) + body
                + struct.pack(">I", zlib.crc32(body)))
    rows = b"".join(
        b"\0" + bytes(c for x in range(w)
                      for c in (x * 255 // w, y * 255 // h, 128))
        for y in range(h))
    head = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)   # 8-bit RGB
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", head)
            + chunk(b"IDAT", zlib.compress(rows)) + chunk(b"IEND", b""))

def prompt_tokens(base, content):
    body = {"messages": [{"role": "user", "content": content}],
            "max_tokens": 1}
    req = urllib.request.Request(base + "/chat/completions",
                                 json.dumps(body).encode("utf-8"),
                                 {"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as resp:
        return json.load(resp)["usage"]["prompt_tokens"]

base = sys.argv[1]
w, h = (int(a) for a in sys.argv[2:4]) if len(sys.argv) > 3 else (512, 512)
text = {"type": "text", "text": "Describe the picture."}
url = "data:image/png;base64," + base64.b64encode(png(w, h)).decode()
image = {"type": "image_url", "image_url": {"url": url}}
alone = prompt_tokens(base, [text])
both = prompt_tokens(base, [image, text])
print(f"text alone {alone}, {w}x{h} image and text {both}: "
      f"the image costs {both - alone} positions")
