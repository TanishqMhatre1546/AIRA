import React from "react";
import { landingContent } from "../../content/landing";

export function WhatYouGet() {
  const { whatYouGet } = landingContent;

  return (
    <section id="what-you-get" className="landing-section">
      <h2 className="landing-section-title">{whatYouGet.heading}</h2>
      <ul className="landing-item-list">
        {whatYouGet.items.map((item, index) => (
          <li key={index} className="landing-item">
            <strong>{item.lead}</strong> {item.text}
          </li>
        ))}
      </ul>
    </section>
  );
}

export default WhatYouGet;
