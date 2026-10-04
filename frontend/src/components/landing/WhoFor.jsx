import React from "react";
import { landingContent } from "../../content/landing";

export function WhoFor() {
  const { whoFor } = landingContent;

  return (
    <section id="who-for" className="landing-section">
      <span className="section-kicker">AUDIENCE</span>
      <h2 className="landing-section-title">{whoFor.heading}</h2>
      <p className="landing-text">{whoFor.text}</p>
    </section>
  );
}

export default WhoFor;
