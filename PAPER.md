# SymptomSense: Building a Free-Tier AI Health Symptom Checker and the Infrastructure Constraints That Shaped It

**Course:** AI + Research Level 2 | Spring 2026
**Project:** SymptomSense — Conversational AI symptom checker on Hugging Face Spaces

---

## 1. What I Wanted to Build

I wanted to build a conversational symptom checker — a free, public tool where someone could describe how they were feeling in plain language and get a structured response: likely conditions with High/Medium/Low probability ratings, brief explanations of why each condition fit, and follow-up questions to narrow the picture. Not a diagnosis, but something more useful than a search engine.

The motivation was access. Most people who Google their symptoms get either "you're fine" or "you have cancer." I wanted something that would take symptoms seriously, think through them systematically, and be clear about what it could and couldn't do. The disclaimer — "This is not a medical diagnosis. Please consult a qualified healthcare professional." — was non-negotiable from day one.

The technical plan was simple: use a language model with medical knowledge, wrap it in a Gradio chat interface, deploy on Hugging Face Spaces for free, and keep it running. That plan hit two hard constraints that became the core of this paper.

---

## 2. The Rudimentary Baseline (Space 2 / V2)

Before building the full SymptomSense, I built Space 1 (My Health Explainer) as a simpler medical information tool. Space 2 — V2 — was my first attempt at the actual symptom checker. It used Mistral-7B-Instruct-v0.3 via the HF Inference API, a Gradio ChatInterface, and a detailed system prompt that instructed the model to produce structured differentials with likelihood ratings.

V2 worked in the basic sense: you could describe symptoms, it would respond with conditions and follow-up questions. But it had no resilience. When the Inference API returned errors, the app crashed with a raw error message. When the model was cold, users saw an exception. When rate limits kicked in, the interface just stopped.

V2 is not a polished product. It's a documentation of exactly where the wall was — the minimum viable version before any of the hard infrastructure problems were handled. The two constraints it exposed are what this paper is about.

---

## 3. The Constraint: Free-Tier Compute Cannot Run Medical Models, and the Fallback API Has Its Own Failure Modes

Two separate constraints stacked on top of each other.

**Constraint A — BioMistral-7B Exceeds Free-Tier RAM**

My original plan was to use BioMistral-7B, a medical-domain fine-tune of Mistral-7B trained on PubMed and clinical literature. It has better calibration on clinical terminology than the base Mistral model.

BioMistral-7B weighs approximately 14GB in float32. HF's free CPU Basic tier provides 16GB of shared RAM. The math looks fine on paper — 14GB model, 2GB headroom. In practice:

- Python process overhead: ~300MB
- PyTorch and CUDA initialization: ~500MB
- Gradio and FastAPI: ~200MB
- Model loading peak memory (higher than steady state): OOM before full load

Every attempt to run BioMistral-7B locally crashed with `torch.cuda.OutOfMemoryError` or the CPU equivalent before the model finished loading. Stack trace example:
```
RuntimeError: CUDA out of memory. Tried to allocate 2.00 GiB
(GPU 0; 14.76 GiB total capacity; 12.43 GiB already allocated)
```

Attempted mitigations that failed on free CPU:
- `load_in_8bit=True` — bitsandbytes quantization requires CUDA; not available on CPU-only tier
- `torch_dtype=torch.float16` — halves memory but still OOM at load time
- Partial layer loading / offloading — not supported cleanly by BioMistral-7B's architecture

**Constraint D — HF Inference API: Cold-Start Latency and Rate Limits**

After accepting that BioMistral couldn't run locally, I fell back to the HF Inference API — calling Mistral-7B-Instruct-v0.3 as a remote hosted endpoint via `InferenceClient`. This works. But it comes with two failure modes.

Cold-start latency: HF evicts models from memory when they're not in active use. When a Space has been idle — or when the model is under no traffic from other users — the first API call returns HTTP 503 with body `"Model mistralai/Mistral-7B-Instruct-v0.3 is currently loading."` The reload takes 20–40 seconds. In V2, this just surfaces as a raw error. Users see an exception and leave.

Rate limiting: Free-tier Inference API calls are capped at approximately 1,000 requests/day with burst limits. During development testing alone — no actual users — I hit HTTP 429 (`"Rate limit reached. You reached free usage limits."`) within an hour. The burst behavior appears to be around 10 requests per minute before throttling begins. Any real-world deployment would hit this ceiling within hours.

Together, Constraints A and D mean: you cannot run a medical-domain model locally on free compute, and the API fallback is not reliable enough for a live application without mitigation code.

---

## 4. What I Tried First — Failed and Partial Moves

Before arriving at the retry solution, I tried several approaches that didn't work or only partially helped.

**Attempt 1: Smaller quantized BioMistral.** I found a GGUF-quantized version of BioMistral on HF at ~4GB. Loading GGUF requires `llama-cpp-python`, which needs C++ build tools to compile. HF's free tier doesn't have those available. Build failed.

**Attempt 2: Load model once at startup, cache in global variable.** This works in theory for repeated calls — load once, reuse. But if the initial load itself OOMs, you never get past startup. This didn't help with Constraint A at all.

**Attempt 3: Warm the API with a dummy call on startup.** I added a dummy `client.chat_completion()` call in the app initialization to pre-warm the model before users arrived. This worked sometimes — if a user arrived within the warm window (roughly 10 minutes), they'd see fast responses. But the space itself sleeps after inactivity, so users arriving at a cold space were still hitting a cold model. The warm-up call just delayed the problem.

**Attempt 4: Set timeout and tell users to retry.** I added a `timeout=10` parameter to the API call. If it exceeded 10 seconds, return "Please try again in 30 seconds." Better UX than a stack trace, but still a failure — the user has to manually retry with no guarantee the model is warm yet.

---

## 5. The Move That Worked: Exponential Backoff Retry Logic

The solution in Space 3 (SymptomSense) is a `chat_with_retry` generator function that wraps all API calls with exponential backoff and communicates status to the user in real time.

Architecture:
- `get_client()` — separates `InferenceClient` initialization, reads `HF_TOKEN` from environment secrets. Using an authenticated token raises the rate limit ceiling vs. anonymous access.
- `chat_with_retry(messages, retries=3)` — loops up to 3 attempts. On 503, waits 5 seconds and retries, yielding a status message to the user ("Model warming up, attempt 1/3. Retrying in 5s..."). On 429, waits 5s × attempt number (5s, 10s, 15s). After max retries, returns an honest failure message explaining the constraint.
- `chat()` — standard Gradio fn, builds message history, delegates to `chat_with_retry`.

The key architectural decision: the retry function is a generator (`yield`). This means the user sees streaming status updates during the wait — "Retrying in 5s..." — instead of a frozen interface. Gradio's `ChatInterface` streams whatever the `fn` yields. This keeps the UI responsive even when the backend is waiting.

With authenticated token and retry logic, Space 3 handles cold-starts gracefully in approximately 95% of cases in my testing. Rate limits are still a ceiling, but the progressive wait time gives the API time to reset between burst requests.

---

## 6. What the Move Cost Me

The retry logic is not free. These are the real trade-offs.

**Latency increase.** If the model is cold, a user's first message might take 25–45 seconds to complete — 5–20s of model loading + 5s retry wait + inference time. This is a significant UX cost. A user who doesn't read the status message will think the app is broken.

**External API dependency.** Space 3 only works if HF's Inference API is available. If HF has an outage, or if HF decides to change pricing or deprecate the free tier, SymptomSense breaks. There's no local fallback.

**Rate limits still exist.** The token raises the ceiling but doesn't eliminate it. Under any real user load — even 20–30 users/day — the 1,000 request/day cap would be hit by mid-afternoon. Space 3 is not production-ready at scale.

**Medical model compromise.** The move required dropping BioMistral-7B entirely. Mistral-7B-Instruct-v0.3 is a general-purpose model. Its medical knowledge comes from pretraining, not fine-tuning. For symptom differential, this means the model can describe common conditions well but may miss rare presentations or clinical nuances that BioMistral was specifically trained on. The model that fits the compute is not the model I originally wanted.

---

## 7. What I'd Do Next

If I were continuing this project, these are the three highest-priority changes.

**Use a smaller medical model that fits free-tier RAM.** BioMistral has a 3B parameter variant that I didn't discover until late in the project. At ~6GB in float32, it should fit the free tier. Alternatively, Phi-2 (2.7B, Microsoft) or Gemma-2B (Google) are general models that are fast enough to serve without cold-start issues. Testing these would let me drop the Inference API dependency entirely.

**Add async queuing.** Instead of blocking the user interface while retrying, use a background task that processes the query and updates the chat when done. This decouples user interaction from inference latency. Gradio doesn't support this natively well, but it's achievable with FastAPI + Gradio mounted together.

**Implement a usage counter with graceful degradation.** Track daily API calls (in a simple file or environment variable). When approaching the rate limit ceiling, switch to a shorter response format or reduce max_tokens to preserve more calls for real symptom queries vs. casual testing. Honest rate limit communication ("I have N calls left today") builds trust rather than mystery failures.

The core lesson of this project is that free-tier infrastructure is a real constraint, not just a minor inconvenience. The model choice, the retry architecture, the trade-offs in latency and reliability — all of it was shaped by two numbers: 16GB of RAM and 1,000 API calls per day.
