import React, { useState, useEffect } from "react";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import {
  faMagnifyingGlass,
  faXmark,
  faArrowUpRightFromSquare,
} from "@fortawesome/free-solid-svg-icons";
import { getSources } from "../api/client";
import { useT } from "../i18n/useT";

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
  const { t } = useT();
  const [sources, setSources] = useState(FALLBACK_SOURCES);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");

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

  const query = searchQuery.trim().toLowerCase();
  const filteredSources = sources.filter((item) => {
    if (!query) return true;
    const matchTitle = item.title?.toLowerCase().includes(query);
    const matchPublisher = item.publisher?.toLowerCase().includes(query);
    const matchConditions = item.conditions?.some((c) =>
      c.toLowerCase().includes(query)
    );
    return matchTitle || matchPublisher || matchConditions;
  });

  return (
    <div className="page-container sources-page">
      <h1 className="sources-page-title">
        {t("sourcesPage.title")}
      </h1>

      <p className="page-intro">
        {t("sourcesPage.intro")}
      </p>

      <div className="sources-filter-bar">
        <div className="sources-search-wrap">
          <FontAwesomeIcon
            icon={faMagnifyingGlass}
            aria-hidden="true"
            className="sources-search-icon"
          />
          <input
            type="search"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder={t("sourcesPage.searchPlaceholder")}
            className="sources-search-input"
            aria-label={t("sourcesPage.searchAria")}
          />
          {searchQuery && (
            <button
              type="button"
              className="sources-search-clear"
              onClick={() => setSearchQuery("")}
              aria-label={t("sourcesPage.clearSearchAria")}
            >
              <FontAwesomeIcon icon={faXmark} aria-hidden="true" />
            </button>
          )}
        </div>
        <div className="sources-filter-count" aria-live="polite">
          {t("sourcesPage.countShowing", { filtered: filteredSources.length, total: sources.length })}
        </div>
      </div>

      {loading && <p className="status-text">{t("sourcesPage.loading")}</p>}

      <div className="sources-directory">
        {filteredSources.length === 0 ? (
          <div className="no-sources-found">
            <p>{t("sourcesPage.noSourcesFound")}</p>
          </div>
        ) : (
          filteredSources.map((item, idx) => {
            const conditionName =
              item.conditions && item.conditions.length > 0
                ? item.conditions.join(", ")
                : item.title;

            return (
              <details key={idx} className="source-accordion">
                <summary className="source-accordion-summary">
                  <span className="source-condition-heading">{conditionName}</span>
                  <span className="source-publisher-badge">{item.publisher}</span>
                </summary>
                <div className="source-accordion-body">
                  <h3 className="source-doc-title">{item.title}</h3>
                  <p className="source-meta-line">
                    <span className="source-meta-label">{t("sourcesPage.publisherLabel")}</span> {item.publisher}
                    {item.edition_year && (
                      <span> | <span className="source-meta-label">{t("sourcesPage.editionLabel")}</span> {item.edition_year}</span>
                    )}
                  </p>
                  {item.conditions && item.conditions.length > 0 && (
                    <p className="source-meta-line">
                      <span className="source-meta-label">{t("sourcesPage.supportedConditionsLabel")}</span> {item.conditions.join(", ")}
                    </p>
                  )}
                  {item.url && (
                    <div className="source-doc-link-wrap">
                      <a
                        href={item.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="source-link"
                      >
                        <span>{t("sourcesPage.accessPublication")}</span>
                        <FontAwesomeIcon
                          icon={faArrowUpRightFromSquare}
                          aria-hidden="true"
                          className="source-ext-icon"
                        />
                      </a>
                    </div>
                  )}
                </div>
              </details>
            );
          })
        )}
      </div>
    </div>
  );
}
