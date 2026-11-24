"""Write diff-*.txt files comparing two snapshot directories.

usage: python3 -I mkdiff.py <before_dir> <after_dir> <out_dir> <label>
Lines starting with '[' at column 0 are section headers; diffs are per section.
"""
import re
import sys
from pathlib import Path

before, after, outdir, label = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]), sys.argv[4]

FILES = {
    'winget-list.txt': 'winget',
    'uninstall-entries.txt': 'uninstall-entries',
    'services.txt': 'services',
    'scheduled-tasks.txt': 'scheduled-tasks',
    'run-keys.txt': 'run-keys',
    'startup-folders.txt': 'startup-folders',
    'firewall-llm.txt': 'firewall-llm',
    'firewall-all.txt': 'firewall-all',
    'path.txt': 'path',
    'env-names.txt': 'env-names',
    'dirs.txt': 'dirs',
    'listening.txt': 'listening',
    'listening-udp.txt': 'listening-udp',
    'processes.txt': 'processes',
    'registry-toplevel.txt': 'registry-toplevel',
}


def norm(name, line):
    if name.startswith('listening'):
        # drop the pid so that restarted services do not show up as changes
        return re.sub(r'pid=\d+\s*', '', line).strip()
    if name == 'processes.txt':
        return line.strip().lower()
    if name == 'winget-list.txt':
        return re.sub(r'\s+', ' ', line).strip()
    return line.rstrip()


def sections(path, name):
    secs, cur = {}, '(top)'
    order = [cur]
    secs[cur] = []
    for raw in path.read_text(encoding='utf-8', errors='replace').splitlines():
        if raw.startswith('[') and name not in ('winget-list.txt',):
            cur = raw.strip()
            if cur not in secs:
                secs[cur] = []
                order.append(cur)
            continue
        if raw.strip():
            secs[cur].append(norm(name, raw))
    return secs, order


for fname, tag in FILES.items():
    b, a = before / fname, after / fname
    if not (b.exists() and a.exists()):
        continue
    sb, ob = sections(b, fname)
    sa, oa = sections(a, fname)
    out = [f'# {label}: {fname}  (+ added, - removed; unchanged lines omitted)']
    changed = False
    for sec in list(dict.fromkeys(ob + oa)):
        lb, la = sb.get(sec, []), sa.get(sec, [])
        setb, seta = set(lb), set(la)
        added = [x for x in la if x not in setb]
        removed = [x for x in lb if x not in seta]
        if sec not in sb:
            out.append(f'+ new section {sec}')
        if sec not in sa:
            out.append(f'- section gone {sec}')
        if added or removed:
            changed = True
            out.append(sec if sec != '(top)' else '')
            out += [f'+ {x}' for x in added]
            out += [f'- {x}' for x in removed]
    if not changed:
        out.append('(no differences)')
    (outdir / f'diff-{tag}.txt').write_text('\n'.join(out) + '\n', encoding='utf-8')
    print(f'{tag}: {"changed" if changed else "same"}')
