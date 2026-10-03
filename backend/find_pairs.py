import json
from pathlib import Path

curated_dir = Path("data/curated")
chunks = []
for p in curated_dir.glob("*.json"):
    if p.name in ("urgency_rules.json", "manifest.json"):
        continue
    data = json.loads(p.read_text(encoding="utf-8"))
    cond_id = p.stem
    doc_id = data.get("id")
    for sec in data.get("sections", []):
        page = sec.get("page", 1)
        for item in sec.get("items", []):
            chunks.append({
                "cond_id": cond_id,
                "doc_id": doc_id,
                "page": page,
                "text": item
            })

pairs = [
    ("pregnancy", "headache", ["pregnant", "pregnancy"]),
    ("pregnancy", "urinary_tract_infection", ["pregnant", "pregnancy"]),
    ("pregnancy", "dengue_fever", ["pregnant", "pregnancy"]),
    ("pregnancy", "acute_respiratory_infections", ["pregnant", "pregnancy"]),
    ("pregnancy", "epistaxis_nosebleed", ["pregnant", "pregnancy"]),
    ("diabetes", "urinary_tract_infection", ["diabet", "sugar"]),
    ("diabetes", "bacterial_skin_infections", ["diabet", "sugar"]),
    ("diabetes", "acute_rhinosinusitis", ["diabet", "sugar"]),
    ("diabetes", "acute_respiratory_infections", ["diabet", "sugar"]),
    ("diabetes", "acute_diarrhea", ["diabet", "sugar"]),
    ("diabetes", "dengue_fever", ["diabet", "sugar"]),
    ("diabetes", "epistaxis_nosebleed", ["diabet", "sugar"]),
    ("diabetes", "eczema_dermatitis", ["diabet", "sugar"]),
    ("immunocompromised", "bacterial_skin_infections", ["immun", "cancer", "steroid", "hiv"]),
    ("immunocompromised", "acute_rhinosinusitis", ["immun", "cancer", "steroid", "hiv"]),
    ("immunocompromised", "headache", ["immun", "cancer", "steroid", "hiv"]),
    ("immunocompromised", "scabies", ["immun", "cancer", "steroid", "hiv", "crusted"]),
    ("immunocompromised", "acute_respiratory_infections", ["immun", "cancer", "steroid", "hiv"]),
    ("age 65 or more", "dengue_fever", ["elderly", "older", "60", "65", "age"]),
    ("age 65 or more", "acute_respiratory_infections", ["elderly", "older", "60", "65", "age"]),
]

for mod, cond, keywords in pairs:
    match = None
    for c in chunks:
        if c["cond_id"] == cond:
            txt = c["text"]
            if any(k in txt.lower() for k in keywords):
                words = txt.split()
                short_q = " ".join(words[:12])
                match = (c["doc_id"], c["page"], short_q)
                break
    if match:
        print(f"| {mod} + {cond} | `{match[0]}` | p.{match[1]} | \"{match[2]}\" |")
    else:
        print(f"| {mod} + {cond} | NONE | - | - |")
