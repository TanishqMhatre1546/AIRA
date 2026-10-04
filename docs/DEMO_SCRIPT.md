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
