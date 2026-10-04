# AIRA Clinical Review and Expert Sign-Off Protocol

This document serves as the formal clinical evaluation and audit protocol for medical reviewers evaluating AIRA version 1.0.

Medical reviewers should verify that triage levels, red flags, emergency rules, condition profiles, clinical modifiers, and helplines accurately reflect published Indian Council of Medical Research (ICMR) and Ministry of Health and Family Welfare (MOHFW) clinical guidelines.

---

## 1. Emergency Safety Rules Audit

| Rule ID | Clinical Condition / Hazard | ICMR Source Document | Trigger Criteria / Red Flag Signs | Reviewer Decision |
|---|---|---|---|---|
| **ER-001** | Urticaria and Angioedema Airway Compromise | `icmr-stw-urticaria-angioedema` (p.1) | Throat, tongue, or lip swelling, stridor, anaphylaxis, respiratory distress. | [ ] Approved [ ] Revision Needed |
| **ER-002** | Rapidly Spreading Skin Infection / Necrosis | `icmr-stw-bacterial-skin-infections` (p.1) | Spreading erythema, blistering, crepitus, severe pain out of proportion, systemic toxicity. | [ ] Approved [ ] Revision Needed |
| **ER-003** | Severe Dehydration / Hypovolemic Shock | `icmr-stw-acute-diarrhea` (p.1) | Lethargy, sunken eyes, skin pinch > 2 seconds, inability to drink fluids, anuria. | [ ] Approved [ ] Revision Needed |
| **ER-004** | Severe Dengue Warning Signs / Shock | `icmr-stw-dengue-fever` (p.1) | Persistent vomiting, severe abdominal pain, mucosal bleeding, fluid accumulation, cold clammy extremities. | [ ] Approved [ ] Revision Needed |
| **ER-005** | Acute Meningism / Intracranial Emergency | `icmr-stw-headache` (p.1) | Thunderclap headache, neck stiffness with fever, altered sensorium, new focal neurological deficits. | [ ] Approved [ ] Revision Needed |
| **ER-006** | Severe Acute Respiratory Distress | `icmr-stw-acute-respiratory-infections` (p.1) | Severe breathlessness, respiratory rate > 30/min, central cyanosis, oxygen saturation < 90%. | [ ] Approved [ ] Revision Needed |
| **ER-007** | Hypertensive Crisis with End-Organ Damage | `icmr-stw-hypertension` (p.1) | Severe headache, chest pain, dyspnea, visual disturbances with severely elevated blood pressure. | [ ] Approved [ ] Revision Needed |
| **ER-008** | Acute Diabetic Emergencies (DKA / HHS) | `icmr-stw-diabetes-type2` (p.1) | Deep rapid breathing (Kussmaul), fruity breath odor, severe dehydration, acute confusion, extreme hyperglycemia. | [ ] Approved [ ] Revision Needed |
| **ER-009** | Deep Neck Infection / Airway Obstruction | `icmr-stw-pharyngitis-sore-throat` (p.1) | Drooling saliva, inability to swallow liquids, stridor, trismus, grey throat membrane. | [ ] Approved [ ] Revision Needed |
| **ER-010** | Uncontrolled Severe Epistaxis | `icmr-stw-epistaxis-nosebleed` (p.1) | Continuous bleeding > 20 minutes despite bilateral pressure, hemodynamic instability. | [ ] Approved [ ] Revision Needed |
| **ER-011** | Acute Pyelonephritis / Urosepsis | `icmr-stw-urinary-tract-infection` (p.1) | High fever with rigors, flank pain, costovertebral angle tenderness, nausea/vomiting. | [ ] Approved [ ] Revision Needed |
| **ER-012** | Acute Orbital / Intracranial Sinus Complications | `icmr-stw-acute-rhinosinusitis` (p.1) | Periorbital swelling, proptosis, visual loss, ophthalmoplegia, severe frontal swelling (Pott puffy tumor). | [ ] Approved [ ] Revision Needed |
| **ER-013** | Secondary Infection in Extensive Eczema | `icmr-stw-eczema-dermatitis` (p.1) | Eczema herpeticum, widespread pustules with high fever, systemic illness. | [ ] Approved [ ] Revision Needed |
| **ER-014** | Craniomaxillofacial Trauma / Basilar Skull Fracture | `icmr-stw-epistaxis-nosebleed` (p.1) | Clear CSF rhinorrhea, periorbital ecchymosis, severe head trauma history. | [ ] Approved [ ] Revision Needed |
| **ER-015** | Extensive Crusted (Norwegian) Scabies | `icmr-stw-scabies` (p.1) | Severe hyperkeratotic crusting with high risk of secondary bacteremia. | [ ] Approved [ ] Revision Needed |
| **ER-016** | Extensive / Refractory Dermatophytosis | `icmr-stw-dermatophytosis` (p.1) | Erythroderma, severe secondary bacterial cellulitis from tinea. | [ ] Approved [ ] Revision Needed |

---

## 2. Condition Baseline Floors and Duration Thresholds

| Condition ID | Clinical Condition Name | Baseline Triage Floor | Duration Threshold for Escalation |
|---|---|---|---|
| `acute_diarrhea` | Acute Diarrhea in Adults | `SELF_CARE` | > 3 days -> `SEE_DOCTOR` |
| `acute_respiratory_infections` | Common Cold and Upper Respiratory Infection | `SELF_CARE` | > 10 days -> `SEE_DOCTOR` |
| `acute_rhinosinusitis` | Acute Rhinosinusitis | `SELF_CARE` | > 10 days -> `SEE_DOCTOR` |
| `bacterial_skin_infections` | Impetigo, Folliculitis, Furunculosis | `SEE_DOCTOR` | > 7 days -> `SEE_DOCTOR` |
| `dengue_fever` | Dengue Fever (Uncomplicated) | `SEE_DOCTOR` | > 5 days -> `SEE_DOCTOR` |
| `dermatophytosis` | Tinea Infections (Ringworm) | `SEE_DOCTOR` | > 14 days -> `SEE_DOCTOR` |
| `diabetes_type2` | Type 2 Diabetes Mellitus Management | `SEE_DOCTOR` | Continuous / Ongoing |
| `eczema_dermatitis` | Eczema and Contact Dermatitis | `SELF_CARE` | > 14 days -> `SEE_DOCTOR` |
| `epistaxis_nosebleed` | Epistaxis (Mild Anterior Nosebleed) | `SELF_CARE` | > 1 day -> `SEE_DOCTOR` |
| `headache` | Tension / Mild Primary Headache | `SELF_CARE` | > 3 days -> `SEE_DOCTOR` |
| `hypertension` | Hypertension in Adults | `SEE_DOCTOR` | Continuous / Ongoing |
| `pharyngitis_sore_throat` | Acute Pharyngitis (Sore Throat) | `SELF_CARE` | > 5 days -> `SEE_DOCTOR` |
| `scabies` | Scabies Infestation | `SEE_DOCTOR` | > 7 days -> `SEE_DOCTOR` |
| `urinary_tract_infection` | Uncomplicated Urinary Tract Infection | `SEE_DOCTOR` | > 2 days -> `SEE_DOCTOR` |
| `urticaria_angioedema` | Mild Acute Urticaria (Hives) | `SELF_CARE` | > 14 days -> `SEE_DOCTOR` |

---

## 3. High-Risk Clinical Modifiers

Clinical status preambles that deterministically escalate triage urgency from `SELF_CARE` to `SEE_DOCTOR`:

| Vulnerability Axis | Triggering Status | Affected Conditions | Clinical Justification and Source |
|---|---|---|---|
| **Pregnancy** | Pregnant or postpartum | Headache, Fever, RTI, Epistaxis | Rule out pre-eclampsia, viral fetopathy, severe anemia (`icmr-stw-headache`, p.1). |
| **Immunocompromised** | On chemotherapy, HIV+, immunosuppressants | All conditions | High vulnerability to fulminant secondary bacterial/fungal infections (`icmr-stw-bacterial-skin-infections`, p.1). |
| **Diabetes** | Diabetic patient | Skin infections, Rhinosinusitis, Nosebleeds | Increased risk of necrotizing fasciitis, mucormycosis, vascular fragility (`icmr-stw-bacterial-skin-infections`, p.1). |
| **Advanced Age** | Age >= 65 years | Respiratory infections, Diarrhea, Dengue | Rapid clinical decompensation and atypical presentations in geriatric patients (`icmr-stw-dengue-fever`, p.1). |

---

## 4. Emergency Helplines Audit

| Service Label | Telephone Number | Availability | Scope |
|---|---|---|---|
| **National Emergency Support** | `112` | 24/7 Nationwide | All acute life-threatening emergencies (Police, Fire, Medical). |
| **Emergency Medical Services** | `108` | 24/7 State-Level | Dedicated emergency ambulance transport. |
| **Patient Transport Service** | `102` | 24/7 State-Level | Non-critical and maternal/neonatal transport. |
| **Tele-MANAS** | `14416` / `1800-891-4416` | 24/7 Nationwide | Ministry of Health national tele-mental health helpline. |

---

## 5. Clinical Reviewer Sign-Off

### Reviewer 1:
- **Full Name:** __________________________________________________
- **Medical Registration Number (NMC / State Council):** ________________________
- **Specialty / Qualification:** _______________________________________
- **Date of Review:** ________________________
- **Sign-Off Status:** [ ] Approved for Deployment   [ ] Revisions Required
- **Reviewer Comments:**
  ____________________________________________________________________
  ____________________________________________________________________
  ____________________________________________________________________

### Reviewer 2 (Independent Auditor):
- **Full Name:** __________________________________________________
- **Medical Registration Number (NMC / State Council):** ________________________
- **Specialty / Qualification:** _______________________________________
- **Date of Review:** ________________________
- **Sign-Off Status:** [ ] Approved for Deployment   [ ] Revisions Required
- **Reviewer Comments:**
  ____________________________________________________________________
  ____________________________________________________________________
  ____________________________________________________________________

---

## 6. Guided Intake Rules and Questions Audit (Pending Clinical Review)

The following intake question set and newly mapped escalation rules were added for guided intake under `review_status: pending_clinical_review`.

### A. Emergency and See-Doctor Rules Added:
| Rule ID | Level | Condition | Trigger Criteria | Source Document | Provenance Item ID | Review Status |
|---|---|---|---|---|---|---|
| **ER-024** | `EMERGENCY` | `headache` | Sudden severe thunderclap headache or headache after injury | `icmr-stw-headache` (p.1) | `headache-danger-1` | pending_clinical_review |
| **SD-001** | `SEE_DOCTOR` | `acute_diarrhea` | Fever or persistent vomiting with diarrhea | `icmr-stw-acute-diarrhea` (p.1) | `diarrhea-danger-3` | pending_clinical_review |
| **SD-002** | `SEE_DOCTOR` | `acute_respiratory_infections` | High fever or worsening cough with phlegm | `icmr-stw-acute-respiratory-infections` (p.1) | `ari-danger-2` | pending_clinical_review |
| **SD-003** | `SEE_DOCTOR` | `acute_rhinosinusitis` | Severe facial pain, swelling or high fever | `icmr-stw-acute-rhinosinusitis` (p.1) | `sinusitis-danger-1` | pending_clinical_review |
| **SD-004** | `SEE_DOCTOR` | `pharyngitis_sore_throat` | Inability to swallow saliva or severe earache | `icmr-stw-pharyngitis-sore-throat` (p.1) | `pharyngitis-danger-1` | pending_clinical_review |
| **SD-005** | `SEE_DOCTOR` | `headache` | Headache worsening on coughing or bending | `icmr-stw-headache` (p.1) | `headache-danger-2` | pending_clinical_review |
| **SD-006** | `SEE_DOCTOR` | `urinary_tract_infection` | Shivering with high fever or flank pain | `icmr-stw-urinary-tract-infection` (p.1) | `uti-danger-1` | pending_clinical_review |
| **SD-007** | `SEE_DOCTOR` | `dengue_fever` | Persistent abdominal pain or persistent vomiting | `icmr-stw-dengue-fever` (p.1) | `dengue-danger-1` | pending_clinical_review |
| **SD-008** | `SEE_DOCTOR` | `epistaxis_nosebleed` | Nosebleed lasting more than 15 minutes | `icmr-stw-epistaxis-nosebleed` (p.1) | `epistaxis-danger-1` | pending_clinical_review |
| **SD-009** | `SEE_DOCTOR` | `bacterial_skin_infections` | Spreading redness or warm tender skin sore | `icmr-stw-bacterial-skin-infections` (p.1) | `skin-danger-1` | pending_clinical_review |
| **SD-010** | `SEE_DOCTOR` | `scabies` | Crusted skin sores or secondary pus discharge | `icmr-stw-scabies` (p.1) | `scabies-danger-1` | pending_clinical_review |
| **SD-011** | `SEE_DOCTOR` | `eczema_dermatitis` | Weeping skin lesions with yellow crusts | `icmr-stw-eczema-dermatitis` (p.1) | `eczema-danger-1` | pending_clinical_review |
| **SD-012** | `SEE_DOCTOR` | `urticaria_angioedema` | Swelling of lips or eyes without breathing issues | `icmr-stw-urticaria-angioedema` (p.1) | `urticaria-danger-2` | pending_clinical_review |

### B. Intake Questions File:
- Location: `backend/data/intake/intake_questions.json`
- Total conditions mapped: 15
- General emergency signs mapped: 7
- Area options mapped: 10
- All options traceable to curated ICMR STW item IDs and page numbers.
- Decision: [ ] Approved [ ] Revision Needed
