import React from "react";

export default function SectionList({ sections, mode }) {
  if (!sections) return null;

  const { guidelines_say = [], do_now = [], watch_for = [] } = sections;
  const isExtractive = mode === "extractive";

  const renderClaims = (claims) => {
    if (!claims || claims.length === 0) return null;
    return (
      <ul className="guideline-list">
        {claims.map((claim, idx) => {
          const text = typeof claim === "string" ? claim : claim.text;
          const citationIds = claim.citation_ids || [];

          return (
            <li key={idx} className="guideline-item">
              <span>{text}</span>
              {citationIds.length > 0 && (
                <span className="citation-ref" aria-label={`Citations ${citationIds.join(", ")}`}>
                  {citationIds.map((cid) => `[${cid}]`).join(" ")}
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
            What the guidelines say
          </h3>
          {renderClaims(guidelines_say)}
        </section>
      )}

      {do_now.length > 0 && (
        <section className="guideline-section" aria-labelledby="heading-do-now">
          <h3 id="heading-do-now" className="guideline-section-title">
            What to do now
          </h3>
          {renderClaims(do_now)}
        </section>
      )}

      {watch_for.length > 0 && (
        <section className="guideline-section" aria-labelledby="heading-watch-for">
          <h3 id="heading-watch-for" className="guideline-section-title">
            Watch for these signs
          </h3>
          {renderClaims(watch_for)}
        </section>
      )}
    </div>
  );
}
