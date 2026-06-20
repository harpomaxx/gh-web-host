# Logit-Based Strategies for LLM Guardrails

Below are the **top 5 logit-based strategies for LLM guardrails**, with key papers and videos.

## Core Idea

Before an LLM chooses the next token, it produces a list of raw scores called **logits**: one score for each possible token in the vocabulary. These logits are converted into probabilities and then sampled or selected.

Logit-based guardrails work by intervening at this decision point. Instead of only checking the final answer after it is written, the system can **ban**, **boost**, **down-rank**, or **score** tokens while generation is happening. This makes guardrails more direct: the model can be prevented from producing invalid formats, nudged away from unsafe content, or monitored for uncertainty using the probabilities behind its choices.

In short: **logits are the control surface between model intent and generated text**.

| # | Strategy | How logits are used | Best for | References |
|---|---|---|---|---|
| 1 | **Hard logit masking / constrained decoding** | Set invalid token logits to `-∞` before sampling, so the model literally cannot emit disallowed tokens. | JSON/schema compliance, regex/grammar constraints, tool-call safety, SQL/code format control. | **LMQL**: *Prompting Is Programming* — https://arxiv.org/abs/2212.06094 <br> **Outlines**: *Efficient Guided Generation for LLMs* — https://arxiv.org/abs/2307.09702 <br> **XGrammar** — https://arxiv.org/abs/2411.15100 |
| 2 | **Logit bias / token allowlists and blocklists** | Add positive/negative bias to selected token logits. Extreme negative bias approximates banning; positive bias can force labels like `safe/unsafe`. | Simple profanity/PII blocking, forcing binary classifiers, nudging refusal phrases, reducing forbidden vocabulary. | OpenAI logit bias guide — https://help.openai.com/en/articles/5247780-using-logit-bias-to-alter-token-probability <br> Vellum guide — https://www.vellum.ai/llm-parameters/logit-bias |
| 3 | **Classifier-guided or expert/anti-expert decoding** | Combine base model logits with logits or scores from a safety classifier, “good” expert, or “bad” anti-expert. Unsafe continuations get down-weighted during generation. | Detoxification, style/safety steering, reducing toxic or policy-violating completions without retraining the base model. | **DExperts** — https://arxiv.org/abs/2105.03023 <br> **GeDi** — https://arxiv.org/abs/2009.06367 <br> **FUDGE** — https://arxiv.org/abs/2104.05218 <br> **PPLM video/poster** — https://iclr.cc/virtual_2020/poster_H1edEyBKDS.html |
| 4 | **Logit-based safety scoring / moderation classifiers** | Use logits or logprobs over labels such as `safe`, `unsafe`, or risk categories; threshold the probabilities to block, route, or escalate. | Input/output moderation, policy classifiers, fast guardrail pipelines. | **Llama Guard** — https://arxiv.org/abs/2312.06674 <br> Meta page — https://ai.meta.com/research/publications/llama-guard-llm-based-input-output-safeguard-for-human-ai-conversations/ <br> Demo video — https://www.youtube.com/watch?v=MTFKSAfyGIo |
| 5 | **Uncertainty, hallucination, and provenance guardrails from logits** | Use token logprobs, entropy, contrastive logits, or watermark logit shifts to detect low-confidence, hallucinated, or machine-generated text. | Abstention, retrieval fallback, human review, factuality checks, AI-output detection. | **Semantic Entropy** — https://www.nature.com/articles/s41586-024-07421-0 <br> Video — https://www.youtube.com/watch?v=eiL6egIX4ms <br> **DoLa: Decoding by Contrasting Layers** — https://arxiv.org/abs/2309.03883 <br> **Watermark for LLMs** — https://arxiv.org/abs/2301.10226 <br> **SynthID-Text** — https://www.nature.com/articles/s41586-024-08025-4 |

## Practical Recommendation

For production guardrails, the strongest pattern is usually layered:

1. **Input classifier** using safe/unsafe logits.
2. **Constrained decoding / logit masking** for required structure.
3. **Logit bias or expert-guided decoding** for soft safety steering.
4. **Output classifier** using risk logits.
5. **Uncertainty/logprob checks** to trigger abstention, retrieval, or human review.
