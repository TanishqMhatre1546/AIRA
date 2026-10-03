import React, { useState, useEffect } from "react";
import { getSources } from "../api/client";

const FALLBACK_SOURCES = [
  {
    title: "Standard Treatment Workflows of India (STW) - Acute Diarrhea in Adults",
    publisher: "Indian Council of Medical Research (ICMR)",
    edition_year: "2022",
    url: "https://main.icmr.nic.in/",
    conditions: ["Acute Diarrhea"],
  },
  {
    title: "Standard Treatment Workflows of India (STW) - Dengue Fever",
    publisher: "Indian Council of Medical Research (ICMR)",
    edition_year: "2022",
    url: "https://main.icmr.nic.in/",
    conditions: ["Dengue Fever"],
  },
  {
    title: "Standard Treatment Workflows of India (STW) - Common Cold and Acute Respiratory Infections",
    publisher: "Indian Council of Medical Research (ICMR)",
    edition_year: "2022",
    url: "https://main.icmr.nic.in/",
    conditions: ["Acute Respiratory Infections"],
  },
  {
    title: "Standard Treatment Workflows of India (STW) - Acute Rhinosinusitis",
    publisher: "Indian Council of Medical Research (ICMR)",
    edition_year: "2022",
    url: "https://main.icmr.nic.in/",
    conditions: ["Acute Rhinosinusitis"],
  },
  {
    title: "Standard Treatment Workflows of India (STW) - Bacterial Skin Infections",
    publisher: "Indian Council of Medical Research (ICMR)",
    edition_year: "2022",
    url: "https://main.icmr.nic.in/",
    conditions: ["Bacterial Skin Infections"],
  },
  {
    title: "Standard Treatment Workflows of India (STW) - Dermatophytosis (Ringworm)",
    publisher: "Indian Council of Medical Research (ICMR)",
    edition_year: "2022",
    url: "https://main.icmr.nic.in/",
    conditions: ["Dermatophytosis"],
  },
  {
    title: "Standard Treatment Workflows of India (STW) - Type 2 Diabetes Mellitus",
    publisher: "Indian Council of Medical Research (ICMR)",
    edition_year: "2022",
    url: "https://main.icmr.nic.in/",
    conditions: ["Type 2 Diabetes"],
  },
  {
    title: "Standard Treatment Workflows of India (STW) - Eczema and Dermatitis",
    publisher: "Indian Council of Medical Research (ICMR)",
    edition_year: "2022",
    url: "https://main.icmr.nic.in/",
    conditions: ["Eczema"],
  },
  {
    title: "Standard Treatment Workflows of India (STW) - Epistaxis (Nosebleed)",
    publisher: "Indian Council of Medical Research (ICMR)",
    edition_year: "2022",
    url: "https://main.icmr.nic.in/",
    conditions: ["Epistaxis"],
  },
  {
    title: "Standard Treatment Workflows of India (STW) - Headache Evaluation",
    publisher: "Indian Council of Medical Research (ICMR)",
    edition_year: "2022",
    url: "https://main.icmr.nic.in/",
    conditions: ["Headache"],
  },
  {
    title: "Standard Treatment Workflows of India (STW) - Hypertension in Adults",
    publisher: "Indian Council of Medical Research (ICMR)",
    edition_year: "2022",
    url: "https://main.icmr.nic.in/",
    conditions: ["Hypertension"],
  },
  {
    title: "Standard Treatment Workflows of India (STW) - Acute Pharyngitis (Sore Throat)",
    publisher: "Indian Council of Medical Research (ICMR)",
    edition_year: "2022",
    url: "https://main.icmr.nic.in/",
    conditions: ["Pharyngitis"],
  },
  {
    title: "Standard Treatment Workflows of India (STW) - Scabies Management",
    publisher: "Indian Council of Medical Research (ICMR)",
    edition_year: "2022",
    url: "https://main.icmr.nic.in/",
    conditions: ["Scabies"],
  },
  {
    title: "Standard Treatment Workflows of India (STW) - Uncomplicated Urinary Tract Infection",
    publisher: "Indian Council of Medical Research (ICMR)",
    edition_year: "2022",
    url: "https://main.icmr.nic.in/",
    conditions: ["Urinary Tract Infection"],
  },
  {
    title: "Standard Treatment Workflows of India (STW) - Urticaria and Angioedema",
    publisher: "Indian Council of Medical Research (ICMR)",
    edition_year: "2022",
    url: "https://main.icmr.nic.in/",
    conditions: ["Urticaria"],
  },
];

export default function Sources() {
  const [sources, setSources] = useState(FALLBACK_SOURCES);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    getSources()
      .then((data) => {
        if (!active) return;
        if (data && Array.isArray(data.sources) && data.sources.length > 0) {
          setSources(data.sources);
        }
        setLoading(false);
      })
      .catch(() => {
        if (active) {
          setLoading(false);
        }
      });

    return () => {
      active = false;
    };
  }, []);

  return (
    <div className="page-container">
      <h1 className="triage-meaning" style={{ fontSize: "var(--font-size-2xl)", fontWeight: 700 }}>
        Authoritative Clinical Sources
      </h1>

      <p className="page-intro">
        AIRA draws exclusively from published, peer-reviewed clinical guidelines issued by the Indian Council of Medical Research (ICMR) and the Ministry of Health and Family Welfare (MOHFW), Government of India.
      </p>

      {loading && <p className="status-text">Loading latest source metadata...</p>}

      <div className="sources-directory">
        {sources.map((item, idx) => (
          <section key={idx} className="source-condition-card">
            <h2 className="source-condition-title">{item.title}</h2>
            <p className="source-item" style={{ marginBottom: "0.5rem" }}>
              <span className="source-meta">Publisher: {item.publisher}</span>
              {item.edition_year && <span className="source-meta"> | Edition: {item.edition_year}</span>}
            </p>
            {item.conditions && item.conditions.length > 0 && (
              <p className="source-item" style={{ marginBottom: "0.5rem" }}>
                <span className="source-meta">Supported conditions: {item.conditions.join(", ")}</span>
              </p>
            )}
            {item.url && (
              <p className="source-item" style={{ marginBottom: 0 }}>
                <a
                  href={item.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="source-link"
                >
                  Access official publication
                </a>
              </p>
            )}
          </section>
        ))}
      </div>
    </div>
  );
}
