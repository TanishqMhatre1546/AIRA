import React from "react";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import {
  faBookMedical,
  faCircleCheck,
  faTriangleExclamation,
} from "@fortawesome/free-solid-svg-icons";

export default function SectionList({ sections, mode }) {
  if (!sections) return null;

  const { guidelines_say = [], do_now = [], watch_for = [] } = sections;
  const isExtractive = mode === "extractive";

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
                      aria-label={`Source citation ${cid}`}
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
      {isExtractive && (
        <p className="mode-notice">These are passages copied from the guideline.</p>
      )}

      {guidelines_say.length > 0 && (
        <section className="guideline-section" aria-labelledby="heading-guidelines-say">
          <h3 id="heading-guidelines-say" className="guideline-section-title">
            <FontAwesomeIcon icon={faBookMedical} aria-hidden="true" className="section-title-icon" />
            <span>What the guidelines say</span>
          </h3>
          {renderClaims(guidelines_say)}
        </section>
      )}

      {do_now.length > 0 && (
        <section className="guideline-section" aria-labelledby="heading-do-now">
          <h3 id="heading-do-now" className="guideline-section-title">
            <FontAwesomeIcon icon={faCircleCheck} aria-hidden="true" className="section-title-icon" />
            <span>What to do now</span>
          </h3>
          {renderClaims(do_now)}
        </section>
      )}

      {watch_for.length > 0 && (
        <section className="guideline-section watch-for-section" aria-labelledby="heading-watch-for">
          <h3 id="heading-watch-for" className="guideline-section-title watch-for-title">
            <FontAwesomeIcon icon={faTriangleExclamation} aria-hidden="true" className="section-title-icon" />
            <span>Watch for these signs</span>
          </h3>
          <div className="watch-for-panel">
            {renderClaims(watch_for, true)}
          </div>
        </section>
      )}
    </div>
  );
}
