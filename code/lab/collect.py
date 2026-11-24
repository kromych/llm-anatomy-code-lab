"""collect.py <pulled out dir> <dest host dir>: copy small per-run files and extract features.txt."""
import pathlib, re, shutil, sys
src, dst = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2]) / 'raw'
dst.mkdir(parents=True, exist_ok=True)
def text(p):
    return p.read_text(encoding='utf-8-sig', errors='replace') if p.exists() else ''
labels = sorted({p.name.split('.')[0] for p in src.glob('*.csv')} | {p.name.split('.')[0] for p in src.glob('*.env')})
for label in labels:
    for p in src.glob(f'{label}.*'):
        if p.suffix in ('.csv', '.md', '.env', '.interference', '.done'):
            name = p.name
            if p.suffix == '.interference':
                name = p.name.replace('.interference', '.sampler.txt')
            out = text(p).replace('\r\n', '\n')
            (dst / name).write_text(out)
    for tl in sorted({p.name[len(label):].split('.')[1] for p in src.glob(f'{label}.*')}):
        pass
    feats = []
    for kind in ('completion.log', 'stderr'):
        for p in sorted(src.glob(f'{label}*.{kind}')):
            for line in text(p).splitlines():
                if re.search(r'load_backend|system_info|^build:|CPU_REPACK|REPACK model buffer|ggml_vulkan: \d|Vulkan\d|using device|AMD|Apple|offloaded|error|illegal|Illegal', line) and not line.startswith('|'):
                    feats.append(f'[{p.name}] {line.strip()}')
    (dst / f'{label}.features.txt').write_text('\n'.join(dict.fromkeys(feats)) + '\n')
print(len(labels), 'labels ->', dst)
