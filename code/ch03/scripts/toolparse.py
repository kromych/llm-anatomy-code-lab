import json

OPEN, CLOSE = "<tool_call>", "</tool_call>"

class ToolCallParser:
    # feed() takes each SSE delta and returns (text, calls) ready so far
    def __init__(self):
        self.buf, self.inside = "", False

    def feed(self, delta):
        self.buf += delta
        text, calls = "", []
        while True:
            tag = CLOSE if self.inside else OPEN
            i = self.buf.find(tag)
            if i < 0:
                break
            if self.inside:
                body = self.buf[:i].strip()
                try:
                    calls.append(json.loads(body))
                except json.JSONDecodeError:
                    text += OPEN + body + CLOSE   # give it back as text
            else:
                text += self.buf[:i]
            self.buf = self.buf[i + len(tag):]
            self.inside = not self.inside
        if not self.inside:                  # keep a possible partial tag
            keep = max((k for k in range(len(OPEN))
                        if self.buf.endswith(OPEN[:k])), default=0)
            text += self.buf[:len(self.buf) - keep]
            self.buf = self.buf[len(self.buf) - keep:]
        return text, calls

    def close(self):
        # end of the stream: an unfinished call or tag goes back as text
        rest = (OPEN if self.inside else "") + self.buf
        self.buf, self.inside = "", False
        return rest, []
