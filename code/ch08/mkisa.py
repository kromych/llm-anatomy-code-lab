"""Speed-ups over each host's baseline, from lab/bench/isa/results.csv, as pgfplots coordinates.

Usage: python3 code/ch08/mkisa.py lab/bench/isa/results.csv figures/ch08-isa.tex
"""
import csv, math, sys
rows = list(csv.DictReader(open(sys.argv[1])))
def get(host, prefix, q, threads, repack='1'):
    m = [r for r in rows if r['host'] == host and r['isa_variant'].startswith(prefix)
         and r['model_quant'] == q and r['threads'] == threads and r['repack'] == repack]
    assert len(m) == 1, (host, prefix, q, threads, len(m))
    r = m[0]
    return float(r['pp512_tps']), float(r['pp512_sd']), float(r['tg128_tps']), float(r['tg128_sd'])
H = [  # host, threads, baseline prefix, [(label, prefix)]
 ('xps-8930', '6', 'baseline', [('SSE4.2', 'SSE4.2,'), ('SSE4.2+AVX', 'SSE4.2+AVX'),
   ('AVX2', 'AVX2'), ('native', 'native ('), ('dispatch', 'dispatch')]),
 ('kromyrzen', '8', 'baseline', [('sse42', 'ggml-cpu-sse42'), ('sandybridge', 'ggml-cpu-sandybridge'),
   ('ivybridge', 'ggml-cpu-ivybridge'), ('piledriver', 'ggml-cpu-piledriver'), ('haswell', 'ggml-cpu-haswell')]),
 ('krom2', '4', 'baseline', [('dotprod', 'armv8.2-a+dotprod,'), ('i8mm', 'armv8.2-a+dotprod+i8mm'),
   ('native', 'native ('), ('vulkan', 'native CPU build + Vulkan')]),
 ('krom1u', '16', 'baseline', [('dotprod', 'armv8.2-a+dotprod'), ('native', 'native ('),
   ('brew', 'Homebrew: ggml-cpu'), ('metal', 'Homebrew: Metal')]),
 ('kr0m-gpu', '32', 'baseline', [('SSE4.2', 'SSE4.2,'), ('SSE4.2+AVX', 'SSE4.2+AVX'),
   ('AVX2', 'AVX2'), ('AVX-512', 'AVX-512 (F'), ('AVX-512+VNNI', 'AVX-512 with VBMI and'),
   ('AVX-512+BF16', 'AVX-512 with VBMI, VNNI'), ('native', 'native ('), ('dispatch', 'dispatch')]),
]
# exact-prefix helper: 'SSE4.2,' means variant == 'SSE4.2'
def g(host, pre, q, t):
    if pre.endswith(','):
        m = [r for r in rows if r['host'] == host and r['isa_variant'] == pre[:-1] and r['model_quant'] == q and r['threads'] == t and r['repack'] == '1']
        assert len(m) == 1, (host, pre, q, len(m)); r = m[0]
        return float(r['pp512_tps']), float(r['pp512_sd']), float(r['tg128_tps']), float(r['tg128_sd'])
    return get(host, pre, q, t)
y = 0
out = {q: {'pp': [], 'tg': []} for q in ('Q4_0', 'Q8_0', 'Q4_K_M')}
off = {'Q4_0': -0.24, 'Q8_0': 0.0, 'Q4_K_M': 0.24}
for host, t, base, vs in H:
    y += 1  # header row
    print(f'% header {host} at y={y}')
    for lab, pre in vs:
        y += 1
        for q in out:
            b = g(host, base, q, t); v = g(host, pre, q, t)
            for k, (i, j) in (('pp', (0, 1)), ('tg', (2, 3))):
                r = v[i] / b[i]
                e = r * math.hypot(v[j] / v[i], b[j] / b[i])
                out[q][k].append((r, e, y + off[q], f'{host}:{lab}'))
        print(f'% y={y} {host} {lab}')
for q in out:
    for k in ('pp', 'tg'):
        print(f'% {q} {k}')
        print(' '.join(f'({r:.3f},{yy:.2f}) +- ({e:.3f},0)' for r, e, yy, _ in out[q][k]))
        for r, e, yy, l in out[q][k]:
            print(f'%   {l:28s} {r:6.2f} +- {e:5.3f}')

# ---------------------------------------------------------------- figure
if len(sys.argv) > 2:
    labels = {2: r'+ SSE4.2', 3: r'+ AVX', 4: r'+ AVX2, FMA, F16C, BMI2', 5: r'native',
              6: r'dispatch: \texttt{haswell}',
              8: r'\texttt{sse42}', 9: r'\texttt{sandybridge} (AVX)', 10: r'\texttt{ivybridge} (+F16C)',
              11: r'\texttt{piledriver} (+FMA)', 12: r'\texttt{haswell} (+AVX2)',
              14: r'+ DOTPROD', 15: r'+ DOTPROD, I8MM', 16: r'native', 17: r'GPU, Vulkan',
              19: r'+ DOTPROD', 20: r'native', 21: r'Homebrew: \texttt{apple\_m1}', 22: r'GPU, Metal',
              24: r'+ SSE4.2', 25: r'+ AVX', 26: r'+ AVX2, FMA, F16C, BMI2',
              27: r'+ AVX-512', 28: r'+ AVX-512, VBMI, VNNI', 29: r'+ AVX-512, BF16',
              30: r'native', 31: r'dispatch: \texttt{zen4}'}
    heads = {1: r'\SysLinuxX{} (Core i7-8700)', 7: r'\SysWin{} (Ryzen 7 3700X)',
             13: r'\SysLinuxArm{} (Apple M2)', 18: r'\SysMac{} (Apple M1 Ultra)',
             23: r'\SysCloud{} (EPYC 9554)'}
    marks = {'Q4_0': ('*', 'series1', 'series1', '2.0pt'),
             'Q8_0': ('square*', 'series2', 'series2', '1.8pt'),
             'Q4_K_M': ('triangle*', 'series3', 'white', '2.3pt')}
    names = {'Q4_0': r'Q4\_0', 'Q8_0': r'Q8\_0', 'Q4_K_M': r'Q4\_K\_M'}
    common = (r"xmode=log, xmin=0.8, xmax=35, xtick={1,2,5,10,20}, log ticks with fixed point,"
              "\n      y dir=reverse, ymin=0.45, ymax=31.55, scale only axis, width=4.75cm, height=10.8cm,"
              "\n      label style={font=\\sffamily\\scriptsize, text=ink2},"
              "\n      tick label style={font=\\sffamily\\scriptsize, text=ink2},"
              "\n      title style={font=\\sffamily\\scriptsize, text=ink, yshift=-3pt},"
              "\n      axis line style={inkaxis}, major tick style={inkaxis}, xmajorgrids,"
              "\n      major grid style={inkgrid, line width=0.3pt}, ytick style={draw=none},"
              "\n      error bars/error bar style={ink2, line width=0.5pt},"
              "\n      error bars/error mark options={rotate=90, mark size=1.2pt, ink2},")
    yt = ','.join(str(k) for k in labels)
    heads_nodes = '\n'.join(f"    \\node[anchor=west, inner xsep=0pt, font=\\sffamily\\scriptsize\\bfseries, text=ink]\n      at ([xshift=-4.05cm]axis cs:0.8,{k}) {{{v}}};" for k, v in heads.items())
    def plots(k, legend):
        s = []
        for q in ('Q4_0', 'Q8_0', 'Q4_K_M'):
            m, d, f, sz = marks[q]
            pts = '\n      '.join(f'({r:.3f},{yy:.2f}) +- ({e:.3f},0)' for r, e, yy, _ in out[q][k])
            s.append(f"    \\addplot[only marks, mark={m}, mark size={sz},\n"
                     f"      mark options={{draw={d}, fill={f}, line width=0.5pt}},\n"
                     f"      error bars/.cd, x dir=both, x explicit]\n      coordinates {{\n      {pts}}};")
            if legend:
                s.append(f"    \\addlegendentry{{{names[q]}}}")
        return '\n'.join(s)
    seps = '\n'.join(f"    \\draw[inkaxis, line width=0.4pt] (axis cs:0.8,{y}) -- (axis cs:35,{y});" for y in (6.6, 12.6, 17.6, 22.6))
    one = "    \\draw[ink2, line width=0.5pt, densely dashed] (axis cs:1,0.45) -- (axis cs:1,31.55);"
    f = open(sys.argv[2], 'w')
    f.write(r"""% Figure: speed-up of llama.cpp builds for different instruction-set
% levels over each machine's baseline build (x86-64 with SSE2 only, or
% armv8-a with NEON), for prompt processing (pp512) and generation (tg128).
% Gemma 3 1B instruct in three formats, llama-bench -p 512 -n 128 -r 5,
% weight repacking on; error bars: one standard deviation of the ratio,
% propagated from the five repetitions.  Data: lab/bench/isa/results.csv
% (generated by code/ch08/mkisa.py; do not edit the coordinates by hand).
% Standalone: `make figures` -> build/figures/ch08-isa.pdf
\begin{tikzpicture}
  \begin{axis}[name=pp, """ + common + r"""
      ytick={""" + yt + r"""},
      yticklabels={""" + ','.join('{' + v + '}' for v in labels.values()) + r"""},
      yticklabel style={text width=3.3cm, align=right},
      clip mode=individual,
      title={prompt processing (pp512)},
      xlabel={speed-up over the baseline build},
      legend style={draw=none, fill=none, font=\sffamily\scriptsize, text=ink,
        at={(1.055,1.075)}, anchor=south, legend columns=3,
        /tikz/every even column/.append style={column sep=10pt}},
      legend cell align=left]
""" + seps + "\n" + one + "\n" + heads_nodes + "\n" + plots('pp', True) + r"""
  \end{axis}
  \begin{axis}[at={($(pp.east)+(0.5cm,0)$)}, anchor=west, """ + common + r"""
      ytick={""" + yt + r"""}, yticklabels={},
      title={generation (tg128)},
      xlabel={speed-up over the baseline build}]
""" + seps + "\n" + one + "\n" + plots('tg', False) + r"""
  \end{axis}
\end{tikzpicture}
""")
