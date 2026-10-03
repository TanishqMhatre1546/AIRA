"""Migrate urgency_rules.json to schema v2 with universal safety and refusal rules."""

import json
import sys
from pathlib import Path
from typing import Any

# Ensure backend root is in sys.path
backend_root = Path(__file__).resolve().parent.parent
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))

EMERGENCY_RULES: list[dict[str, Any]] = [
    # 1. Choking / Immediate Airway Obstruction (prioritized before general breathing distress)
    {
        "id": "ER-023",
        "kind": "emergency",
        "condition": "Choking and acute foreign body airway obstruction",
        "source_id": None,
        "source_page": None,
        "match": {
            "phrases": [
                "choking on food",
                "choking on",
                "food stuck in throat",
                "airway blocked food",
                "choking unable to breathe",
                "choking cannot breathe",
                "choking struggling to breathe",
            ],
            "requires_all": [],
        },
        "negatable": True,
        "response": (
            "Choking is a life-threatening airway emergency. Perform back blows or the "
            "Heimlich maneuver and call 112 immediately."
        ),
        "review_status": "pending_clinical_review",
    },
    # 2. Epiglottitis / Deep Neck Infection (prioritized before general angioedema)
    {
        "id": "ER-009",
        "kind": "emergency",
        "condition": (
            "Airway obstruction, epiglottitis, deep neck infection, or peritonsillar abscess"
        ),
        "source_id": "icmr-stw-pharyngitis-sore-throat",
        "source_page": 1,
        "match": {
            "phrases": [
                "drooling saliva",
                "drooling",
                "unable to swallow liquids",
                "cannot swallow liquids",
                "stridor",
                "muffled voice",
                "cannot open mouth",
                "unable to open mouth",
                "trismus",
                "grey membrane in throat",
                "gray membrane in throat",
                "throat swelling unable to swallow",
                "neck swelling",
            ],
            "requires_all": [],
        },
        "negatable": True,
        "response": (
            "Inability to swallow saliva, stridor (noisy high-pitched breathing), "
            "muffled voice, or a grey throat membrane indicate dangerous airway infections "
            "like epiglottitis or peritonsillar abscess. "
            "Go to a hospital emergency room immediately."
        ),
        "review_status": "source_backed",
    },
    # 3. Urticaria & Angioedema airway compromise
    {
        "id": "ER-001",
        "kind": "emergency",
        "condition": "Urticaria and Angioedema airway compromise",
        "source_id": "icmr-stw-urticaria-angioedema",
        "source_page": 1,
        "match": {
            "phrases": [
                "throat swelling",
                "tongue swelling",
                "lip swelling",
                "throat is swelling",
                "severe lip swelling",
                "choking sensation",
                "anaphylaxis",
                "throat closing",
                "airway swelling",
                "laryngeal angioedema",
                "respiratory distress",
                "swelling of the lips",
                "swelling of the tongue",
                "swelling of the throat",
            ],
            "requires_all": [],
        },
        "negatable": True,
        "response": (
            "This sounds like a severe allergic reaction (angioedema or anaphylaxis) "
            "affecting the airway. Call 112 or go to the nearest emergency room immediately."
        ),
        "review_status": "source_backed",
    },
    # 4. Severe Asthma Exacerbation (prioritized before general respiratory failure)
    {
        "id": "ER-007",
        "kind": "emergency",
        "condition": "Severe asthma exacerbation / acute respiratory distress",
        "source_id": "icmr-stw-acute-respiratory-infections",
        "source_page": 2,
        "match": {
            "phrases": [
                "severe asthma attack",
                "asthma attack",
                "inhaler not working",
                "chest indrawing",
                "chest in drawing",
                "wheezing severe",
                "severe wheezing",
                "cannot complete sentences",
                "too breathless to talk asthma",
                "asthma worsening",
            ],
            "requires_all": [],
        },
        "negatable": True,
        "response": (
            "Severe asthma attacks not relieved by inhalers or accompanied by chest indrawing "
            "are life-threatening. Call 112 or go to an emergency room immediately."
        ),
        "review_status": "source_backed",
    },
    # 5. Severe Respiratory Distress / Respiratory Failure
    {
        "id": "ER-006",
        "kind": "emergency",
        "condition": "Severe respiratory distress / respiratory failure",
        "source_id": "icmr-stw-acute-respiratory-infections",
        "source_page": 1,
        "match": {
            "phrases": [
                "struggling to breathe",
                "lips turning blue",
                "blue lips",
                "cannot breathe",
                "cant breathe",
                "gasping",
                "gasping for air",
                "cyanosis",
                "breathless and gasping",
                "can only speak few words",
                "too breathless to talk",
                "breathing very fast",
                "difficulty breathing",
                "short of breath",
            ],
            "requires_all": [],
        },
        "negatable": True,
        "response": (
            "Severe difficulty breathing, gasping, or bluish lips indicate respiratory distress. "
            "Call 112 or go to the nearest hospital immediately."
        ),
        "review_status": "source_backed",
    },
    # 6. Heart Attack / Acute Coronary Syndrome
    {
        "id": "ER-004",
        "kind": "emergency",
        "condition": "Heart attack warning signs",
        "source_id": "asha-ncd-hypertension",
        "source_page": 31,
        "match": {
            "phrases": [
                "chest pain",
                "chest pressure",
                "chest tightness",
                "heart attack",
                "crushing chest pain",
                "severe crushing chest pain",
                "chest heaviness",
                "pain in chest spreading to jaw",
                "pain radiating to left arm",
                "chest pain radiating",
                "pain in chest spreading",
            ],
            "requires_all": [],
        },
        "negatable": True,
        "response": (
            "Severe chest pain, chest tightness, or pain spreading to the arm or jaw are "
            "warning signs of a heart attack. Call 112 or go to the nearest hospital emergency "
            "department immediately."
        ),
        "review_status": "source_backed",
    },
    # 7. Stroke Warning Signs
    {
        "id": "ER-005",
        "kind": "emergency",
        "condition": "Stroke warning signs",
        "source_id": "asha-ncd-hypertension",
        "source_page": 31,
        "match": {
            "phrases": [
                "face drooping",
                "face drooping suddenly",
                "arm weakness",
                "arm weakness one side",
                "speech difficulty",
                "sudden speech difficulty",
                "cannot speak suddenly",
                "sudden vision loss",
                "paralysis one side",
                "stroke warning signs",
                "stroke",
                "facial droop",
                "slurred speech",
                "numbness on one side",
            ],
            "requires_all": [],
        },
        "negatable": True,
        "response": (
            "Sudden weakness on one side of the face or body, difficulty speaking, or "
            "sudden loss of vision are signs of a stroke. Time is critical. Call 112 or "
            "go to the nearest hospital with stroke facilities immediately."
        ),
        "review_status": "source_backed",
    },
    # 8. Bacterial Skin Infection Sepsis / Necrotizing
    {
        "id": "ER-002",
        "kind": "emergency",
        "condition": "Bacterial skin infection with sepsis or necrosis",
        "source_id": "icmr-stw-bacterial-skin-infections",
        "source_page": 1,
        "match": {
            "phrases": [
                "skin turning black",
                "skin turning dark",
                "skin peeling off",
                "necrotising",
                "necrotizing",
                "severe pain in wound then no pain",
                "severe pain in wound then no pain at all",
                "severe pain then no pain",
                "pain stopped suddenly",
                "blisters with dark fluid",
                "high fever and skin turning black",
                "collapsed after infection",
                "unconscious after infection",
                "unconscious and collapsed after infection",
            ],
            "requires_all": [],
        },
        "negatable": True,
        "response": (
            "Severe skin infections with rapidly spreading discoloration, peeling, or "
            "loss of sensation are dangerous emergencies. Call 112 or go to the nearest "
            "hospital immediately."
        ),
        "review_status": "source_backed",
    },
    # 9. UTI Sepsis / Pyelonephritis
    {
        "id": "ER-003",
        "kind": "emergency",
        "condition": "Urinary tract infection with sepsis / pyelonephritis",
        "source_id": "icmr-stw-urinary-tract-infection",
        "source_page": 1,
        "match": {
            "phrases": [
                "uti fever",
                "fever with chills",
                "shaking with fever",
                "shaking chills",
                "severe shaking chills",
                "back pain with fever",
                "flank pain fever",
                "kidney pain fever",
                "kidney pain",
                "urine infection with fever",
                "burning urination and fever",
                "fever and burning urination",
                "flank pain",
            ],
            "requires_all": [],
        },
        "negatable": True,
        "response": (
            "Fever with urinary symptoms, shaking chills, or back/flank pain indicates "
            "a serious upper kidney infection (pyelonephritis) or sepsis. Go to a hospital "
            "or doctor immediately."
        ),
        "review_status": "source_backed",
    },
    # 10. Rhinosinusitis Complications / Mucormycosis
    {
        "id": "ER-008",
        "kind": "emergency",
        "condition": "Acute rhinosinusitis with orbital or intracranial complications",
        "source_id": "icmr-stw-acute-rhinosinusitis",
        "source_page": 2,
        "match": {
            "phrases": [
                "swelling around eyes",
                "double vision with fever",
                "double vision",
                "stiff neck with high fever",
                "stiff neck",
                "black discharge from nose",
                "black nasal discharge",
                "reduced vision",
                "severe eye swelling",
                "eye swelling with fever",
                "proptosis",
                "orbital swelling",
                "severe sinus pain and stiff neck",
            ],
            "requires_all": [],
        },
        "negatable": True,
        "response": (
            "Sinus symptoms accompanied by eye swelling, vision changes, stiff neck, or "
            "dark tissue discharge indicate severe complications like orbital cellulitis or "
            "mucormycosis. Go to a hospital emergency department immediately."
        ),
        "review_status": "source_backed",
    },
    # 11. Severe Dehydration & Shock
    {
        "id": "ER-010",
        "kind": "emergency",
        "condition": "Severe dehydration and shock in acute diarrhoea",
        "source_id": "icmr-stw-acute-diarrhea",
        "source_page": 1,
        "match": {
            "phrases": [
                "skin pinch goes back very slowly",
                "skin pinch slow",
                "sunken eyes",
                "unable to drink any water",
                "unable to drink",
                "cannot drink water",
                "rapid weak pulse",
                "very rapid weak pulse",
                "very low blood pressure",
                "unconscious with diarrhea",
                "watery diarrhoea very weak",
                "passing many watery stools",
            ],
            "requires_all": [],
        },
        "negatable": True,
        "response": (
            "Signs of severe dehydration (lethargy, sunken eyes, skin pinch taking >2 seconds, "
            "inability to drink) can rapidly lead to shock. Go to a hospital or primary "
            "health centre immediately for IV fluids."
        ),
        "review_status": "source_backed",
    },
    # 12. Dengue Shock / Severe Dengue
    {
        "id": "ER-011",
        "kind": "emergency",
        "condition": "Dengue warning signs and severe dengue / dengue shock",
        "source_id": "icmr-stw-dengue-fever",
        "source_page": 1,
        "match": {
            "phrases": [
                "dengue warning signs",
                "dengue shock",
                "persistent vomiting and severe abdominal pain",
                "severe abdominal pain dengue",
                "bleeding from gums",
                "bleeding gums dengue",
                "cold clammy skin",
                "sudden drop in temperature with dengue",
                "extreme lethargy and restlessness",
                "dengue bleeding",
                "dengue restlessness",
            ],
            "requires_all": [],
        },
        "negatable": True,
        "response": (
            "Persistent vomiting, severe stomach pain, bleeding gums, or cold clammy skin "
            "in dengue are critical warning signs of severe dengue or shock. "
            "Go to a hospital immediately."
        ),
        "review_status": "source_backed",
    },
    # 13. Diabetic Hypoglycaemia
    {
        "id": "ER-012",
        "kind": "emergency",
        "condition": "Severe hypoglycaemia in diabetes",
        "source_id": "icmr-stw-diabetes-type2",
        "source_page": 2,
        "match": {
            "phrases": [
                "diabetic unconscious",
                "severe hypoglycaemia",
                "severe hypoglycemia",
                "diabetic passed out",
                "low blood sugar passed out",
                "unconscious diabetic",
                "diabetic cannot wake up",
                "sugar patient unconscious",
                "diabetic fainted",
                "emergency glucose",
            ],
            "requires_all": [],
        },
        "negatable": True,
        "response": (
            "Severe low blood sugar (hypoglycaemia) causing unconsciousness or inability to "
            "swallow is a medical emergency. Do not force fluids into an unconscious person's "
            "mouth. Call 112 or go to the nearest emergency room immediately."
        ),
        "review_status": "source_backed",
    },
    # 14. Severe Epistaxis (prioritized before universal bleeding)
    {
        "id": "ER-013",
        "kind": "emergency",
        "condition": "Severe or uncontrolled nosebleed (epistaxis)",
        "source_id": "icmr-stw-epistaxis-nosebleed",
        "source_page": 1,
        "match": {
            "phrases": [
                "nosebleed not stopping",
                "nose bleeding heavily",
                "heavy nosebleed",
                "coughing up blood nosebleed",
                "nosebleed after facial injury",
                "bleeding profusely after facial injury",
                "nose bleeding heavily and feeling dizzy",
                "nose bleeding heavily and dizziness",
                "nosebleed fainting",
                "nosebleed not stopping after 20 minutes",
                "nosebleed bleeding profusely",
                "nosebleed heavy bleeding",
                "nose heavy bleeding",
                "nosebleed heavy bleeding after facial injury",
            ],
            "requires_all": [],
        },
        "negatable": True,
        "response": (
            "A nosebleed that does not stop after 20 minutes of firm continuous pressure, "
            "causes heavy bleeding, follows facial trauma, or causes dizziness requires "
            "emergency care. Go to the nearest emergency room or hospital."
        ),
        "review_status": "source_backed",
    },
    # 15. Diabetic Foot Sepsis / Gangrene
    {
        "id": "ER-014",
        "kind": "emergency",
        "condition": "Diabetic foot ulcer with severe spreading infection or gangrene",
        "source_id": "icmr-stw-diabetes-type2",
        "source_page": 3,
        "match": {
            "phrases": [
                "diabetic foot red streaks",
                "red streaks spreading up leg",
                "black toe in diabetic",
                "black toe",
                "diabetic ulcer swelling rapidly",
                "gangrene in diabetic foot",
                "gangrene",
                "diabetic foot infection fever",
                "foul smell diabetic foot",
                "diabetic foot with red streaks",
            ],
            "requires_all": [],
        },
        "negatable": True,
        "response": (
            "Spreading redness, black discoloration (gangrene), foul odor, or high fever in "
            "a person with a diabetic foot ulcer indicates severe tissue infection or sepsis. "
            "Go to a hospital immediately."
        ),
        "review_status": "source_backed",
    },
    # 16. Internal Bleeding / GI Bleeding (prioritized before general bleeding)
    {
        "id": "ER-016",
        "kind": "emergency",
        "condition": "Vomiting blood, black or tarry stools",
        "source_id": None,
        "source_page": None,
        "match": {
            "phrases": [
                "vomiting blood",
                "blood in vomit",
                "vomit blood",
                "black stools",
                "black stool",
                "tarry stools",
                "tarry stool",
                "blood in throw up",
                "black potty",
                "tarry potty",
                "dark blood",
                "throwing up dark blood",
            ],
            "requires_all": [],
        },
        "negatable": True,
        "response": (
            "Vomiting blood or passing black, tarry stools indicates internal bleeding. "
            "Call 112 or go to the nearest hospital immediately."
        ),
        "review_status": "pending_clinical_review",
    },
    # 17. Bleeding in Pregnancy (prioritized before general bleeding)
    {
        "id": "ER-022",
        "kind": "emergency",
        "condition": "Bleeding during pregnancy",
        "source_id": None,
        "source_page": None,
        "match": {
            "phrases": [
                "bleeding in pregnancy",
                "pregnant and bleeding",
                "pregnancy bleeding",
                "spotting in pregnancy",
                "pregnant bleeding",
                "bleeding during pregnancy",
                "pregnant and bleeding heavily",
                "pregnant and heavy bleeding",
            ],
            "requires_all": [],
        },
        "negatable": True,
        "response": (
            "Vaginal bleeding during pregnancy requires immediate emergency obstetric "
            "assessment. Go to the nearest maternity hospital or call 112 or 102 immediately."
        ),
        "review_status": "pending_clinical_review",
    },
    # 18. Universal: Severe or Uncontrolled Bleeding
    {
        "id": "ER-015",
        "kind": "emergency",
        "condition": "Severe or uncontrolled bleeding",
        "source_id": None,
        "source_page": None,
        "match": {
            "phrases": [
                "heavy bleeding",
                "bleeding profusely",
                "bleeding wont stop",
                "blood wont stop",
                "bleeding heavily",
                "severe bleeding",
                "arterial bleeding",
                "spurting blood",
                "uncontrolled bleeding",
            ],
            "requires_all": [],
        },
        "negatable": True,
        "response": (
            "Severe or uncontrolled bleeding is a medical emergency. Apply firm, continuous "
            "pressure with a clean cloth and call 112 or go to the nearest hospital immediately."
        ),
        "review_status": "pending_clinical_review",
    },
    # 19. Universal: Seizures / Fits
    {
        "id": "ER-017",
        "kind": "emergency",
        "condition": "Seizure or fits",
        "source_id": None,
        "source_page": None,
        "match": {
            "phrases": [
                "seizure",
                "having a seizure",
                "fits",
                "having fits",
                "convulsions",
                "convulsion",
                "seizures",
                "mirgi",
            ],
            "requires_all": [],
        },
        "negatable": True,
        "response": (
            "Seizures or convulsions require immediate medical evaluation. Ensure the person "
            "is in a safe space on their side and call 112 or go to the nearest hospital."
        ),
        "review_status": "pending_clinical_review",
    },
    # 20. Universal: Unconsciousness / Unresponsiveness
    {
        "id": "ER-018",
        "kind": "emergency",
        "condition": "Unconscious or not responding",
        "source_id": None,
        "source_page": None,
        "match": {
            "phrases": [
                "unconscious",
                "passed out",
                "not responding",
                "unresponsive",
                "fainted and not waking up",
                "collapsed",
                "cannot wake up",
                "not waking up",
            ],
            "requires_all": [],
        },
        "negatable": True,
        "response": (
            "Loss of consciousness or unresponsiveness is a critical emergency. "
            "Call 112 or go to the nearest hospital immediately."
        ),
        "review_status": "pending_clinical_review",
    },
    # 21. Universal: Poisoning / Overdose
    {
        "id": "ER-019",
        "kind": "emergency",
        "condition": "Poisoning, overdose, swallowed pesticide or chemicals",
        "source_id": None,
        "source_page": None,
        "match": {
            "phrases": [
                "poisoning",
                "drank poison",
                "swallowed poison",
                "swallowed pesticide",
                "drank pesticide",
                "swallowed chemical",
                "chemical poisoning",
                "overdose",
                "drug overdose",
                "swallowed rat poison",
                "consumed insecticide",
            ],
            "requires_all": [],
        },
        "negatable": True,
        "response": (
            "Poisoning or chemical ingestion is a life-threatening emergency. Call 112 or "
            "go to the nearest hospital immediately with the container of the substance."
        ),
        "review_status": "pending_clinical_review",
    },
    # 22. Universal: Snake Bite
    {
        "id": "ER-020",
        "kind": "emergency",
        "condition": "Snake bite",
        "source_id": None,
        "source_page": None,
        "match": {
            "phrases": [
                "snake bite",
                "bitten by snake",
                "snakebite",
                "snake bit",
            ],
            "requires_all": [],
        },
        "negatable": True,
        "response": (
            "A snake bite requires immediate emergency treatment with anti-venom. "
            "Keep the bitten limb still, do not cut or suck the bite, and go to the "
            "nearest hospital immediately. Call 112."
        ),
        "review_status": "pending_clinical_review",
    },
    # 23. Universal: Head Injury Red Flags
    {
        "id": "ER-021",
        "kind": "emergency",
        "condition": "Head injury with vomiting, drowsiness or confusion",
        "source_id": None,
        "source_page": None,
        "match": {
            "phrases": [
                "head injury vomiting",
                "head injury confusion",
                "head injury drowsiness",
                "hit head vomiting",
                "head trauma vomiting",
                "fall on head vomiting",
                "head injury unconscious",
            ],
            "requires_all": [],
        },
        "negatable": True,
        "response": (
            "Head injury accompanied by vomiting, drowsiness, or confusion may indicate "
            "bleeding in the brain. Go to the nearest hospital or call 112 immediately."
        ),
        "review_status": "pending_clinical_review",
    },
]

CRISIS_RULES: list[dict[str, Any]] = [
    {
        "id": "CR-001",
        "kind": "crisis",
        "condition": "Self-harm or suicide crisis",
        "source_id": None,
        "source_page": None,
        "match": {
            "phrases": [
                "suicide",
                "want to die",
                "kill myself",
                "end my life",
                "suicidal",
                "self harm",
                "harm myself",
                "thinking of suicide",
                "commit suicide",
            ],
            "requires_all": [],
        },
        "negatable": False,
        "response": (
            "If you are feeling overwhelmed or having thoughts of self-harm, support is "
            "available right now. Please call the national mental health helpline Tele-MANAS "
            "at 14416 (toll-free, 24/7) or call 112. You do not have to go through this alone."
        ),
        "review_status": "pending_clinical_review",
    }
]

REFUSAL_RULES: list[dict[str, Any]] = [
    {
        "id": "RF-001",
        "kind": "refusal",
        "condition": "Medication dosage request",
        "source_id": None,
        "source_page": None,
        "match": {
            "phrases": [],
            "requires_all": [
                [
                    "how much",
                    "how many",
                    "what dose",
                    "dose of",
                    "dosage",
                    "how often",
                    "how long should i take",
                    "how long to take",
                    "what dosage",
                    "how many tablets",
                    "mg",
                ],
                [
                    "tablet",
                    "tablets",
                    "capsule",
                    "capsules",
                    "syrup",
                    "medicine",
                    "medication",
                    "drug",
                    "@drugs",
                ],
            ],
        },
        "negatable": False,
        "response": (
            "AIRA cannot give medication doses or drug prescription instructions. "
            "Please consult a doctor or pharmacist for safe, personalized medication advice."
        ),
        "review_status": "pending_clinical_review",
    },
    {
        "id": "RF-002",
        "kind": "refusal",
        "condition": "Direct diagnosis request",
        "source_id": None,
        "source_page": None,
        "match": {
            "phrases": [
                "do i have",
                "diagnose me",
                "what disease do i have",
                "what illness do i have",
                "is this cancer",
                "tell me what i have",
                "do i suffer from",
                "diagnose my condition",
            ],
            "requires_all": [],
        },
        "negatable": False,
        "response": (
            "AIRA provides guideline information only and cannot diagnose medical conditions. "
            "Please see a qualified healthcare professional for a clinical examination and "
            "diagnosis."
        ),
        "review_status": "pending_clinical_review",
    },
    {
        "id": "RF-003",
        "kind": "refusal",
        "condition": "Drug interaction advice request",
        "source_id": None,
        "source_page": None,
        "match": {
            "phrases": [
                "with alcohol",
                "with beer",
                "with wine",
                "with whisky",
                "with rum",
            ],
            "requires_all": [
                [
                    "take with",
                    "mix with",
                    "combine with",
                    "together with",
                    "interaction",
                    "interactions",
                    "safe with",
                    "can i take with",
                    "can i mix",
                    "along with",
                    "taken with",
                    "together",
                    "mix",
                    "combine",
                    "interact",
                ],
                [
                    "medicine",
                    "medication",
                    "tablet",
                    "tablets",
                    "syrup",
                    "drug",
                    "@drugs",
                    "alcohol",
                    "beer",
                    "wine",
                    "whisky",
                    "rum",
                ],
            ],
        },
        "negatable": False,
        "response": (
            "AIRA cannot evaluate drug-drug or drug-alcohol interactions. Please consult a "
            "doctor or pharmacist before combining any medications."
        ),
        "review_status": "pending_clinical_review",
    },
]

SCOPE_RULES: list[dict[str, Any]] = [
    {
        "id": "SC-100",
        "kind": "scope",
        "condition": "Pediatric / child scope exclusion",
        "source_id": None,
        "source_page": None,
        "match": {
            "phrases": [
                "baby",
                "infant",
                "newborn",
                "toddler",
                "my child",
                "my son",
                "my daughter",
                "my kid",
                "my baby",
                "months old",
                "month old",
                "1 year old",
                "2 year old",
                "3 year old",
                "4 year old",
                "5 year old",
                "6 year old",
                "7 year old",
                "8 year old",
                "9 year old",
                "10 year old",
                "11 year old",
                "12 year old",
                "1 years old",
                "2 years old",
                "3 years old",
                "4 years old",
                "5 years old",
                "6 years old",
                "7 years old",
                "8 years old",
                "9 years old",
                "10 years old",
                "11 years old",
                "12 years old",
            ],
            "requires_all": [],
        },
        "negatable": False,
        "response": (
            "AIRA version 1 covers adults. For a child who is unwell, see a doctor or "
            "health worker today. In an emergency call 112."
        ),
        "review_status": "pending_clinical_review",
    }
]


def build_v2_rules() -> dict[str, Any]:
    """Assemble complete v2 urgency rules structure."""
    all_rules: list[dict[str, Any]] = []

    # 1. Emergency Rules (23 rules)
    all_rules.extend(EMERGENCY_RULES)

    # 2. Crisis Rules CR-001
    all_rules.extend(CRISIS_RULES)

    # 3. Refusal Rules RF-001 to RF-003
    all_rules.extend(REFUSAL_RULES)

    # 4. Scope Rules SC-100
    all_rules.extend(SCOPE_RULES)

    return {
        "meta": {
            "description": "AIRA deterministic triage and safety rules (Schema v2).",
            "version": "2.0.0",
            "last_updated": "2026-10-03",
        },
        "rules": all_rules,
    }


def main() -> None:
    """Run rule migration and save updated urgency_rules.json."""
    rules_path = backend_root / "data" / "curated" / "urgency_rules.json"
    v2_data = build_v2_rules()

    with open(rules_path, "w", encoding="utf-8") as f:
        json.dump(v2_data, f, indent=2, ensure_ascii=False)
        f.write("\n")

    print(f"Successfully generated {len(v2_data['rules'])} rules in Schema v2: {rules_path}")


if __name__ == "__main__":
    main()
