import React from "react";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faClock, faFileMedical, faEye } from "@fortawesome/free-solid-svg-icons";
import { landingContent } from "../../content/landing";

export function WhatYouGet() {
  const { whatYouGet } = landingContent;
  const icons = [faClock, faFileMedical, faEye];

  return (
    <section id="what-you-get" className="landing-section">
      <span className="section-kicker">OVERVIEW</span>
      <h2 className="landing-section-title">{whatYouGet.heading}</h2>
      <div className="what-you-get-grid">
        {whatYouGet.items.map((item, index) => (
          <div key={index} className="feature-card">
            <div className="feature-icon-box" aria-hidden="true">
              <FontAwesomeIcon icon={icons[index]} />
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
