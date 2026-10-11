import React from "react";
import { Link } from "react-router-dom";
import { useT } from "../../i18n/useT";

export function Terms() {
  const { t } = useT();
  const operatorName = import.meta.env.VITE_OPERATOR_NAME;
  const contactEmail = import.meta.env.VITE_CONTACT_EMAIL;

  const statements = [
    t("landing.terms.statement1"),
    t("landing.terms.statement2"),
    t("landing.terms.statement3"),
    t("landing.terms.statement4"),
    t("landing.terms.statement5"),
    t("landing.terms.statement6"),
  ];

  return (
    <section id="terms" className="landing-section">
      <span className="section-kicker">{t("landing.terms.kicker")}</span>
      <h2 className="landing-section-title">{t("landing.terms.heading")}</h2>

      {statements.map((statement, index) => (
        <p key={index} className="landing-text">
          {statement}
        </p>
      ))}

      {operatorName && (
        <p className="landing-text" data-testid="terms-operator">
          {t("landing.terms.operatedBy", { name: operatorName })}
        </p>
      )}

      {contactEmail && (
        <p className="landing-text" data-testid="terms-contact">
          {t("landing.terms.contact", { email: contactEmail })}
        </p>
      )}

      <div className="landing-legal-date">{t("landing.terms.lastUpdated")}</div>

      <p className="landing-text landing-sources-ref">
        <Link to="/sources" className="landing-link">
          {t("landing.terms.sourcesLinkLabel")}
        </Link>
        .
      </p>
    </section>
  );
}

export default Terms;
