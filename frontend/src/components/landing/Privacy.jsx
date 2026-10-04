import React from "react";
import { legalContent } from "../../content/legal";

export function Privacy() {
  const { privacy, lastUpdated } = legalContent;

  return (
    <section id="privacy" className="landing-section">
      <h2 className="landing-section-title">{privacy.heading}</h2>

      <p className="landing-text">{privacy.statements[0]}</p>
      <p className="landing-text">{privacy.statements[1]}</p>
      <p className="landing-text">
        {privacy.statements[2]}{" "}
        <a
          href={privacy.googleTermsUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="landing-link"
        >
          {privacy.googleTermsText}
        </a>
        . {privacy.statements[3]}
      </p>
      <p className="landing-text">{privacy.statements[4]}</p>
      <p className="landing-text">{privacy.statements[5]}</p>
      <p className="landing-text">{privacy.statements[6]}</p>
      <p className="landing-text">{privacy.statements[7]}</p>

      <div className="landing-legal-date">Last updated: {lastUpdated}</div>
    </section>
  );
}

export default Privacy;
