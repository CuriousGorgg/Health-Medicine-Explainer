# SymptomSense — Demo Day Presentation
## AI + Research Level 2 | Spring 2026

---

## Slide 1: The Problem

**Most people have no idea what their symptoms mean.**

- Search engines return anxiety-inducing worst-case results
- Symptom checkers use rigid decision trees — click options, get answer
- No tool lets you describe what you feel in your own words and get a thoughtful response

**My goal:** Build a conversational AI symptom checker that's free, public, and honest about what it is.

---

## Slide 2: What I Built — SymptomSense

**A free AI health assistant on Hugging Face Spaces**

- Describe your symptoms in plain language
- Get a structured differential: 3-5 possible conditions with High / Medium / Low likelihood
- Follow-up questions narrow the picture
- Every response ends with: *"This is not a medical diagnosis. Please consult a qualified healthcare professional."*

**Stack:** Gradio + Mistral-7B-Instruct-v0.3 via HF Inference API + Python

---

## Slide 3: The Three Spaces

| Space | What It Is | Status |
|---|---|---|
| Space 1: My Health Explainer | First domain build — explains medical terms | Running |
| Space 2: V2 | The wall — symptom checker without retry logic | Running (documents the constraint) |
| Space 3: SymptomSense | Post-move build — full retry logic, authenticated API | Running |

**Space 2 exists to show what breaks. Space 3 shows what I did about it.**

---

## Slide 4: The Wall — Two Constraints

**Constraint A: Medical models are too large for free-tier compute**

- BioMistral-7B weighs ~14GB
- HF free CPU tier has 16GB shared RAM
- OS + Python + PyTorch + Gradio = OOM before model finishes loading
- Stack trace: RuntimeError: out of memory on every startup attempt

**Constraint D: The Inference API has cold-start latency and rate limits**

- Fallback: use Mistral-7B-Instruct via HF Inference API (no local loading)
- Cold model returns HTTP 503 — "Model is currently loading" — 20-40s delay
- Free tier rate limit: ~1,000 req/day, burst cap ~10 req/min
- HTTP 429: "Rate limit reached" after an hour of testing

---

## Slide 5: The Move — Exponential Backoff Retry

**What changed from V2 to SymptomSense:**

```python
def chat_with_retry(messages, retries=3):
    for attempt in range(retries):
        try:
            yield from client.chat_completion(messages, stream=True)
            return
        except Exception as e:
            if "503" in str(e):
                yield f"Model warming up, attempt {attempt+1}/3..."
                time.sleep(5)
            elif "429" in str(e):
                wait = 5 * (attempt + 1)
                yield f"Rate limit hit. Retrying in {wait}s..."
                time.sleep(wait)
```

- Users see status updates instead of a frozen screen
- 3 retries with increasing wait times
- Authenticated HF_TOKEN raises the rate limit ceiling

---

## Slide 6: What the Move Cost

**Honest trade-offs:**

- **Latency:** Cold-start + retry can add 25-45 seconds to the first message
- **API dependency:** If HF's Inference API goes down, SymptomSense breaks — no local fallback
- **Rate limits:** Still hit ~1,000 req/day. Real-world use would hit the ceiling by afternoon
- **Model compromise:** Had to drop BioMistral-7B (medical-domain fine-tune) — the model that fits the compute is not the model I wanted

**The retry logic is a mitigation, not a solution.**

---

## Slide 7: What I'd Do Next

1. **Use a smaller medical model:** BioMistral-3B (~6GB) fits free-tier RAM. Would eliminate the API dependency entirely.

2. **Async queue:** Decouple user input from inference. User submits, app processes in background, chat updates when ready. No blocking wait.

3. **Usage-aware degradation:** Track daily API calls. When approaching the limit, reduce max_tokens to conserve calls. Show users how many requests remain.

4. **Evaluation:** Build a test set of symptom descriptions with ground-truth differential diagnoses. Measure how often SymptomSense includes the correct condition in its top-3.

---

## Slide 8: Key Takeaways

> **Free-tier infrastructure is a real research constraint, not a minor inconvenience.**

- The model choice was dictated by RAM, not quality
- The retry architecture was dictated by rate limits, not preference
- The trade-offs in latency, reliability, and model capability all trace back to two numbers: **16GB RAM** and **1,000 API calls/day**

**Links:**
- Space 1: https://huggingface.co/spaces/CuriousGorg/My_Health_Explainer
- Space 2 (V2): https://huggingface.co/spaces/CuriousGorg/V2
- Space 3: https://huggingface.co/spaces/CuriousGorg/SymptomSense
- Research Journal: https://github.com/CuriousGorgg/Health-Medicine-Explainer/blob/main/research-journal.md
- Paper: https://github.com/CuriousGorgg/Health-Medicine-Explainer/blob/main/PAPER.md
