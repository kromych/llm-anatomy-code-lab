"""Count what one request of a run holds: the system and developer texts
in the order sent, the list of skills inside them, and the tools.

usage: python3 interior.py DUMPDIR TAG[:N]...

DUMPDIR is the directory of request bodies that proxy.py or
proxy_messages.py keeps. For every tag the program takes the first
request that offers tools, or request N. A text sent in several parts is
shown with the sizes of the parts. A list of skills is recognized in the
forms that the harnesses of Chapter 15 use: the element
<available_skills> with its tags (opencode), and the lines "- name: text"
after "### Available skills" (Codex), after "asks for it:" (Goose), or
after "with the Skill tool:" (Claude Code). All sizes are in characters."""
import glob, json, re, sys, textwrap

ITEM = r"(?m)^- [\w:-]+: "
LISTS = [  # where a list starts and ends, an entry, markers counted or not
    ("<available_skills>", "</available_skills>", r"<skill>", True),
    ("### Available skills\n", "</skills_instructions>", ITEM, False),
    ("the user asks for it:\n", "\n\n", ITEM, False),
    ("with the Skill tool:\n\n", "\n\n", ITEM, False)]

def parts_of(content):
    if isinstance(content, list):
        return [p.get("text", "") for p in content if isinstance(p, dict)]
    return [content or ""]

def texts(q):
    """(place, parts) of every system or developer text, in order."""
    found = []
    if q.get("instructions"):
        found.append(("instructions", [q["instructions"]]))
    if q.get("system"):                       # Messages API
        found.append(("system field", parts_of(q["system"])))
    items = q.get("messages") or q.get("input") or []
    for m in items if isinstance(items, list) else []:
        if m.get("role") in ("system", "developer"):
            found.append((m["role"], parts_of(m.get("content"))))
    return found

def skills(text):
    """(before, entries, size, after) for the first list found."""
    for start, end, item, whole in LISTS:
        i = text.find(start)
        j = text.find(end, i + len(start))
        if i < 0 or j < 0:
            continue
        if whole:
            j += len(end)
        else:
            i += len(start)
        n = len(re.findall(item, text[i:j]))
        if n:
            return i, n, j - i, len(text) - j
    return None

for arg in sys.argv[2:]:
    tag, _, n = arg.partition(":")
    files = sorted(glob.glob("%s/%s-[0-9][0-9].json" % (sys.argv[1], tag)))
    bodies = [(f, json.load(open(f))) for f in files]
    if n:
        f, q = bodies[int(n) - 1]
    else:
        f, q = next((b for b in bodies if b[1].get("tools")), bodies[0])
    names = [t.get("function", t).get("name") or t.get("type")
             for t in q.get("tools") or []]
    print("%s, request %d: %d tools" % (tag, int(f[-7:-5]), len(names)))
    print(textwrap.fill("tools: " + " ".join(names), 76,
                        initial_indent="  ", subsequent_indent="    "))
    total = 0
    for place, parts in texts(q):
        size = sum(len(p) for p in parts)
        total += size
        line = "  %s %d" % (place, size)
        if len(parts) > 1:
            line += " (%s)" % " + ".join(str(len(p)) for p in parts)
        found = skills("".join(parts))
        if found:
            line += ": %d before the skills, %d skills in %d, %d after" \
                    % found
        print(line)
    print("  in all %d" % total)
