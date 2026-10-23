import React from "react";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import {
  faBookMedical,
  faCircleCheck,
  faTriangleExclamation,
} from "@fortawesome/free-solid-svg-icons";
import { useT } from "../i18n/useT";

export default function SectionList({
  sections,
  mode,
  contentLanguage,
  translationStatus,
}) {
  const { t, lang } = useT();

  if (!sections) return null;

  const { guidelines_say = [], do_now = [], watch_for = [] } = sections;
  const isExtractive = mode === "extractive";
  const isTranslated = contentLanguage && contentLanguage !== "en";
  const isDraft = translationStatus === "unreviewed" || translationStatus === "draft";
  const isUntranslated = lang !== "en" && contentLanguage === "en";

  const renderClaims = (claims, isWatchFor = false) => {
    if (!claims || claims.length === 0) return null;
    return (
      <ul className={`guideline-list ${isWatchFor ? "watch-for-list" : ""}`}>
        {claims.map((claim, idx) => {
          const text = typeof claim === "string" ? claim : claim.text;
          const citationIds = claim.citation_ids || [];

          return (
            <li key={idx} className={`guideline-item ${isWatchFor ? "watch-for-item" : ""}`}>
              {isWatchFor && (
                <FontAwesomeIcon
                  icon={faTriangleExclamation}
                  className="watch-for-icon"
                  aria-hidden="true"
                />
              )}
              <span className="claim-text">{text}</span>
              {citationIds.length > 0 && (
                <span className="citation-ref-group">
                  {citationIds.map((cid) => (
                    <a
                      key={cid}
                      href={`#source-${cid}`}
                      className="citation-ref"
                      aria-label={t("sectionList.sourceCitationAria", { id: cid })}
                    >
                      [{cid}]
                    </a>
                  ))}
                </span>
              )}
            </li>
          );
        })}
      </ul>
    );
  };

  return (
    <div className="guideline-sections">
      {isDraft && (
        <div className="draft-translation-banner" data-testid="draft-translation-badge" style={{ marginBottom: "0.5rem" }}>
          <span className="draft-badge" style={{ display: "inline-block", padding: "0.2rem 0.5rem", borderRadius: "4px", backgroundColor: "#fff3cd", color: "#856404", fontSize: "0.85rem", fontWeight: "600", border: "1px solid #ffeeba" }}>
            {t("sectionList.draftTranslation")}
          </span>
        </div>
      )}

      {isTranslated && (
        <p className="source-language-notice" data-testid="source-language-notice" style={{ fontSize: "0.9rem", color: "var(--color-text-muted)", fontStyle: "italic", marginBottom: "0.5rem" }}>
          {t("sectionList.sourceTextInEnglish")}
        </p>
      )}

      {isUntranslated && (
        <p className="untranslated-notice" data-testid="untranslated-notice" style={{ fontSize: "0.9rem", color: "var(--color-text-muted)", fontStyle: "italic", marginBottom: "0.5rem" }}>
          {t("sectionList.textNotTranslatedYet")}
        </p>
      )}

      {isExtractive && (
        <p className="mode-notice">{t("sectionList.extractiveNotice")}</p>
      )}

      {guidelines_say.length > 0 && (
        <section className="guideline-section" aria-labelledby="heading-guidelines-say">
          <h3 id="heading-guidelines-say" className="guideline-section-title">
            <FontAwesomeIcon icon={faBookMedical} aria-hidden="true" className="section-title-icon" />
            <span>{t("sectionList.guidelinesSay")}</span>
          </h3>
          {renderClaims(guidelines_say)}
        </section>
      )}

      {do_now.length > 0 && (
        <section className="guideline-section" aria-labelledby="heading-do-now">
          <h3 id="heading-do-now" className="guideline-section-title">
            <FontAwesomeIcon icon={faCircleCheck} aria-hidden="true" className="section-title-icon" />
            <span>{t("sectionList.doNow")}</span>
          </h3>
          {renderClaims(do_now)}
        </section>
      )}

      {watch_for.length > 0 && (
        <section className="guideline-section watch-for-section" aria-labelledby="heading-watch-for">
          <h3 id="heading-watch-for" className="guideline-section-title watch-for-title">
            <FontAwesomeIcon icon={faTriangleExclamation} aria-hidden="true" className="section-title-icon" />
            <span>{t("sectionList.watchFor")}</span>
          </h3>
          <div className="watch-for-panel">
            {renderClaims(watch_for, true)}
          </div>
        </section>
      )}
    </div>
  );
}
