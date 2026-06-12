# Local-LLM Runtime & Orchestration Architecture
**Research date:** 2026-06-09  
**Hardware:** Machine A — MBP M5 Pro 64GB (primary); Machine B — MBP M4 Pro 24GB (LAN/idle)  
**Constraint:** Zero idle penalty — idle footprint approaches zero; heavy compute only during active tasks.  
**Already installed:** Ollama (official app) with gemma4:26b and gemma4:31b.

---

## 1. Ollama

### 1.1 Idle RAM — "just having it" cost

The Ollama app installs a **menu-bar process + a background HTTP daemon** (`ollama serve`) that starts at login. The daemon itself consumes roughly **50–100 MB of RAM** when no model is loaded. When models are idle but still loaded, each model holds its **full weight allocation + KV cache** in unified memory — there is no partial unload.

Known issue: The macOS app has a history of lingering processes when the window is closed without quitting from the menu bar. The IBM [`ollama-bar`](https://github.com/IBM/ollama-bar) helper gives explicit start/stop control. Running Ollama headlessly via `launchctl` (without the GUI app) reduces the background footprint to the daemon alone (~50 MB).

### 1.2 Auto-unload / keep-alive

| Setting | Value | Effect |
|---------|-------|--------|
| `OLLAMA_KEEP_ALIVE` (env, server-wide) | Default: `5m` | Model unloads 5 min after last request |
| `keep_alive` (per-request API param) | Any duration string | Overrides env; `0` = unload immediately after response |
| `OLLAMA_KEEP_ALIVE=-1` | Infinite | Model stays loaded until Ollama restarts |
| `OLLAMA_KEEP_ALIVE=0` | Zero | Unload immediately after every response (max memory savings) |

**For the zero-idle-penalty constraint:** set `OLLAMA_KEEP_ALIVE=0` globally (or per-request `keep_alive: "0"`) and accept a cold-start reload penalty of ~5–15s for large models. Alternatively, set `OLLAMA_KEEP_ALIVE=10m` to absorb a burst of rapid follow-up queries without reloading.

### 1.3 Context window / num_ctx (critical for gemma4)

Gemma4's native context window is **256K tokens**. Ollama's global default is 2048 tokens; if a model's Modelfile specifies a larger default, Ollama honors it — and for gemma4 this means the full 256K is pre-allocated unless overridden.

**RAM cost of KV cache at various context sizes (gemma4:31b, FP16 KV):**

| num_ctx | Approx. KV cache RAM |
|---------|---------------------|
| 4K | ~0.7 GB |
| 8K | ~1.4 GB |
| 32K | ~5.7 GB |
| 128K | ~23 GB |
| 256K | ~46 GB (unworkable on 64 GB with 34 GB weights) |

**Control hierarchy** (highest wins):
1. Per-request API: `"options": {"num_ctx": 8192}`
2. Custom Modelfile: `PARAMETER num_ctx 8192`
3. Env: `OLLAMA_CONTEXT_LENGTH=8192`

**Recommendation:** Create a custom Modelfile for gemma4 variants with `PARAMETER num_ctx 8192` as a sane default. Users who need more context can override per-request. This alone saves ~40 GB of unified memory reservation compared to the 256K default.

Additional levers:
- `OLLAMA_FLASH_ATTENTION=1` — reduces KV cache VRAM by 30–50% (enable by default)
- KV cache quantization via `OLLAMA_KV_CACHE_TYPE=q8_0` (halves KV RAM with minimal quality loss) or `q4_0` (quarters it)

### 1.4 MLX backend (as of Ollama 0.19, March 2026)

Ollama 0.19 ships an **MLX backend for Apple Silicon** in preview. On M5 hardware with the MLX path:
- Prefill speed: **~1,810 tok/s** (vs 1,154 tok/s on the previous Metal backend)
- Decode speed: **~112 tok/s** (vs 58 tok/s)
- **Requirement:** 32 GB or more unified memory — Machine A (64 GB) qualifies; Machine B (24 GB) does **not**

Enable: `export OLLAMA_USE_MLX=1` before starting Ollama (may be auto-detected on qualifying hardware in newer builds).

### 1.5 OpenAI-compatible endpoint

- Default port: **11434**
- Base URL: `http://localhost:11434/v1`
- Full OpenAI chat/completions API compatibility
- No conflict with LM Studio (port 1234) or mlx-lm server (port 8080) — all three can run simultaneously

### 1.6 Model storage

Default path: `~/.ollama/models/`  
Override: `export OLLAMA_MODELS=/path/to/shared/models`

Ollama stores models as **GGUF blobs** (in a content-addressed layout under `~/.ollama/models/blobs/`). It does **not** use a flat GGUF file path — the blob store is not directly compatible with LM Studio's expected path. Sharing requires symlinking (see §6 on sharing strategies).

---

## 2. LM Studio

### 2.1 Idle RAM — "just having it" cost

LM Studio is an **Electron app**. Its background footprint includes:
- Electron renderer + main process: **~254 MB even with no model loaded** (multiple GPU helper processes)
- The `lmstudio` CLI daemon (if enabled at login): additional ~50–100 MB

A known regression: repeated load/unload cycles can leave **20–40 GB of allocated memory unreleased** after 4–5 swaps (not visible in Activity Monitor). Requires quitting and restarting the app to reclaim. This makes LM Studio poorly suited for automated/scripted model cycling.

### 2.2 Auto-unload / TTL

LM Studio has a proper TTL system (added in recent releases):

| Method | Default | Notes |
|--------|---------|-------|
| JIT-loaded models (via API, no prior `lms load`) | 60 min TTL | Auto-unloads after 60 min idle |
| `lms load <model>` (CLI, explicit load) | No TTL | Stays until `lms unload` or app quit |
| `lms load <model> --ttl <seconds>` | User-specified | Fires auto-unload after N seconds idle |
| API request `ttl` field | Per-request override | Overrides default for that model instance |
| Auto-Evict (Developer tab setting) | Configurable | Unloads previous model before loading new one |

For the zero-idle-penalty constraint: enable Auto-Evict and set a short default TTL (300–600s). The memory leak on repeated loads means LM Studio should **not** be the primary programmatic backend; restrict its load cycles to interactive human sessions.

### 2.3 Context window / num_ctx

LM Studio exposes context window and KV cache settings through:
- The GUI (model load dialog → "Context Length")
- API request parameters
- CLI: `lms load <model> --context-length <N>`

The same KV cache RAM math applies as for Ollama. LM Studio does not have a convenient global default override — each model load dialog must be configured.

### 2.4 OpenAI-compatible endpoint

- Default port: **1234**
- Base URL: `http://localhost:1234/v1`
- Full OpenAI chat/completions compatibility
- Network access: change bind from `127.0.0.1` to `0.0.0.0` in Developer tab to serve LAN

No port conflict with Ollama (11434) or mlx-lm (8080).

### 2.5 Model storage

Default path: `~/.cache/lm-studio/models/`  
Can be changed in App Settings → "Storage Location".

LM Studio stores models as flat GGUF files, which is directly compatible with llama-server. Sharing with Ollama requires symlinking (see §6).

---

## 3. llama.cpp / llama-server

### 3.1 Idle RAM — "just having it" cost

**llama-server has zero idle daemon.** It is a binary you launch on demand; it has no background process, no menu bar, no automatic startup. When not running: 0 MB. The process exits when you kill it.

This makes it the **most compatible with the zero-idle-penalty constraint** of any option — but requires explicit invocation.

### 3.2 Auto-unload / keep-alive

No built-in auto-unload (it's a server process — you control its lifetime). Unload by killing the process. For an on-demand wrapper, a simple script can:
1. Start `llama-server` on first request
2. Kill it after N seconds of inactivity (using a TTL wrapper or `timeout` utility)

### 3.3 Context window control

```bash
llama-server \
  --model /path/to/model.gguf \
  --ctx-size 8192 \
  --cache-type-k q8_0 \    # KV cache quantization — halves KV RAM
  --flash-attn \           # Flash attention — further 30-50% KV savings
  --n-gpu-layers 999       # Offload all layers to Metal GPU
```

`--ctx-size` is the exact equivalent of `num_ctx`. For a 31B model at 8K context with KV q8_0 and flash attention, KV cache RAM drops from ~2.8 GB (FP16) to ~0.7 GB.

**KVSplit** (community tool, May 2026) is a llama.cpp patch allowing 2–3× longer contexts on Apple Silicon by using a split KV cache strategy — relevant if long-context is a priority.

### 3.4 OpenAI-compatible endpoint

- Default port: **8080**
- Base URL: `http://localhost:8080/v1`
- Full OpenAI chat/completions API compatibility
- `--host 0.0.0.0` to serve LAN

### 3.5 Model storage

llama-server takes a direct `--model /absolute/path/to/file.gguf`. No special directory layout. Point it at any GGUF file — Ollama blobs (after locating the blob), LM Studio files, or standalone downloads. **This is the most flexible storage story** — one canonical GGUF directory works for both LM Studio and llama-server with no symlinking.

### 3.6 Apple Silicon / Metal performance

- Metal GPU offloading: `--n-gpu-layers 999` (offloads all layers)
- Apple Silicon recommended batch size for prefill: `--batch-size 2048` (improves Metal kernel parallelism)
- Approximate tok/s on M5 Pro (64 GB):
  - 8B model Q4: ~90–120 tok/s decode
  - 27B model Q4: ~35–55 tok/s decode
  - 31B model Q4: ~30–50 tok/s decode
- Flash Attention (`--flash-attn`) is a **hard prerequisite** for KV cache quantization; always enable on Apple Silicon

---

## 4. MLX / mlx-lm

### 4.1 Idle RAM — "just having it" cost

mlx-lm is a **Python package with no daemon**. Like llama-server, it runs only when explicitly invoked. Idle footprint: 0 MB (apart from the Python interpreter if a long-running server process is kept alive).

A distinct property: MLX uses **pageable memory** for model weights — the macOS kernel can compress or page out inactive MLX memory. In practice, a loaded model that hasn't received requests for several minutes may show significantly reduced Resident Set Size as the OS compresses its pages. This is automatic and not configurable — it's a benefit on top of the zero-idle property of shutting down the process.

### 4.2 Auto-unload / keep-alive

Like llama-server: kill the process to unload. The `mlx_lm.server` process holds the model in memory for its lifetime. No built-in TTL. Control via process management (launchd, a wrapper script, or manual).

### 4.3 Context window control

```bash
mlx_lm.server \
  --model mlx-community/gemma-4-27b-it-4bit \
  --max-tokens 131072 \    # max context (tokens)
  --port 8080
```

Context length is set at server startup via `--max-tokens`. No per-request override of the context window (unlike Ollama). This means the KV cache is pre-allocated at startup based on `--max-tokens`.

MLX natively quantizes KV cache internally when using 4-bit model weights; there's no separate flag comparable to llama.cpp's `--cache-type-k`. Memory efficiency comes from the model quantization level.

### 4.4 OpenAI-compatible endpoint

- Default port: **8080** (same as llama-server default — potential conflict if both run simultaneously)
- Base URL: `http://127.0.0.1:8080/v1`
- Full OpenAI chat/completions compatibility
- Change port: `--port 8081` to avoid llama-server collision

### 4.5 Model storage

MLX models are stored in **MLX-specific format** (SafeTensors shards from Hugging Face, not GGUF). Default cache: `~/.cache/huggingface/hub/` (HuggingFace hub cache). MLX models cannot be shared with Ollama/LM Studio/llama-server (different formats). This means **separate disk storage** for MLX models vs GGUF models — roughly doubling storage for any model you run in both formats.

### 4.6 Apple Silicon / Metal (M5-specific) performance

MLX is purpose-built for Apple Silicon. On M5 hardware it exploits the **GPU Neural Accelerators** (new in M5) which are specifically designed for the matrix multiplications that dominate LLM inference:

| Model | M5 Max (tok/s) | M4 Pro (tok/s) | Speedup |
|-------|---------------|----------------|---------|
| Llama 3 8B Q4 | ~82 | ~65 | 1.26× |
| Qwen3 30B-A3B Q4 | ~58 | ~45 | 1.29× |
| Llama 3 70B Q4 | ~18 | ~14 | 1.29× |
| Gemma4 E2B | ~158 | ~115 | 1.37× |

M5 memory bandwidth: **153 GB/s** (vs 120 GB/s on M4, +28%). Since large-model decode is memory-bandwidth-bound, this directly translates to higher tok/s.

**MLX vs llama.cpp on Apple Silicon:**
- Models < 14B: MLX leads by **20–87%**
- Models > 27B: They **converge** (both become memory-bandwidth-bound at these sizes)
- For gemma4:26b and gemma4:31b, the advantage is marginal (~5–15%); llama.cpp with the MLX-powered Ollama 0.19 backend is already competitive

**Critical note:** MLX requires models in MLX format from HuggingFace (e.g., `mlx-community/gemma-4-27b-it-4bit`). You cannot point mlx-lm at a GGUF file. If you already have GGUFs via Ollama, you'd need a separate download.

---

## 5. Summary Comparison Table

| Feature | Ollama | LM Studio | llama-server | mlx-lm |
|---------|--------|-----------|--------------|--------|
| **Idle RAM (no model)** | ~50–100 MB (daemon) | ~254 MB (Electron) | 0 MB | 0 MB |
| **Background daemon** | Yes (launchd on macOS) | Yes (optional) | No | No |
| **Auto-unload** | Yes — KEEP_ALIVE (default 5m) | Yes — TTL (default 60m for JIT) | Manual (kill process) | Manual (kill process) |
| **num_ctx control** | Per-request, Modelfile, env | Per-load dialog / CLI | `--ctx-size` flag | `--max-tokens` at startup |
| **KV cache quantization** | `OLLAMA_KV_CACHE_TYPE=q8_0` | Via model settings | `--cache-type-k q8_0` | Implicit (from model quant) |
| **Flash attention** | `OLLAMA_FLASH_ATTENTION=1` | Enabled via settings | `--flash-attn` | Always on (built-in) |
| **OpenAI-compat port** | **11434** | **1234** | **8080** | **8080** (use `--port 8081`) |
| **Model format** | GGUF (blob store) | GGUF (flat) | GGUF (direct path) | MLX SafeTensors |
| **Shareable GGUF** | Via symlinks | Yes (native GGUF) | Yes (native GGUF) | No (different format) |
| **Apple Silicon backend** | MLX (0.19+, ≥32GB) / Metal | Metal | Metal (--n-gpu-layers 999) | MLX native |
| **M5 decode tok/s (31B Q4)** | ~50–112 (MLX path) | ~30–50 | ~30–50 | ~45–60 |
| **GUI for model discovery** | No | Yes (best-in-class) | No | No |
| **LAN serving** | Yes (`OLLAMA_HOST=0.0.0.0:11434`) | Yes (bind to 0.0.0.0) | Yes (`--host 0.0.0.0`) | Yes (`--host 0.0.0.0`) |
| **Memory leak risk** | Low | Moderate (on repeated loads) | None | None |

---

## 6. Shared Model Store Strategy

To avoid duplicating 17–20 GB GGUFs:

```
~/models/
  gguf/
    gemma4-27b-instruct-q4_k_m.gguf
    gemma4-31b-instruct-q4_k_m.gguf
    ...
  mlx/                         # separate; different format
    gemma-4-27b-it-4bit/       # HF cache or manual download
    ...
```

**Ollama ↔ LM Studio GGUF sharing:**
- Set `OLLAMA_MODELS=~/models/gguf` — but note Ollama's blob store layout won't be flat GGUF files. Instead, use the symlink approach: keep models in LM Studio's flat GGUF directory (`~/models/gguf/`) and import into Ollama via `ollama create` with a Modelfile pointing at the GGUF path.
- Or use the community Python script [`link-ollama-models-to-lm-studio.py`](https://gist.github.com/YuriyGuts/caaa91eee484a5ae825cb23bf6582950) to expose Ollama blobs to LM Studio via symlinks.

**llama-server** points directly at GGUF files — fully compatible with a flat `~/models/gguf/` store.

**MLX models** are a separate download; no sharing with GGUF. Budget ~17 GB additional per model if you want both GGUF (for Ollama/llama-server) and MLX (for standalone mlx-lm). Given that Ollama 0.19 already uses MLX internally on ≥32 GB machines, running standalone mlx-lm is redundant unless you need its specific features (fine-tuning, HF model access without Ollama's model library).

---

## 7. Machine A vs Machine B Division of Labor

```
┌─────────────────────────────────────────────────────────────────────────┐
│  Machine A — M5 Pro 64GB (primary workstation)                          │
│                                                                          │
│  ┌──────────────────────────────────────────────────────┐               │
│  │  Ollama (programmatic backend, always-available)      │               │
│  │  • OLLAMA_KEEP_ALIVE=0 (or 10m for burst sessions)   │               │
│  │  • OLLAMA_USE_MLX=1 (2× speed on M5)                 │               │
│  │  • OLLAMA_FLASH_ATTENTION=1                           │               │
│  │  • OLLAMA_KV_CACHE_TYPE=q8_0                         │               │
│  │  • Custom Modelfiles: num_ctx=8192 default            │               │
│  │  • Port 11434 — used by Claude Code, scripts, etc.   │               │
│  └──────────────────────────────────────────────────────┘               │
│                                                                          │
│  ┌──────────────────────────────────────────────────────┐               │
│  │  LM Studio (human experimentation only)              │               │
│  │  • Launch manually when needed; quit when done        │               │
│  │  • DO NOT enable "Run on Login"                       │               │
│  │  • Use for: model discovery, chat UI, A/B testing    │               │
│  │  • TTL: 300s; Auto-Evict: enabled                    │               │
│  │  • Port 1234 — no conflict with Ollama               │               │
│  └──────────────────────────────────────────────────────┘               │
│                                                                          │
│  llama-server: on-demand only for specific use cases:                    │
│  • Need direct GGUF model path with fine-grained flags                   │
│  • KV cache quantization experiments beyond Ollama's exposure            │
│  • Long-context with KVSplit patch                                       │
│  • Script-managed: start on request, kill after task done                │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│  Machine B — M4 Pro 24GB (LAN, idle/dedicated)                          │
│                                                                          │
│  ┌──────────────────────────────────────────────────────┐               │
│  │  Ollama headless (no GUI app)                        │               │
│  │  • OLLAMA_HOST=0.0.0.0:11434                         │               │
│  │  • OLLAMA_KEEP_ALIVE=0                               │               │
│  │  • Metal backend (24 GB < 32 GB MLX requirement)     │               │
│  │  • Load smaller models: 8B–14B for fast turnaround   │               │
│  │  • gemma4:26b is borderline (needs ≤8K ctx)          │               │
│  │  • Suitable for: parallel inference, smaller tasks   │               │
│  └──────────────────────────────────────────────────────┘               │
│                                                                          │
│  NOT recommended on Machine B:                                           │
│  • LM Studio (Electron overhead wastes its limited RAM)                  │
│  • gemma4:31b (34 GB weights — does not fit)                             │
│  • MLX backend (below 32 GB threshold)                                   │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 8. Recommended Architecture & Division of Labor

### Primary recommendation

**Ollama as the always-available programmatic backend on Machine A.** With `OLLAMA_USE_MLX=1` enabled (available on 64 GB M5), Ollama already runs the MLX engine internally — you get MLX's 2× performance improvement without managing a separate runtime, maintaining a separate model format, or giving up Ollama's convenient API, keep-alive control, and model management.

**LM Studio for human-driven experimentation only, not running at login.** Its Electron overhead (~254 MB idle) and memory leak on repeated loads make it unsuitable as a persistent background service. It excels at its GUI strengths: browsing Hugging Face, interactive chat, comparing models — use it like an app, not a daemon.

**llama-server for specialized/advanced cases only:** when you need flags not exposed by Ollama (aggressive KV quantization, custom context pooling, KVSplit long-context), or when scripting a fully controlled lifecycle where process start/stop must be deterministic.

**mlx-lm standalone: not needed.** Ollama 0.19 already incorporates MLX on ≥32 GB hardware. Standalone mlx-lm would require a separate model format (~17–20 GB duplicate downloads) for no speed benefit over Ollama's MLX backend. Reserve it for fine-tuning workflows only.

### Configuration checklist for Machine A (Ollama)

```bash
# In ~/.zshenv or launchctl setenv (for the Ollama daemon)
export OLLAMA_KEEP_ALIVE=0          # or "10m" for interactive burst sessions
export OLLAMA_USE_MLX=1             # enable MLX engine (M5, 64GB)
export OLLAMA_FLASH_ATTENTION=1     # prerequisite for KV quant
export OLLAMA_KV_CACHE_TYPE=q8_0   # halve KV cache RAM
export OLLAMA_CONTEXT_LENGTH=8192  # global default; override per-request as needed
```

Custom Modelfile for gemma4 (saves ~40 GB KV reservation vs 256K default):
```
FROM gemma4:31b
PARAMETER num_ctx 8192
PARAMETER keep_alive 0
```

### Addressing the no-idle-penalty constraint explicitly

| Runtime | Idle penalty with recommended config |
|---------|-------------------------------------|
| Ollama daemon (no model loaded) | ~50–100 MB RAM — **unavoidable as the API server** |
| Ollama with model loaded + keep_alive=0 | Model unloads immediately post-response → 0 KB model RAM |
| LM Studio (not running at login) | **0 MB** (quit when not in use) |
| llama-server (on-demand) | **0 MB** (no background process) |
| mlx-lm (on-demand) | **0 MB** (no background process) |

The 50–100 MB for the Ollama daemon is the unavoidable cost of having a hot API endpoint. If even this is unacceptable, Ollama can be stopped and started on-demand via launchctl, but this adds a 2–3s startup delay before any model load. For most usage patterns, 100 MB is below the "noticeable system penalty" bar on a 64 GB machine.

**The critical knob is `num_ctx`.** The gemma4 256K context default is the single largest idle cost driver — a loaded gemma4:31b at 256K context consumes ~46 GB of KV cache alone, leaving only 18 GB for the OS and other apps. With `num_ctx=8192` and KV q8_0, the KV cache drops to ~0.7 GB, and the model's weights (~17 GB for Q4) become the primary RAM cost.

### Interactive latency ("if it's slow I'll just use ChatGPT")

With the MLX backend on M5 Pro 64 GB:
- **gemma4:26b Q4:** ~55–75 tok/s decode. First token after cold start: ~5–10s. Subsequent tokens: fast.
- **gemma4:31b Q4:** ~45–65 tok/s decode. First token: ~8–15s cold start.
- With `OLLAMA_KEEP_ALIVE=10m`: warm subsequent requests start generating first token in ~200ms.
- With `OLLAMA_KEEP_ALIVE=0`: every request incurs the cold-start load. For quick Q&A, set `OLLAMA_KEEP_ALIVE=5m` as the operating default — the 5-min window catches typical interactive use patterns without leaving models loaded overnight.

Machine B (M4 Pro 24 GB, Metal backend): gemma4:26b is borderline — at 8K context it should fit (~17 GB model + ~1.4 GB KV + OS overhead ≈ ~21 GB). Expect ~25–40 tok/s. Suitable for overflow/parallel use, not for the primary interactive path.

---

## Sources

- [Ollama FAQ — keep-alive and num_ctx docs](https://docs.ollama.com/faq)
- [Ollama 0.19 MLX backend announcement](https://ollama.com/blog/mlx)
- [MLX Runner (Apple Silicon) — DeepWiki](https://deepwiki.com/ollama/ollama/5.7-mlx-runner-(apple-silicon))
- [Idle TTL and Auto-Evict — LM Studio Docs](https://lmstudio.ai/docs/developer/core/ttl-and-auto-evict)
- [LM Studio memory leak report (Electron / repeated loads)](https://dreamlab.ing/posts/48-killed-lm-studio/)
- [LM Studio OpenAI compatibility](https://lmstudio.ai/docs/developer/openai-compat)
- [Tuning llama-server on Apple Silicon](https://medium.com/@michael.hannecke/tuning-llama-server-on-apple-silicon-9b3e778ab100)
- [Choosing an On-Device LLM Runtime on Apple Silicon](https://medium.com/@michael.hannecke/choosing-an-on-device-llm-runtime-on-apple-silicon-a-decision-framework-beyond-benchmarks-2449067b8b67)
- [Apple ML Research: MLX and M5 Neural Accelerators](https://machinelearning.apple.com/research/exploring-llms-mlx-m5)
- [M5 Max Local AI Guide — LLMCheck](https://llmcheck.net/blog/apple-silicon-m5-max-local-ai-guide/)
- [M4 Pro vs M5 Pro inference benchmarks — Contra Collective](https://contracollective.com/blog/m4-m5-pro-local-ai-inference-mlx-2026)
- [Gemma4 31B — 256K context KV cache discussion (HuggingFace)](https://huggingface.co/unsloth/gemma-4-31B-it-GGUF/discussions/2)
- [Gemma4 hardware requirements](https://gemma4-ai.com/blog/gemma4-hardware)
- [Ollama vs LM Studio 2026 — Dottie AI](https://www.dottie.ai/blog/ollama-vs-lm-studio/)
- [mlx-lm server docs (GitHub)](https://github.com/ml-explore/mlx-lm/blob/main/mlx_lm/SERVER.md)
- [KVSplit — 2–3× longer context on Apple Silicon (HN)](https://news.ycombinator.com/item?id=44009321)
- [Ollama model storage and sharing with LM Studio (symlink script)](https://gist.github.com/YuriyGuts/caaa91eee484a5ae825cb23bf6582950)
- [llmlb — distributed LLM router for multi-machine setups](https://github.com/akiojin/llmlb)
- [OLOL — Ollama load balancer](https://github.com/K2/olol)
