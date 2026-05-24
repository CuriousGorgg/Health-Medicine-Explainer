# Research Journal — SymptomSense
## Health + AI Independent Research | Spring 2026

---

## Week 1 — Finding the Problem Worth Solving

I started with a broad question: can AI do anything useful in the health space for a regular person who doesn't have easy access to a doctor? I spent the first week reading about symptom checkers — WebMD, Babylon Health, Ada — and realized they all had one thing in common: a rigid decision tree. You click options, the algorithm narrows it down. None of them let you just describe what you're feeling in your own words.

I decided my project would be a conversational symptom checker. The user describes symptoms naturally, the AI gives a structured differential with likelihood ratings, and follows up with clarifying questions. I named it SymptomSense.

The first thing I researched was whether this was even responsible to build. I read about AI diagnosis tools and their risks — overconfidence, missing rare conditions, patients acting on wrong output. I added a hard rule to myself: every single response must end with a disclaimer. Not a checkbox, not fine print — it had to be in the actual output.

---

## Week 2 — Choosing the Stack: Gradio + Hugging Face

I decided to build on Hugging Face Spaces because it's free, public, and handles deployment automatically. No server to manage, no Docker to configure from scratch — you push code, it builds.

For the UI framework I picked Gradio. It has a ChatInterface component that handles conversation history, streaming responses, and example prompts out of the box. I wrote a minimal prototype locally: a Gradio app that called a simple echo function. Got it running in about 20 minutes. That confirmed the stack worked.

The key decision was which model to use. My criteria were: (1) open-source, (2) free to run, (3) good instruction-following, (4) some health knowledge. I made a shortlist: Mistral-7B-Instruct, BioMistral-7B, and Llama-3-8B.

---

## Week 3 — The BioMistral Hypothesis

BioMistral-7B looked ideal on paper. It's a medical-domain fine-tune of Mistral-7B trained on PubMed abstracts and clinical notes. If I was building a symptom checker, shouldn't I use a model that actually knows medicine?

I tried to load BioMistral-7B locally on HF Spaces using the transformers library. The model weighs approximately 14GB. HF's free CPU tier gives you 16GB of shared RAM. In theory it fits — 14GB model, 2GB headroom. In practice, the OS, Python, Gradio, and PyTorch all need memory too.

The space crashed on startup with an OOM (Out of Memory) error every time. I tried load_in_8bit=True with bitsandbytes for quantization — that library isn't available on CPU-only instances. I tried torch_dtype=torch.float16 — still crashed. I tried loading only the tokenizer and offloading layers — the model architecture didn't support partial loading cleanly.

After three days of variations, I accepted that BioMistral-7B was not runnable on free-tier CPU. This became Constraint A in my paper.

---

## Week 4 — The API Fallback and the Rate Limit Wall

After the BioMistral failure, I pivoted to using the HF Inference API — a hosted endpoint that lets you call models without running them locally. I switched to Mistral-7B-Instruct-v0.3 via InferenceClient. The space ran without crashing.

But a new problem appeared immediately. The first time I called the API after the space had been idle for a while, it returned a 503 error: "Model is currently loading." The model was cold — HF unloads popular models from memory when they're not in use, and it takes 20-40 seconds to reload. If a user sent a message and got a 503, the app just showed an error and stopped.

The second problem was 429 rate limit errors. The free HF Inference API limits you to approximately 1,000 requests per day and has burst limits. During my own testing — not even real users — I hit 429 within an hour. Any real-world use would hit this ceiling.

These two failure modes — cold-start latency and rate limits — became Constraint D in my paper.

---

## Week 5 — Space 1: First Domain Build (My Health Explainer)

With the constraints identified but not yet solved, I shipped Space 1 as a simpler version: My Health Explainer. This one used Mistral-7B via the Inference API but with a narrower scope — it explained medical terms and conditions rather than doing symptom differential. Less risky, more achievable.

Space 1 ran. It wasn't perfect — it still hit cold-start sometimes — but it worked well enough to be the first public build. I learned a lot about Gradio's streaming behavior and how to write system prompts that produce structured output. The model was good at following formatting instructions when I was explicit about them.

Key lesson from Space 1: specificity in the system prompt matters more than model size. A well-prompted Mistral-7B beats a vaguely-prompted BioMistral-7B you can't even load.

---

## Week 6 — Space 2: The Rudimentary SymptomSense Build (V2)

Space 2 was my first attempt at the full symptom checker. I built it with the knowledge of both constraints but didn't implement any mitigations yet — V2 is meant to document the wall, not solve it.

The code connects to the HF Inference API and streams responses. When a 503 hits, it returns a message saying "Model cold-starting." When a 429 hits, it says "Rate limit hit." These aren't graceful — they're honest. V2 shows what happens when you build the simplest possible version and don't handle the API's failure modes.

I also finalized the system prompt structure for SymptomSense: likelihood ratings (High/Medium/Low), condition names, brief explanations, and follow-up questions. This was the part I was most proud of — the output format felt genuinely useful.

---

## Week 7 — Space 3: The Post-Move Build (SymptomSense)

The move from V2 to Space 3 was specifically about handling the two failure modes I had documented. I added a chat_with_retry function with exponential backoff: on a 503 (cold-start), wait 5 seconds and retry up to 3 times. On a 429 (rate limit), wait progressively longer — 5s, 10s, 15s.

I also separated the InferenceClient initialization into a get_client() function that reads the HF_TOKEN secret, making it easier to authenticate and getting better rate limits with a token vs. anonymous access.

The trade-off: retry logic adds latency. A user sending a message might wait up to 30 extra seconds if the model is cold. That's a real cost. But the app no longer crashes silently — it tells the user what's happening and keeps trying. That's a much better user experience than a raw error.

---

## Week 8 — Reflection and What I'd Do Differently

Looking back across the 8 weeks, the biggest lesson was that infrastructure constraints are as important as model quality. I spent a week on BioMistral when the right answer was "this doesn't fit the environment." Reading the HF documentation more carefully at the start would have saved me days.

The retry logic in Space 3 works but it's a band-aid. If I had more time, I'd add a queue system so users aren't stuck waiting — they'd submit a query and get notified when it's done. I'd also look at model alternatives that are smaller and faster on CPU: Phi-2 (2.7B), Gemma-2B, or TinyLlama. These might sacrifice some quality but would eliminate cold-start entirely by being fast enough to stay loaded.

The disclaimer requirement I set in Week 1 stayed in every version. That felt like the right call. A health AI that doesn't consistently remind users it's not a doctor is a liability, not a feature.
