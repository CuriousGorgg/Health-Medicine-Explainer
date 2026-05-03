import os
import gradio as gr
from huggingface_hub import InferenceClient
 
# ── Model ─────────────────────────────────────────────────────────────────────
# Mistral-7B-Instruct is free on HF Inference API and excellent for this task.
# You can swap to "meta-llama/Meta-Llama-3-8B-Instruct" if you prefer.
MODEL_ID = "mistralai/Mistral-7B-Instruct-v0.3"
 
# HF_TOKEN is automatically available as a secret in HF Spaces.
# For local dev, set it with: export HF_TOKEN=hf_...
client = InferenceClient(model=MODEL_ID, token=os.environ.get("HF_TOKEN"))
 
# ── System prompt ─────────────────────────────────────────────────────────────
SYSTEM = """You are SymptomSense, a knowledgeable and empathetic health information assistant.
 
Your role:
1. When the user first lists symptoms, respond with:
   - A numbered list of 3-5 possible conditions that match, each with:
     • Likelihood: High / Medium / Low
     • A 1-2 sentence explanation of why it matches
   - 2-3 targeted follow-up questions to narrow down the diagnosis further
   - A brief, warm summary sentence
 
2. As the conversation continues and the user answers questions:
   - Update your list of possible conditions (remove unlikely ones, adjust likelihoods)
   - Ask 1-2 more specific questions if needed
   - When the picture is clear enough, give a final refined summary
 
3. Always:
   - Use plain, clear language (no jargon without explanation)
   - Be empathetic and calm — health anxiety is real
   - End every response with a one-line reminder to consult a doctor for proper diagnosis
   - NEVER claim to provide a diagnosis or replace a doctor
 
Format conditions like this:
**1. Condition Name** — Likelihood: High
Brief explanation of why this fits.
 
**2. Condition Name** — Likelihood: Medium
Brief explanation."""
 
# ── Chat function ─────────────────────────────────────────────────────────────
def chat(user_message: str, history: list):
    """
    history: list of [user, assistant] pairs (Gradio format)
    """
    if not user_message.strip():
        return "", history
 
    # Build messages for the API
    messages = [{"role": "system", "content": SYSTEM}]
    for human, assistant in history:
        messages.append({"role": "user",      "content": human})
        messages.append({"role": "assistant", "content": assistant})
    messages.append({"role": "user", "content": user_message})
 
    # Stream the response
    response = ""
    try:
        for chunk in client.chat_completion(
            messages=messages,
            max_tokens=900,
            temperature=0.4,
            top_p=0.9,
            stream=True,
        ):
            token = chunk.choices[0].delta.content or ""
            response += token
            yield "", history + [[user_message, response]]
    except Exception as e:
        error_msg = f"⚠️ Model error: {str(e)}\n\nThis usually means the model is loading (cold start). Wait 20 seconds and try again."
        yield "", history + [[user_message, error_msg]]
        return
 
    history.append([user_message, response])
    yield "", history
 
 
def clear_chat():
    return [], []
 
 
# ── UI ────────────────────────────────────────────────────────────────────────
DESCRIPTION = """
## 🩺 SymptomSense
**A private, AI-powered health guide.** Describe your symptoms in plain language and get a thoughtful breakdown of possible conditions with follow-up questions to refine the picture.
 
> ⚕️ **Not a medical diagnosis.** Always consult a healthcare professional.
"""
 
EXAMPLES = [
    ["I have a fever of 38.5°C, a sore throat, and my body aches all over. Started yesterday suddenly."],
    ["I've had a runny nose, sneezing, and itchy eyes for a week. No fever."],
    ["I feel very tired, have a dry cough, and lost my sense of smell two days ago."],
    ["I have a sharp chest pain that gets worse when I breathe in, and I feel slightly short of breath."],
    ["I've had a headache for 3 days, feel nauseous, and light hurts my eyes."],
]
 
CSS = """
.gradio-container { max-width: 820px !important; margin: auto; }
.contain { border-radius: 12px; }
footer { display: none !important; }
#chatbot { min-height: 460px; }
#chatbot .message.bot { background: #1e2a1e; border: 1px solid #2d4a2d; }
"""
 
with gr.Blocks(
    theme=gr.themes.Soft(
        primary_hue="green",
        secondary_hue="blue",
        neutral_hue="slate",
        font=[gr.themes.GoogleFont("DM Sans"), "system-ui"],
    ),
    css=CSS,
    title="SymptomSense — Private Health Guide",
) as demo:
 
    gr.Markdown(DESCRIPTION)
 
    with gr.Row():
        with gr.Column(scale=4):
            chatbot = gr.Chatbot(
                elem_id="chatbot",
                label="",
                bubble_full_width=False,
                show_label=False,
                avatar_images=(None, "https://api.dicebear.com/7.x/shapes/svg?seed=symptom&size=40"),
                render_markdown=True,
            )
 
            with gr.Row():
                msg = gr.Textbox(
                    placeholder="Describe your symptoms… (e.g. 'I have a fever, headache and sore throat since yesterday')",
                    show_label=False,
                    scale=5,
                    container=False,
                    autofocus=True,
                )
                submit_btn = gr.Button("Send →", variant="primary", scale=1, min_width=90)
 
            with gr.Row():
                clear_btn = gr.Button("🗑 Clear conversation", size="sm", variant="secondary")
 
        with gr.Column(scale=1, min_width=180):
            gr.Markdown("### Quick starts")
            gr.Markdown("Click an example to load it:")
            for ex in EXAMPLES:
                ex_btn = gr.Button(ex[0][:42] + "…", size="sm", variant="secondary")
                ex_btn.click(lambda m=ex[0]: m, outputs=msg)
 
            gr.Markdown("---")
            gr.Markdown("""
**Tips**
- Be specific: mention duration, severity (1–10), and when it started
- Mention relevant history (e.g. recent travel, known allergies)
- Answer the follow-up questions for a sharper assessment
""")
 
    state = gr.State([])
 
    msg.submit(chat, [msg, state], [msg, chatbot])
    submit_btn.click(chat, [msg, state], [msg, chatbot])
    clear_btn.click(clear_chat, outputs=[state, chatbot])
 
    # Sync chatbot display with state
    chatbot.change(lambda h: h, inputs=chatbot, outputs=state)
 
    gr.Markdown("""
---
<div style="text-align:center; font-size: 12px; color: #888;">
SymptomSense runs on <a href="https://huggingface.co" target="_blank">Hugging Face</a> using open-source AI models.
No data is stored. Responses are generated by AI and <strong>are not medical advice</strong>.
</div>
""")
 
if __name__ == "__main__":
    demo.launch()
 
