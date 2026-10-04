import React from "react";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faBan } from "@fortawesome/free-solid-svg-icons";
import { landingContent } from "../../content/landing";

export function Limits() {
  const { limits } = landingContent;

  return (
    <section id="limits" className="landing-section">
      <span className="section-kicker">SAFETY BOUNDARIES</span>
      <h2 className="landing-section-title">{limits.heading}</h2>
      <div className="limits-card">
        <ul className="limits-grid landing-item-list">
          {limits.items.map((item, index) => (
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
