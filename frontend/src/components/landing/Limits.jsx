import React from "react";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faBan } from "@fortawesome/free-solid-svg-icons";
import { useT } from "../../i18n/useT";

export function Limits() {
  const { t } = useT();
  const items = [
    t("landing.limits.item1"),
    t("landing.limits.item2"),
    t("landing.limits.item3"),
    t("landing.limits.item4"),
    t("landing.limits.item5"),
    t("landing.limits.item6"),
  ];

  return (
    <section id="limits" className="landing-section">
      <span className="section-kicker">{t("landing.limits.kicker")}</span>
      <h2 className="landing-section-title">{t("landing.limits.heading")}</h2>
      <div className="limits-card">
        <ul className="limits-grid landing-item-list">
          {items.map((item, index) => (
            <li key={index} className="limit-item landing-item">
              <span className="limit-icon-wrap" aria-hidden="true">
                <FontAwesomeIcon icon={faBan} />
              </span>
              <span>{item}</span>
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}

export default Limits;
