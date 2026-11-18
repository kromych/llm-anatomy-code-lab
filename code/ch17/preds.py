# preds.py -- one line of a SWE-bench predictions file from a diff on the
# standard input. The label names the directory of the harness's logs.
# usage: git diff BASE_COMMIT | python3 preds.py INSTANCE_ID LABEL
import json, sys

instance, label = sys.argv[1:3]
print(json.dumps({"instance_id": instance, "model_name_or_path": label,
                  "model_patch": sys.stdin.read()}))
