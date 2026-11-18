import json, sys
for name in sys.argv[1:]:
    rows = [json.loads(l) for l in open(name + ".jsonl")]
    t = lambda k: sum(r[k] for r in rows)
    print(f"{name:18s} solved {t('ok')} turns {t('turns'):3d} prompt {t('prompt'):6d} "
          f"cached {t('cached'):6d} completion {t('completion'):5d} s {round(t('seconds'), 1)} "
          f"{[int(r['ok']) for r in rows]}")
