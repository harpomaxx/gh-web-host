# Running LLMs on a Raspberry Pi 5 (8GB): prompt caching and speed techniques

Date: 2026-06-22

## Executive summary

A Raspberry Pi 5 with 8GB RAM can run useful local LLMs, but the practical target is **small quantized models** rather than 7B+ models. For interactive use, start with **0.5B-3B parameter models** in **GGUF** format through **llama.cpp** or **Ollama**. Expect roughly:

- **1-1.5B models:** often usable for chat, about **5-15 tokens/s** in community and published Pi 5 benchmarks.
- **3B models:** more capable, but slower, often **2-5 tokens/s**.
- **7B models:** may technically load at aggressive quantization, but are usually too slow for interactive use on the base Pi 5.

The biggest speed wins come from: choosing a smaller or better-distilled model, using 4-bit/5-bit quantization, keeping prompts short, running the model as a long-lived server, reusing prompt/KV cache, avoiding swap, and cooling/powering the Pi well.

## What “LLM on the edge” means here

“LLM on the edge” means the model runs on a local device near the sensor/user/application rather than in a cloud data center. For a Raspberry Pi 5, the benefits are privacy, offline operation, predictable cost, and low-latency local control. The tradeoff is severe compute and memory-bandwidth limits.

The Pi 5 is usually **memory-bandwidth-bound** during token generation: each new token requires repeatedly reading model weights from RAM. That is why model size and quantization dominate performance.

## Recommended stack

### Easiest path: Ollama

Use Ollama if you want the fastest setup and an OpenAI-compatible local API:

```bash
curl -fsSL https://ollama.com/install.sh | sh
sudo systemctl enable ollama
sudo systemctl start ollama
ollama pull qwen2.5:1.5b
ollama run qwen2.5:1.5b
```

Good first models to try:

- `qwen2.5:1.5b` or a newer small Qwen/Qwen-Coder model for general utility.
- `llama3.2:1b` or `llama3.2:3b` for Meta’s small edge-friendly family.
- `gemma3:1b` / small Gemma variants where available.
- TinyLlama-class models for maximum speed, accepting lower quality.

### More control: llama.cpp

Use llama.cpp if you want direct control over quantization, prompt cache behavior, KV-cache types, context length, speculative decoding, and benchmarking.

Build with OpenBLAS on Raspberry Pi OS / Linux:

```bash
sudo apt update
sudo apt install -y build-essential cmake git libopenblas-dev

git clone https://github.com/ggml-org/llama.cpp
cd llama.cpp
cmake -B build -DGGML_BLAS=ON -DGGML_BLAS_VENDOR=OpenBLAS
cmake --build build --config Release -j4
```

llama.cpp’s build documentation notes that BLAS helps prompt processing/prefill; it does not significantly improve autoregressive token-by-token generation.

## Prompt cache techniques

There are several different “caches” people mean when they say prompt caching.

### 1. Normal KV cache inside a conversation

Every transformer inference engine stores keys and values for previous tokens so that each new token does not recompute the entire conversation from scratch. This is the **KV cache**. It is essential and normally always used.

Tradeoff: KV cache consumes RAM proportional to context length, number of layers, hidden size, and concurrent sessions. Long context windows can push a Pi into swap, destroying speed.

Practical advice:

- Keep context modest: start around **2048-4096 tokens**.
- Do not paste huge documents directly; use RAG or summaries.
- Avoid long chat histories; periodically summarize.

### 2. Prefix/prompt cache across requests

If many requests share the same system prompt, tool instructions, persona, or document prefix, the server can reuse the already-computed KV state for the common prefix.

In llama.cpp server, prompt caching is exposed as `--cache-prompt` / `--no-cache-prompt` and is enabled by default in current server docs. API requests can also use `cache_prompt: true`. The common prefix must be byte/token identical enough to be reused.

Design prompts for prefix reuse:

```text
[stable system prompt]
[stable tool instructions]
[stable examples]

User request:
{dynamic user text}
```

Avoid putting volatile values such as timestamps, random IDs, or per-request metadata at the top of the prompt, because they break the shared prefix. Put dynamic data late.

### 3. llama.cpp slots for repeated sessions

llama-server has “slots.” A slot can retain a conversation/prefix state. If you have two recurring prompt patterns, run multiple slots and keep each pattern pinned to a slot.

Example server shape:

```bash
./build/bin/llama-server \
  -m models/qwen2.5-1.5b-instruct-q4_k_m.gguf \
  -c 4096 \
  -t 4 \
  -np 2 \
  --host 0.0.0.0 \
  --port 8080
```

Then send requests with stable prefixes and `cache_prompt: true`. For a single-user appliance, `-np 1` is usually simpler and uses less RAM.

### 4. Persisting cache/session state

llama-server exposes `--slot-save-path PATH`, which can be used by clients that save and restore slot KV state. This is useful when you have a large fixed system prompt or local knowledge prefix that you want to avoid recomputing after a restart.

Caveat: persistent KV cache is fragile across model changes, prompt changes, tokenizer changes, and llama.cpp version changes. Treat it as an optimization, not as durable application state.

### 5. KV-cache quantization

llama.cpp supports separate KV cache data types, for example:

```bash
--cache-type-k q8_0 --cache-type-v q8_0
# or more aggressive:
--cache-type-k q4_0 --cache-type-v q4_0
```

This can reduce RAM use and allow longer contexts or more slots. On a Pi, the main benefit is often **avoiding swap** rather than raw speed. Start with default `f16`; try `q8_0` if memory is tight; use `q4_0` only after testing answer quality.

## Other speed techniques

### 1. Pick the right model size

This matters more than almost everything else. For a Pi 5 8GB:

| Model size | Practicality | Notes |
|---|---:|---|
| <1B | Fastest | Good for classification, routing, simple commands. |
| 1-1.5B | Best first target | Usable chat speed with small-model quality limits. |
| 2-3B | Better answers, slower | Good for careful tasks where waiting is okay. |
| 7B+ | Usually not interactive | May load with low-bit quantization but slow. |

Research and community benchmarks identify small Gemma, Qwen, and Llama 3.2 1B/3B models as strong candidates. Stratosphere Laboratory’s Pi 5 testing found `gemma3:1b`, `llama3.2:1b-instruct`, and `qwen2.5:1.5b` among the more efficient choices.

### 2. Use quantized GGUF weights

Use Q4 or Q5 quantization for most Pi deployments:

- **Q4_K_M / Q4_0:** smaller and faster, some quality loss.
- **Q5_K_M:** larger and sometimes better quality, modestly slower.
- **Q8_0:** better quality but often too large/slow for edge use.

Avoid full precision models on the Pi.

### 3. Keep prompts short and structured

Prompt prefill can be a large part of latency, especially with long system prompts. Techniques:

- Put fixed instructions in a cached prefix.
- Keep examples few and short.
- Use bullet-point output requirements instead of long prose.
- Cap retrieved RAG context aggressively.
- Summarize old conversation turns.

### 4. Limit generation length

Set a realistic maximum output token count. A model producing 5 tokens/s takes about 40 seconds to generate 200 tokens. For command/control tasks, ask for compact JSON or short answers.

### 5. Run a long-lived server

Avoid reloading the model for every request. Use Ollama or llama-server as a service so model weights stay memory-mapped/in RAM and caches can be reused.

### 6. Tune threads, batch, and context empirically

For Pi 5’s four Cortex-A76 cores, start with:

```bash
-t 4 -c 2048
```

Then benchmark. Larger batch sizes help prompt processing but consume memory. Larger context windows consume KV cache memory and can slow down when memory pressure increases.

Use llama.cpp’s benchmarking tools if possible:

```bash
./build/bin/llama-bench -m model.gguf
```

### 7. Avoid thermal throttling and slow storage

Hardware matters:

- Use the official high-quality power supply.
- Use active cooling.
- Prefer SSD/NVMe over microSD for model loading and general responsiveness.
- Monitor temperature and throttling.
- Avoid swap during inference; if the system swaps, use a smaller model/context.

### 8. Speculative decoding

Speculative decoding uses a faster draft model to propose tokens that the main model verifies in batches. llama.cpp supports it via draft model options such as `--model-draft` / `--spec-draft-model` and also supports n-gram speculative modes.

On a Raspberry Pi, classic two-model speculative decoding may not always help because it loads another model and increases memory pressure. It is most worth testing when:

- The target model is relatively large and slow.
- The draft model is tiny and from a compatible family.
- You have enough RAM headroom.

N-gram speculative decoding is lightweight and can help for repetitive text, editing, summarization, or code-like workloads.

### 9. Application-level caching

For edge applications, do not rely only on model-level caches. Add simple application caches:

- Cache exact prompt -> answer for repeated questions.
- Cache embeddings/RAG retrieval results.
- Cache summaries of documents.
- Cache tool outputs, sensor readings, or parsed state.

This can outperform any inference optimization if your workload repeats.

### 10. Consider accelerator hardware, but check model support

The base Pi 5 runs LLMs on CPU. Raspberry Pi’s newer AI HAT+ 2 / Hailo-10H class hardware is aimed at generative AI acceleration, but model/runtime support is narrower than llama.cpp CPU inference. For experimentation across many models, CPU llama.cpp is more flexible. For a fixed appliance model, an accelerator may be useful if it supports exactly your model family and quantization.

## Practical starting configuration

For a first Pi 5 8GB experiment:

1. Install Ollama for convenience.
2. Try `qwen2.5:1.5b`, `llama3.2:1b`, and `llama3.2:3b`.
3. Measure latency and tokens/s on your real prompts.
4. If you need more control, move to llama.cpp with a Q4_K_M GGUF.
5. Run as a persistent server.
6. Keep the system prompt stable and put dynamic content late.
7. Enable/use prompt caching; test whether repeated requests skip prefill.
8. Keep context at 2048 or 4096 initially.
9. Only then experiment with KV-cache quantization, speculative decoding, and accelerator hardware.

Example llama-server command:

```bash
./build/bin/llama-server \
  -m models/qwen2.5-1.5b-instruct-q4_k_m.gguf \
  --host 0.0.0.0 \
  --port 8080 \
  -t 4 \
  -c 4096 \
  -np 1 \
  --cache-prompt \
  --cache-type-k q8_0 \
  --cache-type-v q8_0
```

If quality drops or memory is fine, remove the KV quantization flags and use the default cache type.

## Checklist for fast edge answers

- [ ] Use a 1-1.5B model first.
- [ ] Use Q4/Q5 GGUF quantization.
- [ ] Keep the model loaded in a server process.
- [ ] Use stable prompt prefixes to maximize prompt cache hits.
- [ ] Put dynamic per-request data after the stable prefix.
- [ ] Keep context length modest.
- [ ] Cap output length.
- [ ] Use active cooling and good power.
- [ ] Avoid swap.
- [ ] Benchmark with your real prompts, not only synthetic examples.

## Sources

- llama.cpp server README: prompt caching, slots, slot save path, KV cache type flags, speculative options: https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md
- llama.cpp build documentation: OpenBLAS build flags and BLAS notes: https://github.com/ggml-org/llama.cpp/blob/master/docs/build.md
- llama.cpp speculative decoding documentation: https://github.com/ggml-org/llama.cpp/blob/master/docs/speculative.md
- Stratosphere Laboratory, “How Well Do LLMs Perform on a Raspberry Pi 5?” (2025): https://www.stratosphereips.org/blog/2025/6/5/how-well-do-llms-perform-on-a-raspberry-pi-5
- TinyWeights, “Running LLMs on Raspberry Pi 5: A Practical Guide with Real Benchmarks” (2026): https://tinyweights.dev/posts/run-llms-raspberry-pi-5/
- Raspberry Pi AI software documentation: https://www.raspberrypi.com/documentation/computers/ai.html
- Raspberry Pi announcement of AI HAT+ 2 / generative AI acceleration: https://www.raspberrypi.com/news/introducing-the-raspberry-pi-ai-hat-plus-2-generative-ai-on-raspberry-pi-5/
