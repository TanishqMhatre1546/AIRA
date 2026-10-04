import React from "react";
import { landingContent } from "../../content/landing";

export function Limits() {
  const { limits } = landingContent;

  return (
    <section id="limits" className="landing-section">
      <h2 className="landing-section-title">{limits.heading}</h2>
      <ul className="landing-item-list">
        {limits.items.map((item, index) => (
          <li key={index} className="landing-item">
            {item}
          </li>
        ))}
      </ul>
    </section>
  );
}

export default Limits;
