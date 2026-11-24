# ISA variants of llama.cpp: prompt processing vs token generation

Gemma 3 1B instruct (bartowski/google_gemma-3-1b-it-GGUF @ 116f762), `llama-bench -p 512 -n 128 -r 5`.
Cells: tokens/s, mean ± standard deviation of 5 repetitions, and in brackets the speed-up relative to the
host's baseline variant (same threads, same quantization, repacking on). pp512 = prompt processing of
512 tokens; tg128 = generation of 128 tokens. Raw tables, logs and per-host notes are in the host directories.

## xps-8930: Intel Core i7-8700 (6C/12T), Fedora 44 (Linux 7.2.11)

### 6 threads

| variant | backend | Q4_0 pp512 | Q4_0 tg128 | Q8_0 pp512 | Q8_0 tg128 | Q4_K_M pp512 | Q4_K_M tg128 |
|---|---|---:|---:|---:|---:|---:|---:|
| baseline: x86-64 (SSE2 only) | CPU | 49.5 ± 0.0 (1.00×) | 32.7 ± 0.0 (1.00×) | 57.7 ± 0.3 (1.00×) | 27.4 ± 0.0 (1.00×) | 11.4 ± 0.0 (1.00×) | 10.0 ± 0.0 (1.00×) |
| SSE4.2 | CPU | 94.0 ± 0.1 (1.90×) | 34.9 ± 0.0 (1.07×) | 66.0 ± 0.0 (1.14×) | 27.2 ± 0.0 (1.00×) | 15.1 ± 0.0 (1.33×) | 12.0 ± 0.0 (1.20×) |
| SSE4.2+AVX | CPU | 125.1 ± 0.4 (2.53×) | 40.0 ± 0.0 (1.22×) | 146.6 ± 0.3 (2.54×) | 28.2 ± 0.0 (1.03×) | 118.1 ± 0.2 (10.40×) | 35.7 ± 0.0 (3.59×) |
| AVX2+FMA+F16C+BMI2 | CPU | 282.7 ± 12.8 (5.71×) | 42.8 ± 0.0 (1.31×) | 236.9 ± 1.2 (4.10×) | 29.9 ± 0.0 (1.09×) | 208.5 ± 0.9 (18.35×) | 35.6 ± 0.0 (3.58×) |
| native (-march=native) | CPU | 281.0 ± 3.9 (5.67×) | 43.0 ± 0.1 (1.31×) | 236.9 ± 0.4 (4.10×) | 30.0 ± 0.1 (1.10×) | 210.0 ± 0.2 (18.49×) | 35.5 ± 0.0 (3.57×) |
| dispatch (BACKEND_DL+ALL_VARIANTS) -> haswell | CPU | 279.4 ± 1.3 (5.64×) | 42.7 ± 0.0 (1.31×) | 235.8 ± 1.2 (4.08×) | 29.9 ± 0.0 (1.09×) | 209.1 ± 0.6 (18.40×) | 38.3 ± 0.0 (3.85×) |

Weight repacking (`--repack 1` vs `--repack 0`), native (-march=native), 6 threads:

| quant | pp512 repack on | pp512 off | on/off | tg128 on | tg128 off | on/off |
|---|---:|---:|---:|---:|---:|---:|
| Q4_0 | 281.0 | 205.1 | 1.37× | 43.0 | 37.3 | 1.15× |
| Q8_0 | 236.9 | 238.3 | 0.99× | 30.0 | 28.3 | 1.06× |
| Q4_K_M | 210.0 | 211.2 | 0.99× | 35.5 | 35.0 | 1.01× |

## krom2: Apple M2 (4P+4E), Fedora Asahi Remix 44 (Linux 7.2.12, 16K pages)

### 4 threads

| variant | backend | Q4_0 pp512 | Q4_0 tg128 | Q8_0 pp512 | Q8_0 tg128 | Q4_K_M pp512 | Q4_K_M tg128 |
|---|---|---:|---:|---:|---:|---:|---:|
| baseline: armv8-a (NEON) | CPU | 117.9 ± 0.1 (1.00×) | 55.0 ± 0.0 (1.00×) | 142.2 ± 0.2 (1.00×) | 40.4 ± 0.0 (1.00×) | 101.3 ± 0.0 (1.00×) | 49.5 ± 0.0 (1.00×) |
| armv8.2-a+dotprod | CPU | 578.8 ± 0.3 (4.91×) | 59.3 ± 0.1 (1.08×) | 514.8 ± 0.4 (3.62×) | 40.6 ± 0.0 (1.01×) | 141.8 ± 0.2 (1.40×) | 52.0 ± 0.0 (1.05×) |
| armv8.2-a+dotprod+i8mm | CPU | 567.0 ± 0.3 (4.81×) | 59.2 ± 0.0 (1.08×) | 541.3 ± 0.8 (3.81×) | 40.6 ± 0.0 (1.00×) | 141.6 ± 0.2 (1.40×) | 52.0 ± 0.0 (1.05×) |
| native (-mcpu=apple-m2+...+fp16+dotprod+i8mm) | CPU | 566.0 ± 0.8 (4.80×) | 59.2 ± 0.0 (1.08×) | 539.9 ± 0.3 (3.80×) | 40.6 ± 0.0 (1.00×) | 142.2 ± 0.1 (1.40×) | 52.0 ± 0.1 (1.05×) |
| native CPU build + Vulkan (Asahi), all layers on GPU | Vulkan | 626.2 ± 0.3 (5.31×) | 51.7 ± 0.1 (0.94×) | 588.9 ± 0.6 (4.14×) | 40.3 ± 0.0 (1.00×) | 567.1 ± 0.5 (5.60×) | 44.3 ± 0.0 (0.89×) |

Weight repacking (`--repack 1` vs `--repack 0`), native (-mcpu=apple-m2+...+fp16+dotprod+i8mm), 4 threads:

| quant | pp512 repack on | pp512 off | on/off | tg128 on | tg128 off | on/off |
|---|---:|---:|---:|---:|---:|---:|
| Q4_0 | 566.0 | 236.0 | 2.40× | 59.2 | 58.2 | 1.02× |
| Q8_0 | 539.9 | 280.6 | 1.92× | 40.6 | 40.7 | 1.00× |
| Q4_K_M | 142.2 | 136.2 | 1.04× | 52.0 | 52.0 | 1.00× |

### 8 threads

| variant | backend | Q4_0 pp512 | Q4_0 tg128 | Q8_0 pp512 | Q8_0 tg128 | Q4_K_M pp512 | Q4_K_M tg128 |
|---|---|---:|---:|---:|---:|---:|---:|
| baseline: armv8-a (NEON) | CPU | 148.9 ± 0.9 (1.00×) | 36.4 ± 2.6 (1.00×) | 175.6 ± 0.5 (1.00×) | 31.5 ± 1.4 (1.00×) | 126.9 ± 0.6 (1.00×) | 37.2 ± 2.8 (1.00×) |
| armv8.2-a+dotprod | CPU | 584.2 ± 7.0 (3.92×) | 53.3 ± 2.1 (1.47×) | 533.0 ± 2.4 (3.04×) | 35.9 ± 1.3 (1.14×) | 178.9 ± 1.0 (1.41×) | 42.8 ± 2.3 (1.15×) |
| armv8.2-a+dotprod+i8mm | CPU | 587.5 ± 8.3 (3.95×) | 53.5 ± 0.5 (1.47×) | 561.6 ± 3.7 (3.20×) | 36.8 ± 1.2 (1.17×) | 178.0 ± 0.8 (1.40×) | 40.8 ± 2.0 (1.10×) |
| native (-mcpu=apple-m2+...+fp16+dotprod+i8mm) | CPU | 603.6 ± 2.3 (4.05×) | 52.4 ± 2.5 (1.44×) | 573.4 ± 5.8 (3.27×) | 35.7 ± 2.1 (1.13×) | 179.7 ± 1.3 (1.42×) | 45.2 ± 2.7 (1.22×) |

Weight repacking (`--repack 1` vs `--repack 0`), native (-mcpu=apple-m2+...+fp16+dotprod+i8mm), 8 threads:

| quant | pp512 repack on | pp512 off | on/off | tg128 on | tg128 off | on/off |
|---|---:|---:|---:|---:|---:|---:|
| Q4_0 | 603.6 | 272.6 | 2.21× | 52.4 | 37.9 | 1.38× |
| Q8_0 | 573.4 | 318.3 | 1.80× | 35.7 | 35.3 | 1.01× |
| Q4_K_M | 179.7 | 172.8 | 1.04× | 45.2 | 41.4 | 1.09× |

## kromyrzen: AMD Ryzen 7 3700X (8C/16T), Windows 11 Pro N for Workstations 26H2 (10.0.26300)

### 8 threads

| variant | backend | Q4_0 pp512 | Q4_0 tg128 | Q8_0 pp512 | Q8_0 tg128 | Q4_K_M pp512 | Q4_K_M tg128 |
|---|---|---:|---:|---:|---:|---:|---:|
| baseline: ggml-cpu-x64.dll (SSE2) | CPU | 64.5 ± 0.2 (1.00×) | 32.4 ± 0.1 (1.00×) | 97.1 ± 0.3 (1.00×) | 24.5 ± 0.1 (1.00×) | 28.4 ± 0.0 (1.00×) | 19.4 ± 0.2 (1.00×) |
| ggml-cpu-sse42.dll | CPU | 141.7 ± 0.7 (2.20×) | 34.5 ± 0.5 (1.06×) | 152.8 ± 0.4 (1.57×) | 24.6 ± 0.1 (1.00×) | 36.9 ± 0.1 (1.30×) | 22.9 ± 0.1 (1.18×) |
| ggml-cpu-sandybridge.dll (AVX) | CPU | 169.1 ± 6.1 (2.62×) | 35.1 ± 0.2 (1.08×) | 187.4 ± 0.6 (1.93×) | 24.6 ± 0.1 (1.00×) | 163.3 ± 1.2 (5.75×) | 31.8 ± 0.1 (1.64×) |
| ggml-cpu-ivybridge.dll (AVX+F16C) | CPU | 180.2 ± 1.0 (2.79×) | 36.2 ± 0.2 (1.12×) | 196.3 ± 8.4 (2.02×) | 25.2 ± 0.2 (1.03×) | 163.6 ± 2.2 (5.76×) | 32.8 ± 0.1 (1.69×) |
| ggml-cpu-piledriver.dll (AVX+F16C+FMA) | CPU | 178.1 ± 1.1 (2.76×) | 36.3 ± 0.1 (1.12×) | 192.5 ± 8.6 (1.98×) | 25.4 ± 0.0 (1.03×) | 164.8 ± 1.4 (5.80×) | 32.7 ± 0.5 (1.68×) |
| ggml-cpu-haswell.dll (AVX2+FMA+F16C+BMI2; default) | CPU | 380.6 ± 2.4 (5.90×) | 36.5 ± 0.2 (1.13×) | 297.3 ± 4.1 (3.06×) | 25.3 ± 0.1 (1.03×) | 279.7 ± 4.1 (9.85×) | 32.8 ± 0.3 (1.69×) |

Weight repacking (`--repack 1` vs `--repack 0`), ggml-cpu-haswell.dll (AVX2+FMA+F16C+BMI2; default), 8 threads:

| quant | pp512 repack on | pp512 off | on/off | tg128 on | tg128 off | on/off |
|---|---:|---:|---:|---:|---:|---:|
| Q4_0 | 380.6 | 262.8 | 1.45× | 36.5 | 36.0 | 1.01× |
| Q8_0 | 297.3 | 290.0 | 1.03× | 25.3 | 25.3 | 1.00× |
| Q4_K_M | 279.7 | 245.0 | 1.14× | 32.8 | 32.8 | 1.00× |

## krom1u: Apple M1 Ultra (16P+4E), macOS 27.2

### 16 threads

| variant | backend | Q4_0 pp512 | Q4_0 tg128 | Q8_0 pp512 | Q8_0 tg128 | Q4_K_M pp512 | Q4_K_M tg128 |
|---|---|---:|---:|---:|---:|---:|---:|
| baseline: armv8-a (NEON), source build | CPU | 444.5 ± 9.8 (1.00×) | 129.6 ± 3.7 (1.00×) | 559.9 ± 8.2 (1.00×) | 114.7 ± 2.0 (1.00×) | 395.2 ± 3.3 (1.00×) | 116.5 ± 7.1 (1.00×) |
| armv8.2-a+dotprod, source build | CPU | 1455.2 ± 127.8 (3.27×) | 156.7 ± 2.6 (1.21×) | 1659.5 ± 48.0 (2.96×) | 130.4 ± 2.6 (1.14×) | 583.8 ± 2.1 (1.48×) | 136.4 ± 3.8 (1.17×) |
| native (-mcpu=native), source build | CPU | 1743.2 ± 133.2 (3.92×) | 162.5 ± 3.0 (1.25×) | 1790.5 ± 196.8 (3.20×) | 132.0 ± 9.4 (1.15×) | 557.2 ± 35.6 (1.41×) | 120.0 ± 3.9 (1.03×) |
| Homebrew: ggml-cpu-apple_m1 + Accelerate BLAS, -dev none | CPU+BLAS | 1060.7 ± 79.8 (2.39×) | 143.4 ± 1.5 (1.11×) | 847.3 ± 39.7 (1.51×) | 119.8 ± 2.0 (1.04×) | 710.1 ± 31.1 (1.80×) | 126.1 ± 1.4 (1.08×) |
| Homebrew: Metal, all layers on GPU | Metal | 6605.7 ± 23.0 (14.86×) | 141.1 ± 17.8 (1.09×) | 6539.0 ± 136.5 (11.68×) | 130.7 ± 34.7 (1.14×) | 5724.8 ± 5.6 (14.49×) | 186.3 ± 0.5 (1.60×) |

Weight repacking (`--repack 1` vs `--repack 0`), native (-mcpu=native), source build, 16 threads:

| quant | pp512 repack on | pp512 off | on/off | tg128 on | tg128 off | on/off |
|---|---:|---:|---:|---:|---:|---:|
| Q4_0 | 1743.2 | 1030.3 | 1.69× | 162.5 | 149.0 | 1.09× |
| Q8_0 | 1790.5 | 1135.6 | 1.58× | 132.0 | 123.7 | 1.07× |
| Q4_K_M | 557.2 | 472.9 | 1.18× | 120.0 | 107.7 | 1.11× |


## Notes added 2026-11-14

- **UHD 630 rows.** The last two rows of `results.csv` come from
  `lab/hosts/xps-8930/run/llama-bench-{vulkan,cpu}.txt` (2026-11-13): the
  Vulkan build on the Intel UHD 630 and the native CPU build in the same
  session, both with ggml-org's `gemma-3-1b-it-Q4_K_M.gguf` (762.49 MiB) and
  `-r 3`, not bartowski's file. `code/ch08/mkisa.py` does not plot them.
- **What "Q4_K_M" holds for Gemma 3 1B.** The model's rows of 1152 numbers
  do not divide into K-quant super-blocks of 256, so `llama-quantize` stored
  `attn_q`, `attn_k`, `attn_v`, `ffn_gate` and `ffn_up` in Q5_0 (Q8_0 for the
  13 `attn_v` tensors where the recipe asks for Q6_K). Only `attn_output`
  (rows of 1024, Q4_K) and `ffn_down` (rows of 6912, Q4_K and Q6_K) are
  K-quants. By weight, inside the layers: Q5_0 65.4 %, Q4_K 19.2 %, Q6_K
  14.8 %, Q8_0 0.5 %; `token_embd` (tied output) is Q8_0. Read with gguf-py
  from bartowski's file at 116f762.
- **Consequences.** ggml has AVX/AVX2 code for Q5_0 and the K-quants and no
  SSE code (Q4_0 alone has an SSSE3 path), which explains the plain-C x86
  baseline for this file. ggml repacks Q4_K and Q6_K on Arm (8x4 with
  DOTPROD, 8x8 with I8MM) but never Q5_0, so repacking changes this file
  little on Arm (4 % on the M2, 15 % on the M1 Ultra). Source: llama.cpp
  61dbf4922, `ggml/src/ggml-cpu/repack.cpp` and `arch/x86/quants.c`.

## kr0m-gpu: 2 x AMD EPYC 9554 (252 virtual CPUs), Ubuntu 24.04.3 (Linux 6.14.0)

### 32 threads

| variant | backend | Q4_0 pp512 | Q4_0 tg128 | Q8_0 pp512 | Q8_0 tg128 | Q4_K_M pp512 | Q4_K_M tg128 |
|---|---|---:|---:|---:|---:|---:|---:|
| baseline: x86-64 (SSE2 only) | CPU | 50.1 ± 0.0 (1.00×) | 33.4 ± 0.0 (1.00×) | 130.2 ± 0.2 (1.00×) | 65.2 ± 0.1 (1.00×) | 36.4 ± 0.0 (1.00×) | 25.1 ± 0.0 (1.00×) |
| SSE4.2 | CPU | 238.0 ± 0.1 (4.75×) | 88.3 ± 0.2 (2.64×) | 151.7 ± 0.0 (1.17×) | 68.3 ± 0.2 (1.05×) | 39.9 ± 0.0 (1.10×) | 29.7 ± 0.0 (1.18×) |
| SSE4.2+AVX | CPU | 396.4 ± 0.8 (7.92×) | 99.0 ± 0.2 (2.96×) | 429.8 ± 0.5 (3.30×) | 73.6 ± 0.1 (1.13×) | 367.1 ± 0.5 (10.10×) | 47.5 ± 0.6 (1.89×) |
| AVX2+FMA+F16C+BMI2 | CPU | 805.5 ± 2.0 (16.09×) | 125.2 ± 0.4 (3.75×) | 747.9 ± 1.3 (5.75×) | 79.2 ± 0.2 (1.21×) | 649.5 ± 1.9 (17.86×) | 102.3 ± 0.3 (4.07×) |
| AVX-512 (F, CD, BW, DQ, VL) | CPU | 910.8 ± 1.0 (18.19×) | 132.0 ± 0.2 (3.95×) | 856.7 ± 1.4 (6.58×) | 79.9 ± 0.1 (1.23×) | 841.9 ± 1.9 (23.15×) | 105.7 ± 0.3 (4.21×) |
| AVX-512 with VBMI and VNNI | CPU | 1104.6 ± 1.0 (22.06×) | 128.6 ± 0.3 (3.84×) | 969.8 ± 2.5 (7.45×) | 81.5 ± 1.8 (1.25×) | 936.4 ± 3.7 (25.75×) | 107.4 ± 0.1 (4.27×) |
| AVX-512 with VBMI, VNNI, and BF16 | CPU | 1129.3 ± 1.9 (22.55×) | 131.9 ± 0.1 (3.94×) | 980.8 ± 1.2 (7.54×) | 80.4 ± 0.0 (1.23×) | 942.0 ± 0.9 (25.91×) | 104.6 ± 0.2 (4.16×) |
| native (-march=native) | CPU | 1060.9 ± 3.9 (21.19×) | 132.0 ± 0.1 (3.95×) | 947.1 ± 1.3 (7.28×) | 80.8 ± 0.2 (1.24×) | 894.8 ± 1.1 (24.61×) | 98.9 ± 1.0 (3.93×) |
| dispatch (BACKEND_DL+ALL_VARIANTS) -> zen4 | CPU | 1101.6 ± 1.6 (22.00×) | 128.1 ± 0.3 (3.83×) | 972.7 ± 1.2 (7.47×) | 79.4 ± 0.1 (1.22×) | 917.4 ± 1.4 (25.23×) | 101.8 ± 0.3 (4.05×) |
| CUDA, all layers on one H100 PCIe | CUDA | 35188.4 ± 3835.7 (702.75×) | 467.6 ± 3.8 (13.98×) | 37408.9 ± 2162.1 (287.40×) | 384.8 ± 0.4 (5.91×) | 32659.7 ± 1868.2 (898.26×) | 448.5 ± 1.0 (17.84×) |

Weight repacking (`--repack 1` vs `--repack 0`), native (-march=native), 32 threads:

| quant | pp512 repack on | pp512 off | on/off | tg128 on | tg128 off | on/off |
|---|---:|---:|---:|---:|---:|---:|
| Q4_0 | 1060.9 | 847.5 | 1.25× | 132.0 | 112.2 | 1.18× |
| Q8_0 | 947.1 | 947.0 | 1.00× | 80.8 | 81.0 | 1.00× |
| Q4_K_M | 894.8 | 938.6 | 0.95× | 98.9 | 102.9 | 0.96× |

The CPU runs on kr0m-gpu used 32 threads on the second socket (`numactl --cpunodebind=1 --membind=1`); the machine is a virtual one with 252 virtual processors, whose pairing into cores the guest does not show.
