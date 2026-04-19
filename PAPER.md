## 1. What I Built

I am building a health-care explainer app that lets a user upload an image of an injury or visible symptom and receive two things: a set of possible conditions and clear, step-by-step care advice. The goal is not to replace a doctor, but to make early-stage understanding more accessible, especially in situations where someone is unsure whether something is serious.

The app currently has three core functions. First, it uses an image model to analyze visual features such as color, swelling, shape, or texture. Second, it maps those features to a shortlist of **possible conditions**, ranked by likelihood. Third, it provides **plain-language treatment guidance**, including home care suggestions and signals for when to seek medical attention.

A key design decision was to avoid presenting a single “diagnosis.” Instead, the app presents a **range of possibilities with uncertainty**, because early visual symptoms often overlap across conditions. This choice came from early testing, where overconfident outputs felt misleading.

---

## 2. My Research Question

My research question developed as I began testing the system:

**When users receive AI-generated explanations of possible medical conditions from images, does simplifying the output into clear advice improve understanding, or does it risk oversimplifying uncertainty and leading to overconfidence?**

This question emerged from the tension between clarity and accuracy. The app is meant to explain, but explanation often requires simplification. The challenge is whether that simplification changes how users interpret risk.

---

## 3. Why This Matters to Me

This project goes beyond image classification. There are already systems that can label conditions from images, but many of them produce outputs that are either too technical or too confident.

What matters to me is the **explanation layer**. If someone uploads an image because they are worried, the response should help them think more clearly, not just give them a label. That means balancing three things:

- Accuracy  
- Clarity  
- Responsibility  

If the app gets this wrong, it could either confuse users or make them too certain about something that actually needs professional evaluation.

---

## 4. What I Tried

The project has evolved through several stages:

- In **Week 1**, I tested basic image classification APIs and noticed that outputs were often single-label and overly confident.
- In **Week 2**, I switched to a multi-condition output format, returning a shortlist instead of one answer.
- In **Week 3**, I added explanation layers that translate medical terminology into simple descriptions.
- In **Week 4**, I introduced treatment suggestions, separating **home care** from **when to seek help**.
- In **Week 5**, I tested how users reacted to different explanation styles (technical vs simplified vs mixed).

A small example shows the issue:

| Input | What the system detected | Problem observed |
|---|---|---|
| Mild skin rash | “Possible dermatitis, allergic reaction” | Clear but vague |
| Bruised ankle | “Possible sprain or fracture” | Users focused only on “fracture” |
| Red swollen eye | “Possible infection or irritation” | Advice felt too general |

This showed that users tend to **anchor on the most serious possibility**, even when probabilities are unclear.

---

## 5. What I Learned

Three main insights came out of testing.

First, **uncertainty must be visible, not hidden**. Simply listing multiple conditions is not enough. The way they are presented affects how users interpret risk.

Second, **explanations matter more than predictions**. Users responded better when the app explained *why* a condition was suggested, even briefly, rather than just naming it.

Third, **treatment advice changes how users interpret the diagnosis**. When clear next steps are given, users feel more grounded, but they may also rely too heavily on the app instead of seeking professional help.

This makes the app less of a classifier and more of a **decision-support tool**, which raises a different set of design challenges.

---

## 6. What Still Needs Work / Who It Might Fail For

There are several important limitations.

- The model relies heavily on visual input, but many conditions require context (pain level, duration, medical history).
- Image quality can significantly affect results (lighting, angle, resolution).
- The system may perform unevenly across different skin tones or body types if training data is not balanced.
- Users may misinterpret probabilistic outputs as certainty.
- Treatment advice, even when cautious, may not apply to all cases.

The app may fail most for users who:
- Expect a definitive diagnosis  
- Have complex or non-visible conditions  
- Need urgent medical attention  

So the honest claim is not “this app diagnoses conditions,” but rather:  
**“this app helps users think through possibilities and next steps, with clear limits.”**

---

## 7. Sources I Would Cite Next

These are the areas I would research next:

- **Medical image analysis and diagnostic AI:** to understand model limitations and bias  
- **Risk communication in healthcare:** to study how uncertainty should be presented  
- **User trust in AI systems:** to evaluate how explanation style affects reliance  
- **Clinical guidelines for common visible conditions:** to improve treatment advice accuracy  
- **Ethics of AI in healthcare:** to define appropriate boundaries for non-professional tools  

---

This paper reflects the current state of the project:

- **What I built** ← Weeks 1–3  
- **My research question** ← Weeks 4–5  
- **What I tried** ← Weeks 2–5  
- **What I learned** ← Weeks 5–6  
- **What still needs work** ← Week 6  

The project is still in progress, but the core shift has already happened:  
from building a diagnostic tool to designing a careful explanation system.
