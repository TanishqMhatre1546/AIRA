# AIRA Clinical Data Sources and Provenance

AIRA indexes and cites exclusively official, peer-reviewed clinical guidelines published by the Indian Council of Medical Research (ICMR) and the Ministry of Health and Family Welfare (MOHFW), Government of India.

---

## Authoritative Guideline Documents

| Source Document Title | Publisher | Edition Year | Official URL | Date Retrieved | Licence / Reuse Status | Supported Condition(s) |
|---|---|---|---|---|---|---|
| **Standard Treatment Workflows of India (STW) - Acute Diarrhea in Adults** | Indian Council of Medical Research (ICMR) | 2022 | `https://main.icmr.nic.in/` | 2026-10-01 | to be confirmed | `acute_diarrhea` |
| **Standard Treatment Workflows of India (STW) - Common Cold and Acute Respiratory Infections** | Indian Council of Medical Research (ICMR) | 2022 | `https://main.icmr.nic.in/` | 2026-10-01 | to be confirmed | `acute_respiratory_infections` |
| **Standard Treatment Workflows of India (STW) - Acute Rhinosinusitis** | Indian Council of Medical Research (ICMR) | 2022 | `https://main.icmr.nic.in/` | 2026-10-01 | to be confirmed | `acute_rhinosinusitis` |
| **Standard Treatment Workflows of India (STW) - Bacterial Skin Infections** | Indian Council of Medical Research (ICMR) | 2022 | `https://main.icmr.nic.in/` | 2026-10-01 | to be confirmed | `bacterial_skin_infections` |
| **Standard Treatment Workflows of India (STW) - Dengue Fever** | Indian Council of Medical Research (ICMR) | 2022 | `https://main.icmr.nic.in/` | 2026-10-01 | to be confirmed | `dengue_fever` |
| **Standard Treatment Workflows of India (STW) - Dermatophytosis (Ringworm)** | Indian Council of Medical Research (ICMR) | 2022 | `https://main.icmr.nic.in/` | 2026-10-01 | to be confirmed | `dermatophytosis` |
| **Standard Treatment Workflows of India (STW) - Type 2 Diabetes Mellitus** | Indian Council of Medical Research (ICMR) | 2022 | `https://main.icmr.nic.in/` | 2026-10-01 | to be confirmed | `diabetes_type2` |
| **Standard Treatment Workflows of India (STW) - Eczema and Dermatitis** | Indian Council of Medical Research (ICMR) | 2022 | `https://main.icmr.nic.in/` | 2026-10-01 | to be confirmed | `eczema_dermatitis` |
| **Standard Treatment Workflows of India (STW) - Epistaxis (Nosebleed)** | Indian Council of Medical Research (ICMR) | 2022 | `https://main.icmr.nic.in/` | 2026-10-01 | to be confirmed | `epistaxis_nosebleed` |
| **Standard Treatment Workflows of India (STW) - Headache Evaluation and Management** | Indian Council of Medical Research (ICMR) | 2022 | `https://main.icmr.nic.in/` | 2026-10-01 | to be confirmed | `headache` |
| **Standard Treatment Workflows of India (STW) - Hypertension in Adults** | Indian Council of Medical Research (ICMR) | 2022 | `https://main.icmr.nic.in/` | 2026-10-01 | to be confirmed | `hypertension` |
| **Standard Treatment Workflows of India (STW) - Acute Pharyngitis (Sore Throat)** | Indian Council of Medical Research (ICMR) | 2022 | `https://main.icmr.nic.in/` | 2026-10-01 | to be confirmed | `pharyngitis_sore_throat` |
| **Standard Treatment Workflows of India (STW) - Scabies Management** | Indian Council of Medical Research (ICMR) | 2022 | `https://main.icmr.nic.in/` | 2026-10-01 | to be confirmed | `scabies` |
| **Standard Treatment Workflows of India (STW) - Uncomplicated Urinary Tract Infection** | Indian Council of Medical Research (ICMR) | 2022 | `https://main.icmr.nic.in/` | 2026-10-01 | to be confirmed | `urinary_tract_infection` |
| **Standard Treatment Workflows of India (STW) - Urticaria and Angioedema** | Indian Council of Medical Research (ICMR) | 2022 | `https://main.icmr.nic.in/` | 2026-10-01 | to be confirmed | `urticaria_angioedema` |

---

## Provenance Integrity and Validation

1. **Chunk Attribution:** Each of the 85 index chunks is directly attributed to an explicit page and paragraph in the source JSON files stored in `backend/data/curated/`.
2. **Provenance Audit:** Run `python scripts/audit_provenance.py` in `backend/` to verify that every extracted claim references an extant chunk.
3. **Checksum Invariant:** The sha256 checksums of the corpus files are compiled into `backend/data/index/manifest.json`. Any unauthorized edit to guideline texts invalidates the startup checksum check.
