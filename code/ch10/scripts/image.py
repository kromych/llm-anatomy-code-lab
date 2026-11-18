# image.py -- send an image to a vision model as a part of a message.
# Builds a small PNG of one color with the standard library, asks for the
# color, and asks again without the image to see how many prompt tokens
# the image took.
# Usage: python3 image.py BASE_URL MODEL [R G B]   (standard library only)
import base64, json, struct, sys, urllib.request, zlib

BASE, MODEL = sys.argv[1], sys.argv[2]
RGB = bytes(int(v) for v in sys.argv[3:6]) or bytes([220, 30, 30])

def png(rgb, side=64):
    """A side x side PNG of one color (8-bit RGB, no interlace)."""
    def chunk(kind, data):
        body = kind + data
        return (struct.pack(">I", len(data)) + body +
                struct.pack(">I", zlib.crc32(body)))
    rows = (b"\x00" + rgb * side) * side      # filter type 0 on each row
    return (b"\x89PNG\r\n\x1a\n" +
            chunk(b"IHDR", struct.pack(">IIBBBBB", side, side, 8, 2,
                                       0, 0, 0)) +
            chunk(b"IDAT", zlib.compress(rows)) + chunk(b"IEND", b""))

def ask(parts):
    body = {"model": MODEL, "temperature": 0, "max_tokens": 20,
            "messages": [{"role": "user", "content": parts}]}
    req = urllib.request.Request(BASE + "/chat/completions",
            json.dumps(body).encode(),
            {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=600) as resp:
        r = json.load(resp)
    return r["choices"][0]["message"]["content"], r["usage"]

image = png(RGB)
url = "data:image/png;base64," + base64.b64encode(image).decode()
text = {"type": "text", "text": "What color is this square? One word."}
print("PNG of %d bytes, data URL of %d characters" % (len(image), len(url)))
for label, parts in (("with the image", [
        {"type": "image_url", "image_url": {"url": url}}, text]),
        ("text alone", [text])):
    answer, usage = ask(parts)
    print("%-15s %r, %d prompt tokens" % (
        label, answer.strip(), usage["prompt_tokens"]))
