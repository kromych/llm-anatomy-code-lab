# Published decoding speeds: AI providers, hardware vendors, MLPerf

Reference data for comparing the book's own llama.cpp measurements (one
request, laptops and desktops, roughly 10-100 tokens/s for 1B-8B models) with
the speeds that model providers, hardware vendors and MLPerf publish.
Compiled 2026-11-14; every source was accessed on that date.

The same 63 data points are in `vendor-speeds.csv`, in the same order as the
IDs below (P = providers, H = hardware and inference services, M = MLPerf,
I = independent measurements). Values and quotes are copied from the sources;
where we derived a number (per-GPU from per-system, per-user from a latency
limit, a ratio) the conditions column says "our division" and shows the
arithmetic.

## Metrics

**Per-user output speed** (tokens/s per user, per stream; NVIDIA and
SemiAnalysis call it "interactivity"). How fast one request receives
generated tokens once they flow. It is the reciprocal of the time per output
token: 40 ms per token is 25 tokens/s. llama.cpp's token-generation rate for a
single request (`tg` in `llama-bench`, the "eval" rate in the server log) is
this quantity, measured without prompt processing and without a network.

**Time per output token (TPOT).** MLPerf's definition: "the average interval
between all the tokens generated" in one request [S48].

**Time to first token (TTFT).** From sending the request to receiving the first
token: network, queueing and prompt processing (prefill). For reasoning models
the first token may be a reasoning token; Artificial Analysis therefore also
reports *time to first answer token*, which includes the thinking time
[S49].

**Aggregate throughput.** Tokens per second summed over all requests served at
once, normalised per GPU or chip, per server (usually 8 GPUs), per rack (an
NVL72 rack has 72 GPUs) or per megawatt. In the decode phase, aggregate
throughput is roughly per-user speed times the number of concurrent streams:
NVIDIA's 10,000 tokens/s per B200 at 50 tokens/s per user (H6) means about 200
streams per GPU. A vendor's best per-user figure and its best per-GPU figure
are different operating points of the same machine (compare H3 and H4).

**MLPerf scenarios** [S48]. *Offline*: all samples are sent at once and
there is no latency limit, so it measures maximum throughput. *Server*: queries
arrive at random (Poisson) and 99 % of them must meet the benchmark's TTFT and
TPOT limits; the result is the highest load that passes. *Interactive*: the
same with tighter limits. MLPerf reports tokens/s for the whole system under
test; it does not report per-user speed, but the TPOT limit sets a floor on it.

| MLPerf benchmark (v6.1) | Server TTFT / TPOT | min. tokens/s per user (1000 / TPOT) | Interactive TTFT / TPOT | min. tokens/s per user |
|---|---|---|---|---|
| Llama 3.1 8B | 2,000 ms / 100 ms | 10 | 500 ms / 30 ms | 33.3 |
| Llama 2 70B | 2,000 ms / 200 ms | 5 | 450 ms / 40 ms | 25 |
| DeepSeek-R1 | 2,000 ms / 80 ms | 12.5 | 1,500 ms / 15 ms | 66.7 |
| gpt-oss-120b | 3,000 ms / 80 ms | 12.5 | 2,000 ms / 20 ms | 50 |

Limits from the MLPerf inference rules [S48]; the per-user column is our
division. Speculative decoding is allowed only in the DeepSeek-R1 and
gpt-oss-120b Interactive scenarios.

**Kinds of data point.** *vendor claim*: published by the company about its own
product or partner; *vendor claim (cites independent measurement)*: the vendor
quotes a third party, usually Artificial Analysis; *MLPerf submission*:
audited result in the MLCommons results table (or the submitter's restatement
of it); *independent measurement*: Artificial Analysis data read directly;
*secondary, unverified*: no primary source could be read.

## The ranges at a glance

- **Per-user speed, vendor claims:** from 60 tokens/s (DeepSeek-V3 on
  DeepSeek's API, December 2024, P9) to 3,431 tokens/s (Gemma 4 31B on NVIDIA
  Groq 3 LPX, measured by Artificial Analysis, H10; NVIDIA's own coding run
  reached a median of 4,767). The top of the range belongs to wafer-scale and
  LPU hardware (Cerebras, Groq), speculative decoding and diffusion models.
  Frontier GPU numbers: >250 (DeepSeek-R1, H1), >1,000 (Llama 4 Maverick, H3),
  >150 (DeepSeek-V4-Pro, H9) tokens/s per user.
- **Per-user speed, independent (Artificial Analysis, 1k-token prompts):** from
  48 tokens/s (GPT-6.1 Sol, standard tier, I10) to 1,849 tokens/s (gpt-oss-120B
  on Cerebras, I1). Closed models from OpenAI, Anthropic, Google and xAI on
  standard tiers run at about 48-217 tokens/s (I8-I10, I12, I13).
- **Aggregate per GPU or chip:** from 677 tokens/s per chip (Qwen 3.5-397B,
  decode-heavy, TPU Ironwood, H18) to 60,000 tokens/s per GPU (gpt-oss on B200,
  NVIDIA claim, H5). In MLPerf v6.1 the rows here span 3,521 tokens/s per GPU
  (DeepSeek-R1 Interactive, GB300, M9) to 21,744 (Llama 3.1 8B Server, B300,
  M4), all our divisions of system results.
- **Against the book's numbers:** for the same 8B model class, a hosted
  Llama 3.1 8B streams 631 tokens/s on Groq and 148 tokens/s on CoreWeave
  (I5, I6). In MLPerf one 8x B300 server produces 173,950 tokens/s of Llama 3.1
  8B in total (M4), while the benchmark only requires each user to get 10
  tokens/s (99th percentile), the low end of a laptop.

## 1. Model and API providers

Figures the model owners (or the partner serving their product) publish. Meta's
own LlamaCon post gives no speed [S45]; P6 and P7 are its partners'
figures. No verifiable xAI figure was found (see "Not verified").

| ID | Company | Model | Hardware | Metric | Conditions | Value | Date | Kind | Src | Quote |
|---|---|---|---|---|---|---|---|---|---|---|
| P1 | Anthropic | Claude Fable 5.2, Claude Mythos 5.2, Claude Opus 5.5 (fast mode; research preview on Opus 5) | not stated | ratio of output tokens/s per request, fast mode vs standard speed | same model, 'faster inference configuration'; gain is in OTPS, not TTFT; premium price; no absolute baseline published | **up to 2.5** x standard OTPS | undated (beta header fast-mode-2026-02-01) | vendor claim | [S1] | "Fast mode delivers up to 2.5x higher output tokens per second at premium pricing." |
| P2 | OpenAI | GPT models in the API (docs examples: gpt-6.1-sol, gpt-5.6-sol) | not stated | speed ratio, Fast mode vs Standard processing | service tier 'Fast mode' (renamed from Priority processing on 2026-07-30); no absolute tokens/s published | **up to 2.5** x Standard | undated (accessed 2026-11-14) | vendor claim | [S2] | "Fast mode delivers up to 2.5× faster speeds and more consistent latency with pay-as-you-go pricing." |
| P3 | OpenAI | Ultrafast tier (GPT-6 Astra; GPT-6.1 Sol) | not stated | generated tokens/s per request | premium 'Ultrafast' tier; OpenAI quoted as 'up to 8X faster generation in Codex and up to 6X ... through the API' vs Standard; OpenAI docs page gives no number | **up to 300** tokens/s | 2026-09-29 | secondary, unverified | [S3] | "reaches up to 300 generated tokens per second" |
| P4 | OpenAI (figure published by Cerebras) | GPT-5.3-Codex-Spark (smaller GPT-5.3-Codex; size not disclosed) | Cerebras Wafer-Scale Engine | output tokens/s per request | research preview at launch; conditions not stated; a later OpenAI staff post relayed on the OpenAI forum says 'over 1200 tokens per second' (2026-02-20, unverified) | **>1,000** tokens/s | 2026-02-12 | vendor claim | [S4] | "it runs at over 1,000 tokens/s" |
| P5 | Google DeepMind | Gemini Diffusion (experimental text-diffusion model; size not disclosed) | not stated | sampling speed, tokens/s, excluding fixed overhead | 'Average sampling speed across reported evals'; excludes a 0.84 s overhead; diffusion model, not autoregressive | **1,479** tokens/s | undated page (model announced May 2025) | vendor claim | [S5] | "Sampling speed excluding overhead ... 1479 tokens / sec" |
| P6 | Meta Llama API (figure published by Cerebras) | Llama 4 Scout | Cerebras (wafer-scale) | output tokens/s per request | Llama API preview; ChatGPT (~130) and DeepSeek (~25) figures attributed to Artificial Analysis; headline says '18x faster than OpenAI' | **>2,600** tokens/s | 2025-04-29 | vendor claim | [S6] | "delivers over 2,600 tokens per second for Llama 4 Scout, compared to approximately 130 tokens per second for ChatGPT" |
| P7 | Meta Llama API (figure published by Groq) | Llama 4 (model not named in the release) | Groq LPU | tokens/s ('throughput'; per request implied) | limited preview; 'up to'; conditions not stated | **up to 625** tokens/s | 2025-04-29 | vendor claim | [S7] | "Speeds of up to 625 tokens/sec throughput" |
| P8 | Mistral AI | Le Chat 'Flash Answers' (Mistral Large 2, 123B, per Cerebras) | Cerebras (per Cerebras) | words per second (not tokens) | 'up to'; compared with 'any other chat assistant' | **~1,000** words/s | 2025-02-06 | vendor claim | [S8] | "le Chat reasons, reflects, and responds faster than any other chat assistant, up to ~1000 words / sec." |
| P9 | DeepSeek | DeepSeek-V3 (671B MoE, 37B activated) | not stated | output tokens/s on DeepSeek's API | launch claim; '3x faster than V2'; conditions not stated | **60** tokens/s | 2024-12-26 | vendor claim | [S9] | "60 tokens/second (3x faster than V2!)" |
| P10 | Inception | Mercury 2 (diffusion LLM; size not disclosed) | NVIDIA H100 ('standard NVIDIA GPUs') | decoding tokens/s per request | conditions not stated; diffusion model generates several tokens per step | **1,000+** tokens/s | 2026-10-29 | vendor claim | [S10] | "decoding 1000+ tokens per second on standard NVIDIA GPUs." |
| P11 | Inception | Mercury 2 | 'standard NVIDIA GPUs' | time to first token (TTFT) | conditions not stated | **<300** ms | 2026-10-29 | vendor claim | [S10] | "TTFT <300 ms on standard NVIDIA GPUs." |

## 2. Hardware and inference-service vendors

| ID | Company | Model | Hardware | Metric | Conditions | Value | Date | Kind | Src | Quote |
|---|---|---|---|---|---|---|---|---|---|---|
| H1 | NVIDIA | DeepSeek-R1 671B, FP4 | DGX B200 (8x B200) | output tokens/s per user | concurrency 1; input 1,024 / output 2,048 tokens | **>250** tokens/s per user | 2025-03-18 | vendor claim | [S11] | "A single NVIDIA DGX system with eight NVIDIA Blackwell GPUs can achieve over 250 tokens per second per user" |
| H2 | NVIDIA | DeepSeek-R1 671B, FP4 | DGX B200 (8x B200) | aggregate output tokens/s per 8-GPU system | 'Concurrency MAX'; = >3,750 tokens/s per GPU (30,000 / 8, our division) | **>30,000** tokens/s per server | 2025-03-18 | vendor claim | [S11] | "or a maximum throughput of over 30,000 tokens per second" |
| H3 | NVIDIA | Llama 4 Maverick (400B MoE), FP8 | DGX B200 (8x B200) | output tokens/s per user | EAGLE-3 speculative decoding (draft length 3); measured by Artificial Analysis (1,038 tokens/s per Cerebras release, H11) | **>1,000** tokens/s per user | 2025-05-22 | vendor claim (cites independent measurement) | [S12] | "can achieve over 1,000 tokens per second (TPS) per user on the 400-billion-parameter Llama 4 Maverick model" |
| H4 | NVIDIA | Llama 4 Maverick (400B MoE), FP8 | DGX B200 (8x B200) | aggregate tokens/s per 8-GPU server | highest-throughput configuration (per-user speed not given); = 9,000 tokens/s per GPU (72,000 / 8, our division) | **72,000** tokens/s per server | 2025-05-22 | vendor claim | [S12] | "it reaches 72,000 TPS/server at our highest throughput configuration." |
| H5 | NVIDIA | gpt-oss-120b (precision not stated) | B200, TensorRT-LLM | aggregate tokens/s per GPU | SemiAnalysis InferenceMAX context; the same sentence also claims 1,000 tokens/s per user; not stated that both hold at one operating point | **60,000** tokens/s per GPU | 2025-10-09 | vendor claim | [S13] | "NVIDIA B200 sets the pace with 60,000 tokens per second per GPU and 1,000 tokens per second per user on gpt-oss" |
| H6 | NVIDIA | Llama 3.3 70B (dense; FP8/NVFP4 listed, not specified) | B200 | aggregate tokens/s per GPU at a fixed per-user speed | InferenceMAX v1, input 1K / output 1K, at 50 tokens/s per user (implies ~200 concurrent streams per GPU, our division) | **10,000** tokens/s per GPU | 2025-10-13 | vendor claim | [S14] | "Blackwell delivers 10,000 tokens per second at 50 TPS/user in the Llama 3.3 70B 1K/1K benchmark" |
| H7 | NVIDIA | DeepSeek-R1 (precision not specified) | GB200 NVL72 | aggregate tokens/s per GPU at a fixed per-user speed | InferenceMAX, input 8K / output 1K, 50 tokens/s per user; 'up to 15x' H200 (figure alt text) | **10,000** tokens/s per GPU | 2025-10-13 | vendor claim | [S14] | "GB200 achieving up to 15x higher throughput, 10,000 TPS/GPU, than H200 at 50 TPS per user" |
| H8 | Baseten (NVIDIA-based inference provider) | gpt-oss-120b | 8x B200, TP8 EP1, TensorRT-LLM | output tokens/s per request | EAGLE-3 speculative decoding; 'independently benchmarked' by Artificial Analysis; Baseten's post says 8 B200; Cerebras' blog of 2025-11-06 describes the same result as eight GB200 GPUs | **~650** tokens/s | 2025-10-24 | vendor claim (cites independent measurement) | [S15] | "uplift from ~400 to ~650 tokens per second on GPT-OSS 120B" |
| H9 | NVIDIA | DeepSeek-V4-Pro | GB200 NVL72 | output tokens/s per user | SemiAnalysis InferenceX open benchmark; input/output lengths and precision not stated | **>150** tokens/s per user | 2026-04-24 | vendor claim | [S16] | "DeepSeek-V4-Pro on NVIDIA GB200 NVL72 achieves over 150 tokens/sec/user" |
| H10 | NVIDIA (Groq 3 LPX) | Gemma 4 31B | Groq 3 LPX rack (LP30 LPUs; number used not stated) | median output tokens/s per request | measured by Artificial Analysis (data 2026-08-20), 100K-token input; 10K input gave 3,382; NVIDIA's own SPEED-Bench coding run: median 4,767 | **3,431** tokens/s | 2026-08-24 | vendor claim (cites independent measurement) | [S17] | "Median speed across samples with 100K input context length was 3,431 tokens/second." |
| H11 | Cerebras | Llama 4 Maverick | Cerebras (chip not named on page) | output tokens/s per request | measured by Artificial Analysis; NVIDIA Blackwell (DGX B200) endpoint 1,038 on the same benchmark | **2,522** tokens/s | 2025-05-28 | vendor claim (cites independent measurement) | [S18] | "Artificial Analysis has benchmarked Cerebras' Llama 4 Maverick endpoint at 2,522 tokens per second" |
| H12 | Cerebras | gpt-oss-120b (precision not stated) | Cerebras Inference Cloud | output tokens/s per request | 'at full 128k context'; 'third-party benchmarking or internal testing' | **3,000** tokens/s | 2025-08-05 | vendor claim | [S19] | "Developers can run the model at 3000 tokens per second at full 128k context" |
| H13 | Cerebras | Mistral Large 2 (123B) for Le Chat | Cerebras Wafer Scale Engine | output tokens/s, text queries | '10x faster' than ChatGPT 4o, Sonnet 3.5, DeepSeek R1 | **>1,100** tokens/s | 2025-02-06 | vendor claim | [S20] | "At over 1,100 token/s, Le Chat is 10x faster than popular models such as ChatGPT 4o, Sonnet 3.5, and DeepSeek R1" |
| H14 | Groq | Llama 3.1 8B (llama-3.1-8b-instant) | Groq LPU (GroqCloud) | speed column 'SPEED (T/SEC)' | nominal per-model speed in model list; conditions not stated | **560** tokens/s | undated (accessed 2026-11-14) | vendor claim | [S21] | "SPEED (T/SEC) ... llama-3.1-8b-instant ... 560" |
| H15 | Groq | Llama 3.3 70B (llama-3.3-70b-versatile) | Groq LPU (GroqCloud) | speed column 'SPEED (T/SEC)' | nominal per-model speed in model list; conditions not stated | **280** tokens/s | undated (accessed 2026-11-14) | vendor claim | [S21] | "SPEED (T/SEC) ... llama-3.3-70b-versatile ... 280" |
| H16 | Groq | gpt-oss-120b (openai/gpt-oss-120b) | Groq LPU (GroqCloud) | speed column 'SPEED (T/SEC)' | nominal per-model speed in model list; conditions not stated | **500** tokens/s | undated (accessed 2026-11-14) | vendor claim | [S21] | "SPEED (T/SEC) ... openai/gpt-oss-120b ... 500" |
| H17 | SambaNova | DeepSeek-R1 671B (full model; precision not stated) | SN40L RDU, one rack of 16 chips | output tokens/s per user | Artificial Analysis measured 'over 195 output token/s' on the same deployment; rack-level 20,000 tokens/s only a target | **198** tokens/s per user | 2025-02-13 | vendor claim (cites independent measurement) | [S22] | "SambaNova is the fastest platform running DeepSeek at 198 tokens per second per user" |
| H18 | Google Cloud | Qwen 3.5-397B MoE (peak FP8 spec quoted; run precision not stated) | TPU7x Ironwood, host with 4 chips, JAX serving stack | aggregate tokens/s per chip | decode-heavy: input 1K / output 8K, 64 concurrent requests; prefill-heavy 8K/1K gave 3,707 tokens/s/chip (token type not specified) | **677** tokens/s per chip | 2026-07-14 | vendor claim | [S23] | "Under the 1K/8K decode-heavy workload, our stack delivers an actual throughput of 677 tokens/s/chip." |
| H19 | Google Cloud (with vLLM/SGLang teams) | Kimi K3 (2.8T parameters) | TPU Ironwood (chip count not stated on page) | output tokens/s for a single user | precision and speculative decoding settings not stated for this figure; secondary reports say 16 chips with speculative decoding | **>700** tokens/s per user | 2026-10-20 | vendor claim | [S24] | "serving more than 700 tokens per second to a single user on Ironwood TPU" |
| H20 | AWS | not stated (Amazon Bedrock serving) | Trn3 UltraServer vs Trn2 UltraServer | ratio of output tokens per megawatt | 'at similar latency per user'; also 'up to 3x faster performance than Trainium2'; no absolute tokens/s published | **>5** x output tokens per MW vs Trn2 | 2025-12-02 | vendor claim | [S25] | "delivering up to 3× faster performance than Trainium2 with over 5× higher output tokens per megawatt" |
| H21 | NVIDIA | 2-trillion-parameter MoE, 400K input context | Vera Rubin NVL72 + Groq 3 LPX vs GB200 NVL72 | ratio of aggregate tokens/s per megawatt at a fixed per-user speed | operating point 400 tokens/s per user; 'up to'; methodology not published | **up to 35** x TPS per MW vs GB200 NVL72 | 2026-03-16 | vendor claim | [S26] | "delivers up to 35x higher TPS per megawatt at 400 TPS per user" |

## 3. MLPerf Inference v6.1 (datacenter, closed division)

Results published 2026-09-16, with a record 30 submitting organisations
[S31]. The LLM benchmarks with results in this round are Llama 3.1
8B, Llama 2 70B (99.9 % accuracy target), DeepSeek-R1 and gpt-oss-120b; Llama
3.1 405B and Mixtral 8x7B are still defined in the rules but have no v6.1
results in the summary table [S27]. Values are read from the
official summary spreadsheet; per-GPU values are our divisions. "Preview" means
the hardware was not yet available for purchase (Vera Rubin). Selection: the
best result per accelerator for each benchmark and scenario (M1, M2, M4, M5,
M7, M8, M11, M13), plus reference points: AMD's own submissions (M3, M12),
NVIDIA's available GB300 NVL72 rack as the baseline for Vera Rubin (M6, M9,
M10), the largest system (M14) and MLCommons' round summary (M15).

| ID | Company | Model | Hardware | Metric | Conditions | Value | Date | Kind | Src | Quote |
|---|---|---|---|---|---|---|---|---|---|---|
| M1 | Oracle (NVIDIA GPUs) | Llama 2 70B (99.9% accuracy target) | 8x GB300 (GB300 NVL72), TensorRT | aggregate tokens/s per system, Offline | Offline: all samples sent at once, no latency limit; = 16,532 tokens/s per GPU (our division); available; ID 6.1-0088 | **132,253** tokens/s per 8 GPUs | 2026-09-16 | MLPerf submission | [S27] | "summary.xlsx row 6.1-0088, llama2-70b-99.9, Offline, Tokens/s: 132253" |
| M2 | Oracle (NVIDIA GPUs) | Llama 2 70B (99.9%) | 8x GB300 (GB300 NVL72), TensorRT | aggregate tokens/s per system, Server | Poisson arrivals; p99 TTFT <= 2,000 ms, TPOT <= 200 ms (>= 5 tokens/s per user); = 15,998 tokens/s per GPU (our division); ID 6.1-0088 | **127,984** tokens/s per 8 GPUs | 2026-09-16 | MLPerf submission | [S27] | "summary.xlsx row 6.1-0088, llama2-70b-99.9, Server, Tokens/s: 127984" |
| M3 | AMD | Llama 2 70B (99.9%), MXFP4 GEMMs | 8x Instinct MI355X | aggregate tokens/s per system, Interactive | p99 TTFT <= 450 ms, TPOT <= 40 ms (>= 25 tokens/s per user); = 9,149 tokens/s per GPU (our division); best in category MiTAC 8x MI355X 74,385.6; ID 6.1-0003 | **73,191.5** tokens/s per 8 GPUs | 2026-09-16 | MLPerf submission | [S28] | "llama2-70b-99.9 Interactive MI355X 8 73,191.5 Tokens/s (table row)" |
| M4 | Cisco (NVIDIA GPUs) | Llama 3.1 8B | 8x B300-SXM-270GB, TensorRT | aggregate tokens/s per system, Server | p99 TTFT <= 2,000 ms, TPOT <= 100 ms (>= 10 tokens/s per user); = 21,744 tokens/s per GPU (our division); ID 6.1-0014 | **173,950** tokens/s per 8 GPUs | 2026-09-16 | MLPerf submission | [S27] | "summary.xlsx row 6.1-0014, llama3.1-8b, Server, Tokens/s: 173950" |
| M5 | MiTAC (AMD GPUs) | Llama 3.1 8B | 8x Instinct MI355X | aggregate tokens/s per system, Interactive | p99 TTFT <= 500 ms, TPOT <= 30 ms (>= 33 tokens/s per user); = 17,125 tokens/s per GPU (our division); ID 6.1-0069 | **136,999** tokens/s per 8 GPUs | 2026-09-16 | MLPerf submission | [S27] | "summary.xlsx row 6.1-0069, llama3.1-8b, Interactive, Tokens/s: 136999" |
| M6 | NVIDIA | DeepSeek-R1 | GB300 NVL72 (72 GPUs), TensorRT | aggregate tokens/s per rack, Offline | no latency limit; = 9,441 tokens/s per GPU (our division); available; ID 6.1-0074; 4 racks (288 GPUs, ID 6.1-0073) gave 2,705,130; best available per GPU: Oracle 8x GB300, 9,629 | **679,740** tokens/s per rack | 2026-09-16 | MLPerf submission | [S27] | "summary.xlsx row 6.1-0074, deepseek-r1, Offline, Tokens/s: 679740" |
| M7 | Nebius (NVIDIA GPUs) | DeepSeek-R1 | 36x VR200 (Vera Rubin NVL72), preview | aggregate tokens/s per GPU, Server | p99 TTFT <= 2,000 ms, TPOT <= 80 ms (>= 12.5 tokens/s per user); system 591,368 tokens/s; 'preview' (not yet available); ID 6.1-0107 | **16,427** tokens/s per GPU | 2026-09-16 | MLPerf submission | [S29] | "Nebius posted the leading server result at 16,427 tokens/s per GPU." |
| M8 | NVIDIA | DeepSeek-R1 | Vera Rubin NVL72 (72 GPUs), preview | aggregate tokens/s per rack, Interactive | p99 TTFT <= 1,500 ms, TPOT <= 15 ms (>= 66.7 tokens/s per user); speculative decoding (MTP) allowed; = 9,066 tokens/s per GPU (our division); ID 6.1-0106 | **652,750** tokens/s per rack | 2026-09-16 | MLPerf submission | [S27] | "summary.xlsx row 6.1-0106, deepseek-r1, Interactive, Tokens/s: 652750.1447708113" |
| M9 | NVIDIA | DeepSeek-R1 | GB300 NVL72 (72 GPUs), TensorRT | aggregate tokens/s per rack, Interactive | same limits as M8; = 3,521 tokens/s per GPU (our division); available; ID 6.1-0074; best available per GPU: Azure GB300 NVL72, 3,612 | **253,506** tokens/s per rack | 2026-09-16 | MLPerf submission | [S27] | "summary.xlsx row 6.1-0074, deepseek-r1, Interactive, Tokens/s: 253506" |
| M10 | NVIDIA | DeepSeek-R1 | Vera Rubin NVL72 vs GB300 NVL72 | ratio of throughput (vendor reading of its MLPerf v6.1 results) | scenario not specified; consistent with M8/M9 Interactive (652,750 / 253,506 = 2.57, our division) | **up to 2.5** x GB300 NVL72 | 2026-09-16 | vendor claim | [S30] | "On DeepSeek-R1, using the NVIDIA TensorRT-LLM library, throughput is up to 2.5x higher than GB300 NVL72." |
| M11 | CoreWeave (NVIDIA GPUs) | gpt-oss-120b | GB300 NVL72 (72 GPUs) | aggregate tokens/s per rack, Offline | no latency limit; = 16,635 tokens/s per GPU (our division); ID 6.1-0025 | **1,197,710** tokens/s per rack | 2026-09-16 | MLPerf submission | [S27] | "summary.xlsx row 6.1-0025, gpt-oss-120b, Offline, Tokens/s: 1197710" |
| M12 | AMD | gpt-oss-120b (8-bit activations, 4-bit weights in MoE) | 72x Instinct MI355X (9 nodes) | aggregate tokens/s per system, Server | p99 TTFT <= 3,000 ms, TPOT <= 80 ms (>= 12.5 tokens/s per user); = 13,395 tokens/s per GPU (our division); ID 6.1-0004; best per GPU in this scenario: CoreWeave GB300 NVL72, 16,118 | **964,468** tokens/s per 72 GPUs | 2026-09-16 | MLPerf submission | [S28] | "gpt-oss-120b Server MI355X 72 964,468 Tokens/s (table row)" |
| M13 | NVIDIA | gpt-oss-120b | GB300 NVL72 (72 GPUs), TensorRT | aggregate tokens/s per rack, Interactive | p99 TTFT <= 2,000 ms, TPOT <= 20 ms (>= 50 tokens/s per user); EAGLE3 speculative decoding allowed; = 9,296 tokens/s per GPU (our division); ID 6.1-0074 | **669,305** tokens/s per rack | 2026-09-16 | MLPerf submission | [S27] | "summary.xlsx row 6.1-0074, gpt-oss-120b, Interactive, Tokens/s: 669305" |
| M14 | Crusoe (AMD GPUs) | gpt-oss-120b | 512x Instinct MI355X (64 nodes), vLLM | aggregate tokens/s per system, Offline | largest LLM system in the round (Crusoe also ran DeepSeek-R1 on 512 GPUs: 2,901,950 Offline); = 11,229 tokens/s per GPU (our division); ID 6.1-0027 | **5,749,440** tokens/s per 512 GPUs | 2026-09-16 | MLPerf submission | [S28] | "gpt-oss-120b Offline MI355X 512 5,749,440 Tokens/s (table row)" |
| M15 | MLCommons (round summary) | DeepSeek-R1 | best per-accelerator result | improvement of best per-accelerator Server result vs v5.1 (Sept 2025) | per-accelerator normalisation used by MLCommons in its release | **5.7** x vs v5.1 | 2026-09-16 | MLPerf (MLCommons round summary) | [S31] | "For the Deepseek R1 test, the best per-accelerator server scenario result was 5.7x better compared to v5.1 one year ago." |

## 4. Independent measurements: Artificial Analysis

Methodology version 3.0.0 (2026-11-03) [S49]: single requests of about
1,000, 10,000 and 100,000 input tokens plus a multi-turn agentic workload, each
"under concurrent load"; benchmark runs every 6 hours from Google Cloud
us-central1; for each run the median of each workload is taken, and an
endpoint's value is the average of the run medians over the past 5 days. The
headline value averages the workloads. **Output Speed** counts reasoning tokens
and divides by the whole request duration, "so it includes time to first
token". Values were read from the data embedded in the provider pages on
2026-11-14 (the pages show them only as charts) and rounded to 0.1. We use the
1k-token workload as the closest analogue of a short chat request and give the
headline value in the conditions column.

| ID | Company | Model | Hardware | Metric | Conditions | Value | Date | Kind | Src | Quote |
|---|---|---|---|---|---|---|---|---|---|---|
| I1 | Cerebras (endpoint) | gpt-oss-120B | Cerebras | output tokens/s per request (AA 'Output Speed') | AA 1k-input workload; TTFT 0.21 s; headline (avg of 1k/10k/100k/multi-turn) 1,340.4; vendor claims 3,000 (H12) | **1,849.2** tokens/s | 2026-11-14 (5-day average) | independent measurement | [S32] | "cerebras_gpt-oss-120b ... "1k":{"outputSpeed":1849.2134032959616,"timeToFirstToken":0.20572415015625803}" |
| I2 | SambaNova (endpoint) | gpt-oss-120B | SN40L | output tokens/s per request | 1k workload; TTFT 0.90 s; headline 409.3 | **643.9** tokens/s | 2026-11-14 (5-day average) | independent measurement | [S32] | "sambanova_gpt-oss-120b ... "1k":{"outputSpeed":643.9233684704858,"timeToFirstToken":0.9038457337692634}" |
| I3 | Groq (endpoint) | gpt-oss-120B | Groq LPU | output tokens/s per request | 1k workload; TTFT 0.24 s; headline 376.4; 100k workload 292.9; Groq lists 500 (H16) | **459.6** tokens/s | 2026-11-14 (5-day average) | independent measurement | [S32] | "groq_gpt-oss-120b ... "1k":{"outputSpeed":459.5662626407094,"timeToFirstToken":0.24282136006247504}" |
| I4 | Amazon Bedrock (endpoint) | gpt-oss-120B | not disclosed | output tokens/s per request | 1k workload; TTFT 0.76 s; headline 92.0 | **115.0** tokens/s | 2026-11-14 (5-day average) | independent measurement | [S32] | "amazon-bedrock_gpt-oss-120b ... "1k":{"outputSpeed":114.9846358395273,"timeToFirstToken":0.7611488343528963}" |
| I5 | Groq (endpoint) | Llama 3.1 Instruct 8B | Groq LPU | output tokens/s per request | 1k workload; TTFT 0.21 s; headline 517.4; Groq lists 560 (H14) | **631.3** tokens/s | 2026-11-14 (5-day average) | independent measurement | [S33] | "groq_llama-3-1-instruct-8b ... "1k":{"outputSpeed":631.3374054839848,"timeToFirstToken":0.21245407200001398}" |
| I6 | CoreWeave (endpoint) | Llama 3.1 Instruct 8B | not disclosed (GPU cloud) | output tokens/s per request | 1k workload; TTFT 0.17 s; headline 123.0 | **148.5** tokens/s | 2026-11-14 (5-day average) | independent measurement | [S33] | "coreweave_llama-3-1-instruct-8b ... "1k":{"outputSpeed":148.482534005477,"timeToFirstToken":0.16836113350011317}" |
| I7 | Groq (endpoint) | Llama 3.3 Instruct 70B | Groq LPU | output tokens/s per request | 1k workload; TTFT 0.31 s; headline 210.7; Groq lists 280 (H15) | **321.7** tokens/s | 2026-11-14 (5-day average) | independent measurement | [S34] | "groq_llama-3-3-instruct-70b ... "1k":{"outputSpeed":321.7029186913106,"timeToFirstToken":0.30538895335299177}" |
| I8 | Anthropic (first-party API) | Claude Opus 5.5 (medium effort, standard speed) | not disclosed | output tokens/s per request (includes reasoning tokens) | 1k workload; TTFT 12.1 s (includes thinking); headline 105.4; max effort headline 113.8 with TTFT 396 s | **109.8** tokens/s | 2026-11-14 (5-day average) | independent measurement | [S35] | "anthropic_claude-opus-5-5-medium ... "1k":{"outputSpeed":109.8368412015205,"timeToFirstToken":12.13091486505884}" |
| I9 | Anthropic (first-party API) | Claude Haiku 5.5 (medium effort) | not disclosed | output tokens/s per request (includes reasoning tokens) | 1k workload; TTFT 7.55 s (includes thinking); headline 220.6 | **215.4** tokens/s | 2026-11-14 (5-day average) | independent measurement | [S36] | "anthropic_claude-haiku-5-5-medium ... "1k":{"outputSpeed":215.38612314859026,"timeToFirstToken":7.5509346325293905}" |
| I10 | OpenAI (first-party API, Standard tier) | GPT-6.1 Sol (medium effort) | not disclosed | output tokens/s per request (includes reasoning tokens) | 1k workload; TTFT 5.04 s; headline 49.4 | **48.1** tokens/s | 2026-11-14 (5-day average) | independent measurement | [S37] | "openai_gpt-6-1-sol-medium ... "1k":{"outputSpeed":48.121876126985605,"timeToFirstToken":5.042355903382363}" |
| I11 | OpenAI (first-party API, Ultrafast tier) | GPT-6.1 Sol (max effort) | not disclosed | output tokens/s per request (includes reasoning tokens) | 1k workload; TTFT 34.3 s; headline 205.4; Standard tier, same effort: 43.5 at 1k, so 221.1 / 43.5 = 5.1x (our division); Fast tier 66.8 | **221.1** tokens/s | 2026-11-14 (5-day average) | independent measurement | [S37] | "openai_gpt-6-1-sol_ultrafast ... "1k":{"outputSpeed":221.12051856324157,"timeToFirstToken":34.288764125625114}" |
| I12 | Google (AI Studio) | Gemini 4 Hydrogen (high) | not disclosed | output tokens/s per request (includes reasoning tokens) | 1k workload; TTFT 10.8 s; headline 170.7 | **216.5** tokens/s | 2026-11-14 (5-day average) | independent measurement | [S38] | "google_gemini-4-hydrogen-high_ai-studio ... "1k":{"outputSpeed":216.5208524751249,"timeToFirstToken":10.824932160374951}" |
| I13 | xAI (first-party API) | Grok 4.7 (high) | not disclosed | output tokens/s per request (includes reasoning tokens) | 1k workload; TTFT 12.75 s; headline 67.3 | **61.2** tokens/s | 2026-11-14 (5-day average) | independent measurement | [S39] | "xai_grok-4-7-high ... "1k":{"outputSpeed":61.167280037395265,"timeToFirstToken":12.753585263375038}" |
| I14 | DeepSeek (first-party API) | DeepSeek V4 Pro (0813) | not disclosed | output tokens/s per request (includes reasoning tokens) | 1k workload; TTFT 1.02 s (first reasoning token); time to first answer token (headline) 56.8 s; headline speed 82.6 | **83.6** tokens/s | 2026-11-14 (5-day average) | independent measurement | [S40] | "deepseek_deepseek-v4-pro-0813 ... "1k":{"outputSpeed":83.62062484019128,"timeToFirstToken":1.023799640593782}" |
| I15 | Mistral (first-party API) | Mistral Large 4 | not disclosed | output tokens/s per request (includes reasoning tokens) | 1k workload; TTFT 1.46 s; headline 104.4 | **110.3** tokens/s | 2026-11-14 (5-day average) | independent measurement | [S41] | "mistral_mistral-large-4 ... "1k":{"outputSpeed":110.29326899268098,"timeToFirstToken":1.4611459947500043}" |
| I16 | Inception (first-party API) | Mercury 2.5 (diffusion LLM) | not disclosed | output tokens/s per request | 1k workload; TTFT 2.28 s; headline 522.2; vendor claims 1,000+ for Mercury 2 (P10; different model version) | **727.3** tokens/s | 2026-11-14 (5-day average) | independent measurement | [S42] | "inception_mercury-2-5 ... "1k":{"outputSpeed":727.341644943033,"timeToFirstToken":2.276268026375055}" |

**Cross-check of vendor claims against Artificial Analysis (1k workload):**

| Claim | Vendor figure | Artificial Analysis |
|---|---|---|
| gpt-oss-120B on Cerebras | 3,000 tokens/s (H12) | 1,849.2 (I1) |
| gpt-oss-120B on Groq | 500 tokens/s (H16) | 459.6 (I3) |
| Llama 3.1 8B on Groq | 560 tokens/s (H14) | 631.3 (I5) |
| Llama 3.3 70B on Groq | 280 tokens/s (H15) | 321.7 (I7) |
| Inception Mercury | 1,000+ tokens/s, Mercury 2 (P10) | 727.3, Mercury 2.5 (I16) |
| OpenAI Ultrafast, API | "up to 6X" (P3, secondary) | 5.1x Standard for GPT-6.1 Sol, max effort (I11, our division) |
| SambaNova DeepSeek-R1 | 198 tokens/s per user (H17) | "over 195" (quoted by SambaNova, 2025) |

**GPT-6.1 Sol in the figure of Section 7.8.** The figure
(`figures/ch07-vendor.tex`, written by `code/ch07/mkvendor.py`) shows both
service tiers at maximum effort, so that
its two rows differ in the tier alone: 221.1 tokens/s on the Ultrafast tier
(I11) and 43.5 on the Standard tier (the value in the conditions of I11).
I10, the Standard tier at medium effort (48.1), is not plotted, and the text
of Section 7.8 gives the range of the makers' own services as 44 to 217
tokens/s.

## Caveats for comparison

1. **Per-user is not per-GPU.** A laptop running one request has per-user speed
   equal to its total throughput. A datacenter GPU's aggregate is shared by tens
   to hundreds of streams (H6: about 200 at 50 tokens/s each). Compare the
   book's numbers with per-user figures (P, H1, H3, H9, H10, I rows), never with
   per-GPU, per-rack or MLPerf totals.
2. **Where the clock starts.** llama.cpp's generation rate excludes prompt
   processing. Vendor per-user figures usually time the decode phase on the
   server. Artificial Analysis divides by the full request time including TTFT
   and the network round trip, under concurrent load, so long prompts lower its
   figure (Groq gpt-oss-120B: 459.6 tokens/s at 1k input, 292.9 at 100k, I3).
3. **Load.** Record per-user figures are measured at concurrency 1 (H1). MLPerf
   Server and Interactive impose random arrivals, and Artificial Analysis
   measures under load; a shared service at busy hours is slower than its
   record.
4. **"Up to" and content.** Speculative decoding (EAGLE-3 in H3, H8; allowed in
   MLPerf Interactive for DeepSeek-R1 and gpt-oss-120b) and diffusion models
   (P5, P10, I16) emit several tokens per step, and how many depends on how
   predictable the text is: on the same hardware NVIDIA measured a median of
   4,767 tokens/s on coding problems against 3,431 on Artificial Analysis'
   workload (H10).
5. **Tokens are not words, and tokenizers differ.** Mistral states ~1,000
   words/s (P8), Cerebras >1,100 tokens/s for the same service (H13). Different
   models split the same text into different numbers of tokens, so equal
   tokens/s across models is not equal text per second.
6. **Reasoning tokens.** For reasoning models the output-speed figures count
   hidden thinking tokens, and TTFT can include minutes of thinking: Claude Opus
   5.5 at maximum effort has a headline TTFT of 396 s against 12.1 s at medium
   effort (I8). The effort setting and the service tier (OpenAI Standard / Fast /
   Ultrafast, Anthropic fast mode) change the speed of the same model.
7. **Precision and accuracy.** Vendor figures use FP4 (H1), FP8 (H3) or MXFP4
   (M3) or do not say; local GGUF quantisation is different again. MLPerf
   requires 99 % or 99.9 % of the reference accuracy; vendor claims carry no
   such check.
8. **Model size and architecture.** Mixture-of-experts models activate only part
   of their weights per token (DeepSeek-V3: 671B parameters, 37B activated, P9),
   so per-token work follows the active, not the total, parameter count.
   Compare speeds only for the same model (or the same model class and size).
9. **What counts as one device.** Per-GPU figures for NVL72 racks are our
   divisions and ignore the CPUs and NVLink switches in the rack. A Cerebras
   wafer, a Groq LPU and a TPU chip are not GPUs, and a single fast stream on
   them may occupy many chips. Per-megawatt (H20, H21) or per-rack figures, or
   cost, are fairer normalisations across architectures.
10. **Availability and date.** MLPerf "preview" systems (M7, M8) were not yet
    for sale. The figures span December 2024 to November 2026 and different
    software versions; MLCommons reports a 5.7x per-accelerator gain on
    DeepSeek-R1 in one year (M15). Artificial Analysis changed its methodology
    on 2026-11-03, so the Artificial Analysis numbers quoted by vendors before
    then (H3, H10, H11, H17) used the earlier method.
11. **Undated pages.** The Groq and Cerebras model lists and the Anthropic and
    OpenAI fast-mode docs are living pages; the values are as read on
    2026-11-14.
12. **Ratios without a baseline.** P1, P2, P3, H20 and H21 give only ratios.
    Artificial Analysis data can anchor them: Claude Opus 5.5 at standard speed
    runs at about 110 tokens/s (I8), so "up to 2.5x" would be at most about 275
    tokens/s (our arithmetic, not a measurement).

## Not verified, or dropped

- **OpenAI Ultrafast:** "up to 300 generated tokens per second", "up to 8X ... in
  Codex and up to 6X ... through the API", and an August 2026 GPT-5.6 Sol
  preview at "up to 14X" / 750 output tokens/s appear only in VentureBeat
  [S3] and in search snippets of OpenAI's X posts; openai.com
  returned HTTP 403 to our fetch tool and OpenAI's Ultrafast docs page gives no
  number [S43]. Kept as P3, labelled secondary.
- **GPT-5.3-Codex-Spark:** "over 1200 tokens per second" (2026-02-20) is relayed
  by a forum user [S44]; "time to first token cut in half"
  appears only in secondary coverage.
- **xAI:** no verifiable tokens/s figure. The Grok Code Fast 1 post (x.ai,
  2025-08-28) shows a chart with "Tokens per second (TPS)" and "190", but the
  page text does not tie the value to a model; secondary reports say about 160.
  Dropped. Grok 4.7 is covered by I13.
- **Google Gemini 4 Hydrogen:** "2.5x faster than Gemini 3.8 Flash", attributed
  to Sundar Pichai in secondary coverage; no Google primary source found.
  Dropped (I12 kept).
- **Kimi K3 on Ironwood (H19):** the chip count (16) and a comparison with 452
  tokens/s on 16 GB200 GPUs appear only in secondary summaries.
- **AWS Bedrock latency-optimized inference:** "60 % faster" Claude 3.5 Haiku and
  Llama 3.1 405B timings (3.9 s vs 13.9 s) are in secondary reports only; AWS's
  own announcement has no numbers [S47].
- **Meta Llama API (P6):** the Cerebras newsroom item is a republished news
  article; its "18x" baseline (OpenAI vs "traditional GPU-based solutions") is
  not reconciled in the text.
- **SemiAnalysis InferenceX** Ironwood vs B200/B300 (9,364 vs 8,903 / 8,925
  total tokens/s per chip at 20 tokens/s per user, Qwen 3.5 397B FP8): the page
  we read was marked as an unofficial copy. Dropped.
- **NVIDIA H5:** the post does not give the methodology for the 60,000 / 1,000
  pair; NVIDIA's developer blog notes that InferenceMAX v1 tested only
  concurrencies 4-64 [S14].
- **MLPerf latency limits** are from the master branch of the rules (there is no
  v6.1 tag); AMD's v6.1 write-up independently states the gpt-oss-120b limits
  of 3 s TTFT and 80 ms TPOT [S28].

## Spot-check for the book (2026-11-14, about 10:40-11:00 UTC)

Before the figures went into Section 7.8 of the book, the following rows were
re-read at their primary sources on 2026-11-14. "Holds" means the value, the
metric and the conditions quoted above were found again as stated.

| IDs | Source | Checked | Result |
|---|---|---|---|
| P1 | S1 Anthropic fast mode docs | 2026-11-14 | holds ("up to 2.5x higher output tokens per second"; OTPS, not TTFT) |
| P5 | S5 Gemini Diffusion page | 2026-11-14 | holds (1479 tokens/s, 0.84 s overhead, average across evals) |
| P9 | S9 DeepSeek-V3 news | 2026-11-14 | holds (60 tokens/s, dated 2024-12-26) |
| P10, P11 | S10 Inception, Mercury 2 | 2026-11-14 | holds (1000+ tokens/s on H100s; TTFT <300 ms appears only in the page description) |
| H1, H2 | S11 NVIDIA DeepSeek-R1 on DGX B200 | 2026-11-14 | holds (concurrency 1 / MAX, FP4, ISL 1,024 / OSL 2,048) |
| H3, H4 | S12 NVIDIA Llama 4 Maverick | 2026-11-14 | holds (EAGLE-3, FP8, measured by Artificial Analysis; 72,000 TPS/server) |
| H6, H7 | S14 NVIDIA InferenceMAX | 2026-11-14 | holds (H7 only in the alt text of Figure 1) |
| H9 | S16 NVIDIA DeepSeek-V4-Pro | 2026-11-14 | holds (>150 tokens/s/user, SemiAnalysis InferenceX) |
| H10 | S17 NVIDIA Groq 3 LPX | 2026-11-14 | holds (3,431 at 100K, 3,382 at 10K, 4,767 coding median) |
| H11 | S18 Cerebras Maverick press release | 2026-11-14 | holds (2,522 vs 1,038; title "Cerebras Beats NVIDIA Blackwell in Llama 4 Maverick Inference") |
| H12 | S19 Cerebras gpt-oss-120B | 2026-11-14 | holds (3,000 tokens/s at full 128k context; the footer's "third-party benchmarking or internal testing" refers to comparisons, not to this figure) |
| H14, H15, H16 | S21 GroqCloud models | 2026-11-14 | holds (560, 280, 500) |
| H17 | S22 SambaNova DeepSeek-R1 | 2026-11-14 | holds (198 per user; AA "over 195"; 16 RDUs in one rack) |
| H19 | S24 Google, vLLM/SGLang on TPU | 2026-11-14 | holds (>700 tokens/s to a single user); the page gives no chip count and does not say whether speculative decoding was used |
| M1, M2, M4, M5, M6, M9, M11, M13 | S27 MLPerf v6.1 summary.xlsx | 2026-11-14 | holds (cell values identical) |
| MLPerf limits table | S48 rules | 2026-11-14 | holds |
| I1-I15 (except I11 headline) | S32-S41 Artificial Analysis | 2026-11-14, ~10:40 UTC | hold within 2.1 %: the five-day averages move between reads (I1 1,849.2 -> 1,834.0; I3 459.6 -> 460.0; I4 115.0 -> 114.6; I8 109.8 -> 109.3; I9 215.4 -> 215.0; I10 48.1 -> 47.9; I11 221.1 -> 221.3, standard tier at max effort 43.5 -> 43.8; I12 216.5 -> 212.1; I13 61.2 -> 60.1; I14 83.6 -> 83.6; I15 110.3 -> 110.4); I5 631.3 and I6 148.5 unchanged. The book uses the values compiled above. |
| Methodology | S49 Artificial Analysis v3.0.0 | 2026-11-14 | holds (Output Speed over the request's full duration, includes TTFT and reasoning tokens; every 6 h from Cloud Run us-central1; median per run, 5-day average) |

The cited Google page does give the parameter count of Kimi K3 in H19 ("the
2.8T-parameter Kimi K3 model").

Second pass (2026-11-14, about 14:30 UTC), the rows not re-checked
above. Each source was fetched again and the recorded value searched for; for
the small numbers (P2, H20, H21, M10, M15) the quoted sentence was found
verbatim.

| IDs | Source | Checked | Result |
|---|---|---|---|
| P2 | S2 OpenAI fast mode docs | 2026-11-14 | holds ("up to 2.5x faster speeds") |
| P3 | S3 VentureBeat (secondary) | 2026-11-14 | holds as a secondary source; OpenAI's page still not readable |
| P4 | S4 Cerebras, Codex-Spark | 2026-11-14 | holds (">1,000 tokens/s") |
| P6 | S6 Cerebras, Llama API | 2026-11-14 | holds (2,600) |
| P7 | S7 Groq, Llama API | 2026-11-14 | holds (625) |
| P8 | S8 Mistral Le Chat | 2026-11-14 | holds (1,000) |
| H5 | S13 NVIDIA InferenceMAX blog | 2026-11-14 | holds (60,000 per GPU) |
| H8 | S15 Baseten gpt-oss | 2026-11-14 | holds (650) |
| H13 | S20 Cerebras, Le Chat | 2026-11-14 | holds (1,100) |
| H18 | S23 Google, Qwen 3.5 on Ironwood | 2026-11-14 | holds (677) |
| H20 | S25 AWS Trn3 | 2026-11-14 | holds ("over 5x higher output tokens per megawatt") |
| H21 | S26 NVIDIA Groq 3 LPX | 2026-11-14 | holds ("up to 35x higher TPS per megawatt at 400 TPS per user") |
| M3, M12, M14 | S28 AMD ROCm blog | 2026-11-14 | holds (73,191.5; 964,468; 5,749,440) |
| M7 | S29 Nebius | 2026-11-14 | holds (16,427) |
| M8 | S27 MLPerf v6.1 summary.xlsx | 2026-11-14 | holds (cell 652750.1447708113 on sheet 1) |
| M10 | S30 NVIDIA Vera Rubin MLPerf | 2026-11-14 | holds ("up to 2.5x higher than GB300 NVL72") |
| M15 | S31 MLCommons v6.1 results | 2026-11-14 | holds ("5.7x better compared to v5.1") |
| I16 | S42 Artificial Analysis, Mercury 2.5 | 2026-11-14, ~14:30 UTC | holds within the drift of the five-day average: 727.3 -> 719.7 (-1.0 %); TTFT 2.28 -> 2.29 s |

Every row of this file has now been re-read at its source on 2026-11-14.

## Sources

All accessed 2026-11-14.

- **S1** Anthropic, Claude Platform docs, "Fast mode" (undated page). <https://platform.claude.com/docs/en/build-with-claude/fast-mode> (accessed 2026-11-14)
- **S2** OpenAI API docs, "Fast mode" (undated page). <https://developers.openai.com/api/docs/guides/fast-mode> (accessed 2026-11-14)
- **S3** VentureBeat, C. Franzen, GPT-6.1 Sol / Ultrafast, 2026-09-29 (secondary; cites https://openai.com/index/devday-2026-recap/, which returned HTTP 403). <https://venturebeat.com/technology/openais-gpt-6-1-sol-offers-astra-like-performance-at-1-5th-price-a-new-ultrafast-tier-clocks-at-300-tokens-per-second> (accessed 2026-11-14)
- **S4** Cerebras blog, "OpenAI GPT-5.3-Codex-Spark Powered by Cerebras", 2026-02-12. <https://www.cerebras.ai/blog/openai-codexspark> (accessed 2026-11-14)
- **S5** Google DeepMind, "Gemini Diffusion" model page (undated). <https://deepmind.google/models/gemini-diffusion/> (accessed 2026-11-14)
- **S6** Cerebras newsroom, "Meta unleashes Llama API running 18x faster than OpenAI", 2025-04-29 (republished news article). <https://www.cerebras.ai/news/meta-unleashes-llama-api-running-18x-faster-than-openai-cerebras-partnership-delivers-2-600> (accessed 2026-11-14)
- **S7** Groq newsroom, "Meta and Groq Collaborate to Deliver Fast Inference for the Official Llama API", 2025-04-29. <https://groq.com/news/meta-and-groq-collaborate-to-deliver-fast-inference-for-the-official-llama-api> (accessed 2026-11-14)
- **S8** Mistral AI, "The all new le Chat", 2025-02-06. <https://mistral.ai/news/all-new-le-chat> (accessed 2026-11-14)
- **S9** DeepSeek API docs news, "Introducing DeepSeek-V3", 2024-12-26. <https://api-docs.deepseek.com/news/news1226> (accessed 2026-11-14)
- **S10** Inception blog, "Mercury 2: the first reasoning model fast enough to pick up the phone" (page dated 2026-10-29). <https://inceptionlabs.ai/blog/mercury-2-the-first-reasoning-model-fast-enough-to-pick-up-the-phone> (accessed 2026-11-14)
- **S11** NVIDIA Technical Blog, "NVIDIA Blackwell Delivers World-Record DeepSeek-R1 Inference Performance", 2025-03-18. <https://developer.nvidia.com/blog/nvidia-blackwell-delivers-world-record-deepseek-r1-inference-performance/> (accessed 2026-11-14)
- **S12** NVIDIA Technical Blog, "Blackwell Breaks the 1,000 TPS/User Barrier With Meta's Llama 4 Maverick", 2025-05-22. <https://developer.nvidia.com/blog/blackwell-breaks-the-1000-tps-user-barrier-with-metas-llama-4-maverick/> (accessed 2026-11-14)
- **S13** NVIDIA blog, "NVIDIA Blackwell Raises Bar in New InferenceMAX Benchmarks", 2025-10-09. <https://blogs.nvidia.com/blog/blackwell-inferencemax-benchmark-results/> (accessed 2026-11-14)
- **S14** NVIDIA Technical Blog, "NVIDIA Blackwell Leads on New SemiAnalysis InferenceMAX Benchmarks", 2025-10-13. <https://developer.nvidia.com/blog/nvidia-blackwell-leads-on-new-semianalysis-inferencemax-benchmarks/> (accessed 2026-11-14)
- **S15** Baseten blog, "How we made the fastest GPT-OSS on NVIDIA GPUs 60% faster", 2025-10-24 (updated 2026-11-02). <https://www.baseten.co/blog/how-we-made-the-fastest-gpt-oss-on-nvidia-gpus-60-percent-faster/> (accessed 2026-11-14)
- **S16** NVIDIA Technical Blog, "Build with DeepSeek V4 Using NVIDIA Blackwell and GPU-Accelerated Endpoints", 2026-04-24. <https://developer.nvidia.com/blog/build-with-deepseek-v4-using-nvidia-blackwell-and-gpu-accelerated-endpoints> (accessed 2026-11-14)
- **S17** NVIDIA Technical Blog, "How NVIDIA Groq 3 LPX Unlocks Ultrafast Interactivity at Long Context on NVIDIA Vera Rubin", 2026-08-24. <https://developer.nvidia.com/blog/how-nvidia-groq-3-lpx-unlocks-ultrafast-interactivity-at-long-context-on-nvidia-vera-rubin/> (accessed 2026-11-14)
- **S18** Cerebras press release, Llama 4 Maverick, 2025-05-28. <https://www.cerebras.ai/press-release/maverick> (accessed 2026-11-14)
- **S19** Cerebras blog, "Cerebras launches OpenAI's gpt-oss-120B at a blistering 3,000 tokens/sec", 2025-08-05. <https://www.cerebras.ai/blog/cerebras-launches-openai-s-gpt-oss-120b-at-a-blistering-3-000-tokens-sec> (accessed 2026-11-14)
- **S20** Cerebras blog, Mistral Le Chat, 2025-02-06. <https://www.cerebras.ai/blog/mistral-le-chat> (accessed 2026-11-14)
- **S21** GroqCloud docs, "Supported Models" (undated page). <https://console.groq.com/docs/models> (accessed 2026-11-14)
- **S22** SambaNova press release, "SambaNova Launches the Fastest DeepSeek-R1 671B with the Highest Efficiency", 2025-02-13. <https://sambanova.ai/press/fastest-deepseek-r1-671b-with-highest-efficiency> (accessed 2026-11-14)
- **S23** Google Developers Blog, "Systems Engineering Playbook: Optimizing Qwen 3.5-397B MoE on Ironwood (TPU7x)", 2026-07-14. <https://developers.googleblog.com/systems-engineering-playbook-optimizing-qwen-35-397b-moe-on-ironwood-tpu7x/> (accessed 2026-11-14)
- **S24** Google Developers Blog, "Announcing New vLLM and SGLang Inference Engines on TPU", 2026-10-20. <https://developers.googleblog.com/announcing-new-vllm-and-sglang-inference-engines-on-tpu/> (accessed 2026-11-14)
- **S25** AWS What's New, "Announcing Amazon EC2 Trn3 UltraServers", 2025-12-02. <https://aws.amazon.com/about-aws/whats-new/2025/12/amazon-ec2-trn3-ultraservers> (accessed 2026-11-14)
- **S26** NVIDIA Technical Blog, "Inside NVIDIA Groq 3 LPX", 2026-03-16. <https://developer.nvidia.com/blog/inside-nvidia-groq-3-lpx-the-low-latency-inference-accelerator-for-the-nvidia-vera-rubin-platform> (accessed 2026-11-14)
- **S27** MLCommons, MLPerf Inference v6.1 results summary spreadsheet (datacenter, closed), linked from https://mlcommons.org/benchmarks/inference-datacenter/. <https://github.com/mlcommons/inference_results_v6.1/raw/refs/heads/main/summary.xlsx> (accessed 2026-11-14)
- **S28** AMD ROCm Blogs, "Technical Dive into AMD MLPerf Inference v6.1 Submission", 2026-09-17. <https://rocm.blogs.amd.com/artificial-intelligence/mlperf-inf-v6.1/README.html> (accessed 2026-11-14)
- **S29** Nebius blog, "MLPerf Inference v6.1 Results: NVIDIA Vera Rubin NVL72", 2026-09-16. <https://nebius.com/blog/posts/mlperf-inference-v6-1-results> (accessed 2026-11-14)
- **S30** NVIDIA blog, Vera Rubin NVL72 in MLPerf Inference v6.1, 2026-09-16. <https://blogs.nvidia.com/blog/vera-rubin-nvl72-mlperf-inference/> (accessed 2026-11-14)
- **S31** MLCommons, "MLCommons Sets Participation Record with New MLPerf Inference v6.1 Benchmark Results", 2026-09-16. <https://mlcommons.org/2026/09/mlperf-inference-v6-1-results/> (accessed 2026-11-14)
- **S32** Artificial Analysis, gpt-oss-120B API providers. <https://artificialanalysis.ai/models/gpt-oss-120b/providers> (accessed 2026-11-14)
- **S33** Artificial Analysis, Llama 3.1 Instruct 8B API providers. <https://artificialanalysis.ai/models/llama-3-1-instruct-8b/providers> (accessed 2026-11-14)
- **S34** Artificial Analysis, Llama 3.3 Instruct 70B API providers. <https://artificialanalysis.ai/models/llama-3-3-instruct-70b/providers> (accessed 2026-11-14)
- **S35** Artificial Analysis, Claude Opus 5.5 API providers. <https://artificialanalysis.ai/models/claude-opus-5-5/providers> (accessed 2026-11-14)
- **S36** Artificial Analysis, Claude Haiku 5.5 API providers. <https://artificialanalysis.ai/models/claude-haiku-5-5/providers> (accessed 2026-11-14)
- **S37** Artificial Analysis, GPT-6.1 Sol API providers. <https://artificialanalysis.ai/models/gpt-6-1-sol/providers> (accessed 2026-11-14)
- **S38** Artificial Analysis, Gemini 4 Hydrogen API providers. <https://artificialanalysis.ai/models/gemini-4-hydrogen/providers> (accessed 2026-11-14)
- **S39** Artificial Analysis, Grok 4.7 API providers. <https://artificialanalysis.ai/models/grok-4-7/providers> (accessed 2026-11-14)
- **S40** Artificial Analysis, DeepSeek V4 Pro API providers. <https://artificialanalysis.ai/models/deepseek-v4-pro/providers> (accessed 2026-11-14)
- **S41** Artificial Analysis, Mistral Large 4 API providers. <https://artificialanalysis.ai/models/mistral-large-4/providers> (accessed 2026-11-14)
- **S42** Artificial Analysis, Mercury 2.5 API providers. <https://artificialanalysis.ai/models/mercury-2-5/providers> (accessed 2026-11-14)
- **S43** OpenAI API docs, "Ultrafast mode" (undated page; no speed figure). <https://developers.openai.com/api/docs/guides/ultrafast-mode> (accessed 2026-11-14)
- **S44** OpenAI Developer Community thread (user post relaying an OpenAI staff post), 2026-02-12 / 2026-02-20. <https://community.openai.com/t/gpt-5-3-codex-spark-research-preview-with-1000-tokens-per-second/1374091> (accessed 2026-11-14)
- **S45** Meta AI blog, LlamaCon announcements, 2025-04-29 (no speed figure). <https://ai.meta.com/blog/llamacon-llama-news/> (accessed 2026-11-14)
- **S46** Cerebras blog, "Blackwell vs Cerebras", 2025-11-06 (competitor's account of Baseten result). <https://www.cerebras.ai/blog/blackwell-vs-cerebras> (accessed 2026-11-14)
- **S47** AWS What's New, latency-optimized inference in Amazon Bedrock, 2024-12-02 (no numeric figure). <https://aws.amazon.com/about-aws/whats-new/2024/12/latency-optimized-inference-foundation-models-amazon-bedrock> (accessed 2026-11-14)
- **S48** MLCommons, MLPerf Inference rules (master branch, read 2026-11-14; benchmark table and scenario table). <https://github.com/mlcommons/inference_policies/blob/master/inference_rules.adoc> (accessed 2026-11-14)
- **S49** Artificial Analysis, "Performance Benchmarking Methodology" (Version 3.0.0, 2026-11-03). <https://artificialanalysis.ai/methodology/performance-benchmarking> (accessed 2026-11-14)
