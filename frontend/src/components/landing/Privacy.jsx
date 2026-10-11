import React from "react";
import { legalContent } from "../../content/legal";
import { useT } from "../../i18n/useT";

export function Privacy() {
  const { t } = useT();

  return (
    <section id="privacy" className="landing-section">
      <span className="section-kicker">{t("landing.privacy.kicker")}</span>
      <h2 className="landing-section-title">{t("landing.privacy.heading")}</h2>

      <p className="landing-text">{t("landing.privacy.statement1")}</p>
      <p className="landing-text">{t("landing.privacy.statement2")}</p>
      <p className="landing-text">
        {t("landing.privacy.statement3Prefix")}{" "}
        <a
          href={legalContent.privacy.googleTermsUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="landing-link"
        >
          {t("landing.privacy.statement3Link")}
        </a>
        . {t("landing.privacy.statement3Suffix")}
      </p>
      <p className="landing-text">{t("landing.privacy.statement4")}</p>
      <p className="landing-text">{t("landing.privacy.statement5")}</p>
      <p className="landing-text">{t("landing.privacy.statement6")}</p>
      <p className="landing-text">{t("landing.privacy.statement7")}</p>

      <div className="landing-legal-date">{t("landing.privacy.lastUpdated")}</div>
    </section>
  );
}

export default Privacy;
