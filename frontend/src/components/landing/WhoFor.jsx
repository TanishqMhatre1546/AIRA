import React from "react";
import { useT } from "../../i18n/useT";

export function WhoFor() {
  const { t } = useT();

  return (
    <section id="who-for" className="landing-section">
      <span className="section-kicker">{t("landing.whoFor.kicker")}</span>
      <h2 className="landing-section-title">{t("landing.whoFor.heading")}</h2>
      <p className="landing-text">{t("landing.whoFor.text")}</p>
    </section>
  );
}

export default WhoFor;
