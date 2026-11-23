"""Collect lab/bench/isa/<host>/raw/<label>.csv (llama-bench -o csv) into results.csv and summary.md."""
import csv, pathlib, re, sys
ROOT = pathlib.Path(sys.argv[1])
HOSTS = {
    'xps-8930': dict(os='Fedora 44 (Linux 7.2.11)', cpu='Intel Core i7-8700 (6C/12T)', cc='GCC 16.2.1',
                     base='x64', order=['x64', 'sse42', 'avx', 'avx2', 'native', 'dl']),
    'krom2': dict(os='Fedora Asahi Remix 44 (Linux 7.2.12, 16K pages)', cpu='Apple M2 (4P+4E)', cc='GCC 16.2.1',
                  base='armv8a', order=['armv8a', 'dotprod', 'i8mm', 'native', 'vulkan']),
    'kromyrzen': dict(os='Windows 11 Pro N for Workstations 26H2 (10.0.26300)', cpu='AMD Ryzen 7 3700X (8C/16T)',
                      cc='Clang 20.1.8 (official release zip)', base='x64',
                      order=['x64', 'sse42', 'sandybridge', 'ivybridge', 'piledriver', 'haswell']),
    'krom1u': dict(os='macOS 27.2', cpu='Apple M1 Ultra (16P+4E)', cc='Apple clang 21.0.0',
                   base='src-armv8a', order=['src-armv8a', 'src-dotprod', 'src-native', 'brew-cpu', 'brew-metal']),
    'kr0m-gpu': dict(os='Ubuntu 24.04.3 (Linux 6.14.0)', cpu='2 x AMD EPYC 9554 (252 virtual CPUs)', cc='GCC 13.3.0',
                     base='x64', order=['x64', 'sse42', 'avx', 'avx2', 'avx512', 'icelake', 'zen4', 'native', 'dl',
                                        'cuda']),
}
VARIANT = {
    ('xps-8930', 'x64'): ('baseline: x86-64 (SSE2 only)', 'CPU'),
    ('xps-8930', 'sse42'): ('SSE4.2', 'CPU'),
    ('xps-8930', 'avx'): ('SSE4.2+AVX', 'CPU'),
    ('xps-8930', 'avx2'): ('AVX2+FMA+F16C+BMI2', 'CPU'),
    ('xps-8930', 'native'): ('native (-march=native)', 'CPU'),
    ('xps-8930', 'dl'): ('dispatch (BACKEND_DL+ALL_VARIANTS) -> {loaded}', 'CPU'),
    ('krom2', 'armv8a'): ('baseline: armv8-a (NEON)', 'CPU'),
    ('krom2', 'dotprod'): ('armv8.2-a+dotprod', 'CPU'),
    ('krom2', 'i8mm'): ('armv8.2-a+dotprod+i8mm', 'CPU'),
    ('krom2', 'native'): ('native (-mcpu=apple-m2+...+fp16+dotprod+i8mm)', 'CPU'),
    ('krom2', 'vulkan'): ('native CPU build + Vulkan (Asahi), all layers on GPU', 'Vulkan'),
    ('kromyrzen', 'x64'): ('baseline: ggml-cpu-x64.dll (SSE2)', 'CPU'),
    ('kromyrzen', 'sse42'): ('ggml-cpu-sse42.dll', 'CPU'),
    ('kromyrzen', 'sandybridge'): ('ggml-cpu-sandybridge.dll (AVX)', 'CPU'),
    ('kromyrzen', 'ivybridge'): ('ggml-cpu-ivybridge.dll (AVX+F16C)', 'CPU'),
    ('kromyrzen', 'piledriver'): ('ggml-cpu-piledriver.dll (AVX+F16C+FMA)', 'CPU'),
    ('kromyrzen', 'haswell'): ('ggml-cpu-haswell.dll (AVX2+FMA+F16C+BMI2; default)', 'CPU'),
    ('krom1u', 'src-armv8a'): ('baseline: armv8-a (NEON), source build', 'CPU'),
    ('krom1u', 'src-dotprod'): ('armv8.2-a+dotprod, source build', 'CPU'),
    ('krom1u', 'src-native'): ('native (-mcpu=native), source build', 'CPU'),
    ('krom1u', 'brew-cpu'): ('Homebrew: ggml-cpu-apple_m1 + Accelerate BLAS, -dev none', 'CPU+BLAS'),
    ('krom1u', 'brew-metal'): ('Homebrew: Metal, all layers on GPU', 'Metal'),
    ('kr0m-gpu', 'x64'): ('baseline: x86-64 (SSE2 only)', 'CPU'),
    ('kr0m-gpu', 'sse42'): ('SSE4.2', 'CPU'),
    ('kr0m-gpu', 'avx'): ('SSE4.2+AVX', 'CPU'),
    ('kr0m-gpu', 'avx2'): ('AVX2+FMA+F16C+BMI2', 'CPU'),
    ('kr0m-gpu', 'avx512'): ('AVX-512 (F, CD, BW, DQ, VL)', 'CPU'),
    ('kr0m-gpu', 'icelake'): ('AVX-512 with VBMI and VNNI', 'CPU'),
    ('kr0m-gpu', 'zen4'): ('AVX-512 with VBMI, VNNI, and BF16', 'CPU'),
    ('kr0m-gpu', 'native'): ('native (-march=native)', 'CPU'),
    ('kr0m-gpu', 'dl'): ('dispatch (BACKEND_DL+ALL_VARIANTS) -> {loaded}', 'CPU'),
    ('kr0m-gpu', 'cuda'): ('CUDA, all layers on one H100 PCIe', 'CUDA'),
}
BUILDNO = {'61dbf4922': '12376', 'b1b770d90': '12359'}
QUANTS = ['Q4_0', 'Q8_0', 'Q4_K_M']

def quant(model_type):
    if 'Q4_K' in model_type:
        return 'Q4_K_M'
    return re.search(r'(Q\d_\d)', model_type).group(1)

rows = []
for host, h in HOSTS.items():
    raw = ROOT / host / 'raw'
    if not raw.is_dir():
        continue
    for f in sorted(raw.glob('*.csv')):
        if '.try' in f.name:
            continue
        label = f.stem                       # e.g. native-t6
        key, threads_label = label.rsplit('-t', 1)
        name, backend = VARIANT[(host, key)]
        loaded = ''
        feat = raw / f'{label}.features.txt'
        if feat.exists():
            m = re.search(r'ggml-cpu-([\w.]+?)\.(?:so|dll|dylib)', feat.read_text())
            loaded = m.group(1) if m else ''
        name = name.replace('{loaded}', loaded or '?')
        agg = {}
        for r in csv.DictReader(f.open()):
            q, rep = quant(r['model_type']), r.get('repack', '1')
            rep = '1' if rep.lower() in ('1', 'true') else '0'
            k = (q, rep, r['n_threads'])
            a = agg.setdefault(k, dict(date=r['test_time'], commit=r['build_commit']))
            t = 'pp' if int(r['n_prompt']) > 0 else 'tg'
            a[t] = float(r['avg_ts']); a[t + '_sd'] = float(r['stddev_ts'])
        for (q, rep, thr), a in agg.items():
            rows.append(dict(host=host, os=h['os'], cpu=h['cpu'], isa_variant=name, backend=backend,
                             model_quant=q, threads=thr, pp512_tps=a.get('pp'), pp512_sd=a.get('pp_sd'),
                             tg128_tps=a.get('tg'), tg128_sd=a.get('tg_sd'), repack=rep,
                             build=f"{a['commit']} (b{BUILDNO.get(a['commit'], '?')}), {h['cc']}",
                             date=a['date'], _key=key))

cols = ['host', 'os', 'cpu', 'isa_variant', 'backend', 'model_quant', 'threads', 'pp512_tps', 'pp512_sd',
        'tg128_tps', 'tg128_sd', 'repack', 'build', 'date']
order = lambda r: (list(HOSTS).index(r['host']), int(r['threads']), HOSTS[r['host']]['order'].index(r['_key']),
                   r['repack'] == '0', QUANTS.index(r['model_quant']))
rows.sort(key=order)
with open(ROOT / 'results.csv', 'w', newline='') as fh:
    w = csv.DictWriter(fh, fieldnames=cols, extrasaction='ignore')
    w.writeheader()
    for r in rows:
        w.writerow({k: (f'{v:.2f}' if isinstance(v, float) else v) for k, v in r.items()})

def cell(r, t, base):
    v, sd = r[f'{t}_tps'], r[f'{t}_sd']
    if v is None:
        return 'n/a'
    s = f'{v:.1f} ± {sd:.1f}'
    if base and base.get(f'{t}_tps'):
        s += f' ({v / base[f"{t}_tps"]:.2f}×)'
    return s

out = ['# ISA variants of llama.cpp: prompt processing vs token generation', '',
       'Gemma 3 1B instruct (bartowski/google_gemma-3-1b-it-GGUF @ 116f762), `llama-bench -p 512 -n 128 -r 5`.',
       'Cells: tokens/s, mean ± standard deviation of 5 repetitions, and in brackets the speed-up relative to the',
       "host's baseline variant (same threads, same quantization, repacking on). pp512 = prompt processing of",
       '512 tokens; tg128 = generation of 128 tokens. Raw tables, logs and per-host notes are in the host directories.', '']
for host, h in HOSTS.items():
    hr = [r for r in rows if r['host'] == host]
    if not hr:
        continue
    out += [f'## {host}: {h["cpu"]}, {h["os"]}', '']
    for thr in sorted({r['threads'] for r in hr}, key=int):
        tr = [r for r in hr if r['threads'] == thr and r['repack'] == '1']
        base = {r['model_quant']: r for r in tr if r['_key'] == h['base']}
        out += [f'### {thr} threads', '',
                '| variant | backend | ' + ' | '.join(f'{q} pp512 | {q} tg128' for q in QUANTS) + ' |',
                '|---|---|' + '---:|' * (2 * len(QUANTS))]
        for key in h['order']:
            vr = {r['model_quant']: r for r in tr if r['_key'] == key}
            if not vr:
                continue
            any_r = next(iter(vr.values()))
            cells = []
            for q in QUANTS:
                r = vr.get(q)
                cells += [cell(r, t, base.get(q)) if r else 'n/a' for t in ('pp512', 'tg128')]
            out.append(f'| {any_r["isa_variant"]} | {any_r["backend"]} | ' + ' | '.join(cells) + ' |')
        out.append('')
        rep0 = [r for r in hr if r['threads'] == thr and r['repack'] == '0']
        if rep0:
            out += [f'Weight repacking (`--repack 1` vs `--repack 0`), {rep0[0]["isa_variant"]}, {thr} threads:', '',
                    '| quant | pp512 repack on | pp512 off | on/off | tg128 on | tg128 off | on/off |',
                    '|---|---:|---:|---:|---:|---:|---:|']
            for r0 in rep0:
                r1 = next(r for r in hr if r['threads'] == thr and r['repack'] == '1' and r['_key'] == r0['_key']
                          and r['model_quant'] == r0['model_quant'])
                out.append(f'| {r0["model_quant"]} | {r1["pp512_tps"]:.1f} | {r0["pp512_tps"]:.1f} | '
                           f'{r1["pp512_tps"] / r0["pp512_tps"]:.2f}× | {r1["tg128_tps"]:.1f} | {r0["tg128_tps"]:.1f} | '
                           f'{r1["tg128_tps"] / r0["tg128_tps"]:.2f}× |')
            out.append('')
(ROOT / 'summary.md').write_text('\n'.join(out) + '\n')
print(f'{len(rows)} rows')
