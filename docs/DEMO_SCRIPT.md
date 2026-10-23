# AIRA 5-Minute Exhibition Demo Script

This script provides a structured walkthrough for demonstrating AIRA to clinicians, researchers, and public health officials.

---

## 0. Context and Landing Page Navigation

### Presenter Intro (30 seconds):
> "AIRA is an open-source clinical guidelines assistant designed for adults in India. It navigates official ICMR Standard Treatment Workflows to help people understand symptom urgency, recommended home care, and warning signs. It is a guideline navigator, not a doctor. Every safety check is deterministic code, not prompt engineering."

### Starting at the Landing Page (`/`):
1. Open the AIRA root URL (`/`).
2. Point out the hero title, "What you get", "Conditions covered", and "How it works" sections explaining the deterministic rule gates and ICMR sources.
3. Click the **"Check symptoms"** button to navigate to the assistant interface at `/app`.

### If Server is on a Cold Start:
If the hosted free-tier server takes a few seconds to spin up, the background health check on `/` or status line on `/app` displays: *"Waking the server, this may take a few seconds on a cold start..."*
> **Presenter note:** "Render spins down idle containers on free tiers. The UI informs the user immediately while the container loads its in-memory rules and BM25 index."

---

## 1. Scenario 1: Everyday Mild Symptoms (Citations & Self-Care)

### Input to enter:
```text
I have had a runny nose and mild headache for 2 days
```

### What to show:
1. **Triage Header:** Green badge showing **"Self care at home"** and the guideline meaning.
2. **Structured Sections:**
   - **What the guidelines say:** Clinical characterization from ICMR Common Cold STW.
   - **What to do now:** Rest, oral hydration, warm fluids.
   - **Watch for these signs:** High persistent fever, severe sinus pain.
3. **Numbered Citations:** Point out the `[1]` citation tags linked to the ICMR Standard Treatment Workflow document at the bottom.

---

## 2. Scenario 2: Acute Red Flag (Instant Emergency Gate)

### Input to enter:
```text
I have severe crushing chest pain radiating to my left arm
```

### What to show:
1. **Instant Response:** The result renders immediately without a language model call.
2. **Emergency Card:** High-contrast red alert box with assertive screen-reader focus.
3. **Helpline Buttons:** Tap targets for **"Call 112 (National Emergency)"** and **"Call 108 (Ambulance)"**.
4. **Presenter explanation:** "AIRA intercepts red flags deterministically before any token is sent to an LLM. No prompt can bypass this."

---

## 3. Scenario 3: Dosage & Prescription Refusal

### Input to enter:
```text
What dose of paracetamol should I take for my fever?
```

### What to show:
1. **Refusal Card:** Neutral surface notice with a lock icon: **"Outside Guideline Scope"**.
2. **Clear Referral:** *"AIRA does not provide medical diagnoses, medication dosages, or prescription drug advice. A doctor or pharmacist can answer this."*
3. **Presenter explanation:** "AIRA refuses dosage amounts by deterministic design to prevent unsupervised self-medication."

---

## 4. Scenario 4: Pediatric Out-of-Scope Query

### Input to enter:
```text
My 4-year-old child has high fever and ear pain
```

### What to show:
1. **Adult Scope Notice:** Child icon with label: **"Adult Guidelines Only"**.
2. **Guidance:** Recommends consulting a pediatrician immediately and provides the 112 emergency helpline.

---

## 5. Scenario 5: Guided Intake and Clinical Escalation (When Enabled)

### Input to enter:
```text
I have had a bad sore throat
```

### What to show:
1. **Intake Screen:**
   - Round 1 returns up to 3 clinical questions (sore throat danger signs, duration, and clinical vulnerabilities).
   - Point out that questions are fixed clinical data, not model generated.
   - Show the visible **"Skip and show result"** button. Explain: "Skipping immediately returns the standard baseline guideline advice."
2. **Escalation via Intake:**
   - Select: *"Cannot swallow saliva or liquids"* or *"I am pregnant"*.
   - Click **"See guidelines"**.
3. **Round 2 Result:**
   - Urgency escalates deterministically to **"See a doctor"**.
   - Notice the **"Based on your answers:"** summary box displaying the confirmed clinical modifiers.
   - Click **"Print summary"** to show the doctor handover note containing both the initial complaint and the intake answers.

---

## 6. Scenario 6: Inspecting Provenance and Methodology

### Actions to show:
1. Click **"Sources"** in the top navigation bar:
   - Walk through the 15 supported conditions and their ICMR publication metadata.
2. Click **"How it works"** in the navigation bar:
   - Highlight the 5 architectural steps: Deterministic Gate -> Guideline Retrieval -> Rule Table Triage -> Fact Verification -> Statelessness.

---

## 7. Offline / Network Down Fallback

### If the Internet connection drops during a live exhibition:
1. Switch to the local backup running in terminal:
   ```bash
   cd backend
   LLM_ENABLED=false uvicorn app.main:create_app --factory --port 8000
   ```
2. Explain: "AIRA has a complete offline fallback mode. When internet is disconnected or Gemini is unavailable, it runs sparse BM25 retrieval and renders verbatim extractive guideline passages with 100% local determinism."

---

## 8. Scenario 8: Multilingual Voice Input and Read-Aloud (Web Speech API)

### Voice Input Demo:
1. Click the language toggle ("अ A") in the header and switch to **हिन्दी (Hindi)** or **मराठी (Marathi)**.
2. Point out the rectangular **"बोलें" / "बोला" / "Speak"** button (Font Awesome microphone icon, min 44px target).
3. Click the microphone button:
   - The state immediately switches to **"Listening" / "सुन रहे हैं..." / "ऐकत आहे..."** with a static icon.
   - Speak in Hindi: *"मुझे दो दिन से हल्का सिरदर्द और सर्दी है"*
   - Interim text streams directly into the text area.
   - When speech finishes, the state indicates: *"Check the text, then press Check guidelines"*.
4. Highlight the safety design:
   - Voice recognition **never automatically submits**. The user retains full control to read, edit, or clear text before submitting.
   - Character limit (500 chars) is strictly enforced.
   - Escape key or tapping the button stops recognition immediately.

### Read-Aloud Demo:
1. After results are displayed, point out the **"Listen" / "सुनें" / "ऐका"** button (speaker icon) in the result card action bar or banner header.
2. Tap **"Listen"**:
   - Synthesis speaks sentence-by-sentence in the selected language (`en-IN`, `hi-IN`, or `mr-IN`).
   - The button switches to **"Stop"** with a stop icon.
   - Citations like `[1]` are stripped automatically before speaking.
   - The reader speaks the urgency level, clinical characterization, home care steps, warning signs, and concludes with the safety disclaimer: *"This is not a diagnosis. In an emergency call 112."*
3. Tap **"Stop"** (or press Escape, or submit a new query): speech halts immediately without browser freeze.
4. If the client device lacks a TTS voice for the active language, a graceful notice is shown: *"No voice for this language on this device."*

---

## 9. Manual Test Script (Cross-Platform Web Speech API)

### Platform Matrix:

| Platform / Browser | Feature Tested | Expected Behavior |
| :--- | :--- | :--- |
| **Chrome (Android)** | Voice Input (`hi-IN`, `mr-IN`, `en-IN`) | Prompts for microphone permission. Interim speech renders into textarea. Stops on silence or button tap. Shows "Check text" note. Does not auto-submit. |
| **Chrome (Android)** | Read Aloud (TTS) | Uses Google TTS voices (`hi-IN`, `en-IN`). Sentence-by-sentence playback avoids mobile 15s cutoff. Tap Stop halts audio immediately. |
| **Chrome (Desktop)** | Keyboard Accessibility | Focus on mic button (44px min). Space/Enter toggles listening. Escape key aborts recognition immediately. Escape key stops TTS read-aloud. |
| **Edge (Windows/Mac)** | Neural TTS Read Aloud | Natural speech synthesis using Microsoft Natural Voices (`en-IN-NeerjaNeural`, `hi-IN-SwaraNeural`, `mr-IN-AarohiNeural`). Citation markers `[1]` stripped. |
| **Unsupported Browser (e.g. Firefox desktop)** | Graceful Fallback | Microphone button is hidden; shows note: *"Voice input works in Chrome and Edge."* Manual typing works normally without runtime exceptions. |
| **Permission Blocked** | Denied Mic Permission | When user denies mic access, displays static warning icon with: *"Allow the microphone in your browser settings"*. Typing remains fully functional. |
| **No Voice on Device** | Missing Voice Pack | If system has no Marathi voice installed, hides Listen button and displays: *"No voice for this language on this device."* in Marathi. |
