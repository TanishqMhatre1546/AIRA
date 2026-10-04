# Manual Browser Verification Checklist for Guided Intake

This document provides a manual testing protocol for verifying AIRA guided intake in a desktop or mobile web browser.

---

## 1. Prerequisites and Setup
1. Start the backend with intake enabled:
   ```bash
   cd backend
   INTAKE_ENABLED=true uvicorn app.main:create_app --factory --port 8000
   ```
2. Start the frontend:
   ```bash
   cd frontend
   npm run dev
   ```
3. Open browser developer tools and navigate to `http://localhost:5173`.

---

## 2. Browser Verification Scenarios

### Scenario A: Standard Follow-up Questions (Mild Symptoms)
1. In the symptom input box, enter: `sore throat for 3 days`. Click **Check guidelines**.
2. **Verify:**
   - The UI displays the intake screen titled: **A few quick questions**.
   - Exactly 2 or 3 questions appear: sore throat danger signs and vulnerability risk questions. The duration question is omitted because duration was stated in the input text.
   - An optional text area titled **Anything else to add? (optional)** appears with a live counter: `300 characters remaining`.
   - A secondary button **Skip and show result** is visible.

### Scenario B: Skip Intake Baseline Parity
1. On the intake screen from Scenario A, click **Skip and show result**.
2. **Verify:**
   - The UI immediately renders the standard result card without asking questions again.
   - Triage level is **Self care at home** (`SELF_CARE`), identical to the baseline single-step response.

### Scenario C: Emergency Option Intercept
1. Enter `sore throat for 3 days` and submit to reach the intake screen.
2. Select the option: **Drooling saliva because you cannot swallow liquids**.
3. Click **See guidelines**.
4. **Verify:**
   - The UI immediately renders the red emergency alert card (`EMERGENCY`).
   - Emergency helpline buttons (`112` and `108`) are displayed.
   - Response mode is static with zero model calls.

### Scenario D: Red Flag Direct Emergency
1. Enter `severe chest pain` and submit.
2. **Verify:**
   - The red emergency alert card appears immediately.
   - No intake questions are shown.

### Scenario E: Vague Query Area Selection
1. Enter `i feel unwell` and submit.
2. **Verify:**
   - The first question displayed is **What is the main problem?** (`Q_AREA`).
   - The second question is **Do you have any of these right now?** (`Q_GENERAL_SIGNS`).
   - The third question is **How long has this been going on?** (`Q_DURATION`).

### Scenario F: Emergency Text in Extra Text Area
1. Enter `sore throat for 3 days` and reach the intake screen.
2. In the optional text area, type: `now crushing chest pain radiating to left arm`.
3. Click **See guidelines**.
4. **Verify:**
   - The red emergency alert card appears immediately.

### Scenario G: Mutual Exclusivity of "None of these"
1. On any multi-select intake question (such as danger signs or risk factors):
   - Select one or more specific options.
   - Click **None of these**. Verify that all previous options in that question are deselected.
   - Select a specific option again. Verify that **None of these** is automatically deselected.

---

## 3. Responsive and Mobile Testing (320px Viewport)
1. Open Browser DevTools: Device Emulation -> set viewport width to `320px` (for example iPhone SE or Galaxy Fold).
2. **Verify:**
   - No horizontal scrollbars appear on any screen.
   - All radio buttons, checkboxes, and buttons maintain a minimum tap target height of 44px.
   - Question text and options wrap cleanly without clipping or text overlap.
   - The **Skip and show result** and **See guidelines** buttons stack or wrap appropriately without overflow.

---

## 4. Accessibility and Keyboard Navigation
1. Disconnect mouse or do not use pointer.
2. Use `Tab`, `Shift+Tab`, `Space`, `Enter`, and Arrow keys:
   - When the intake screen loads, focus moves automatically to the heading: **A few quick questions**.
   - Use `Tab` to navigate through question options.
   - For single-select questions: use Arrow keys or Space to toggle radio options.
   - For multi-select questions: use Space to toggle checkboxes.
   - Use `Tab` to enter the text area and type.
   - Use `Tab` to reach **See guidelines** and press `Enter` to submit.
   - Use `Tab` to reach **Skip and show result** and press `Enter` to skip.
3. Verify visible focus outlines around every interactive control.

---

## 5. Network Tab Privacy and Data Leak Audit
1. Open Browser DevTools: **Network** tab.
2. Submit a symptom query and complete the intake form.
3. Inspect the JSON response of the first POST request to `/api/triage`:
   - Inspect every question object and option object inside `questions`.
   - Confirm that none of the following clinical metadata keys appear anywhere in the payload:
     `canonical_phrase`, `rule_id`, `min_level`, `kind`, `condition_ids`, `item_id`, `source_id`, `source_page`, `modifier`, `duration_days`.
4. Inspect the request payload of the second POST request to `/api/triage`:
   - Verify only `question_id` and `selected_option_ids` (and optional `extra_text`) are transmitted.

---

## 6. Printable Summary Handover Verification
1. Submit an intake form with selected answers (for example, selecting duration and risk factors).
2. When the result card renders, verify the **Based on your answers:** summary box displays the selected answers.
3. Click **Print summary** (or press Ctrl+P).
4. In the print preview, verify:
   - The print header includes both the user description and the list of answers given.
   - Navigation bars, buttons, and form inputs are hidden in print view.
   - Clinical sections and citations are preserved.
