import React from "react";
import { Link } from "react-router-dom";
import { legalContent } from "../../content/legal";

export function Terms() {
  const { terms, lastUpdated } = legalContent;
  const operatorName = import.meta.env.VITE_OPERATOR_NAME;
  const contactEmail = import.meta.env.VITE_CONTACT_EMAIL;

  return (
    <section id="terms" className="landing-section">
      <span className="section-kicker">LEGAL TERMS</span>
      <h2 className="landing-section-title">{terms.heading}</h2>

      {terms.statements.map((statement, index) => (
        <p key={index} className="landing-text">
          {statement}
        </p>
      ))}

      {operatorName && (
        <p className="landing-text" data-testid="terms-operator">
          Operated by {operatorName}.
        </p>
      )}

      {contactEmail && (
        <p className="landing-text" data-testid="terms-contact">
          Contact: {contactEmail}
        </p>
      )}

      <div className="landing-legal-date">Last updated: {lastUpdated}</div>

      <p className="landing-text landing-sources-ref">
        <Link to="/sources" className="landing-link">
          {terms.sourcesLinkLabel}
        </Link>
        .
      </p>
    </section>
  );
}

export default Terms;
