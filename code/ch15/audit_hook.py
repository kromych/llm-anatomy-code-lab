# audit_hook.py -- a hook for Codex CLI: append each event that arrives on
# standard input to a log, and deny a command that names a protected file
# together with a sign of writing.
# In hooks.json: "command": "python3 audit_hook.py LOG [PROTECTED...]"
import json, sys, time

LOG, PROTECTED = sys.argv[1], sys.argv[2:]
WRITES = (">", "apply_patch", "sed -i", "tee ", "rm ", "mv ", "write")

event = json.load(sys.stdin)
with open(LOG, "a", encoding="utf-8") as f:
    f.write(json.dumps({"time": round(time.time(), 3), **event}) + "\n")

if event.get("hook_event_name") == "PreToolUse":
    text = json.dumps(event.get("tool_input"))
    for name in PROTECTED:
        if name in text and any(w in text for w in WRITES):
            why = f"{name} is protected by a hook; leave it unchanged."
            print(json.dumps({"hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": why}}))
            break
