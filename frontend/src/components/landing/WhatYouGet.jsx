import React from "react";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faClock, faFileMedical, faEye } from "@fortawesome/free-solid-svg-icons";
import { useT } from "../../i18n/useT";

export function WhatYouGet() {
  const { t } = useT();
  const items = [
    {
      lead: t("landing.whatYouGet.urgencyLead"),
      text: t("landing.whatYouGet.urgencyText"),
      icon: faClock,
    },
    {
      lead: t("landing.whatYouGet.guidelinesLead"),
      text: t("landing.whatYouGet.guidelinesText"),
      icon: faFileMedical,
    },
    {
      lead: t("landing.whatYouGet.signsLead"),
      text: t("landing.whatYouGet.signsText"),
      icon: faEye,
    },
  ];

  return (
    <section id="what-you-get" className="landing-section">
      <span className="section-kicker">{t("landing.whatYouGet.kicker")}</span>
      <h2 className="landing-section-title">{t("landing.whatYouGet.heading")}</h2>
      <div className="what-you-get-grid">
        {items.map((item, index) => (
          <div key={index} className="feature-card">
            <div className="feature-icon-box" aria-hidden="true">
              <FontAwesomeIcon icon={item.icon} />
            </div>
            <p className="feature-text">
              <strong className="feature-lead">{item.lead}</strong> {item.text}
            </p>
          </div>
        ))}
      </div>
    </section>
  );
}

export default WhatYouGet;
