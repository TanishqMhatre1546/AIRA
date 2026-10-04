import React from "react";
import { Link } from "react-router-dom";
import { landingContent } from "../../content/landing";

export function Hero() {
  const { hero } = landingContent;

  return (
    <section className="landing-hero" aria-labelledby="landing-hero-heading">
      <h1 id="landing-hero-heading" className="landing-hero-title">
        {hero.title}
      </h1>
      <p className="landing-hero-lead">{hero.paragraph}</p>
      <div className="landing-hero-actions">
        <Link to="/app" className="landing-primary-button">
          {hero.checkSymptomsButton}
        </Link>
        <a href="#how-it-works" className="landing-text-link">
          {hero.howItWorksLink}
        </a>
      </div>
      <div className="landing-emergency-callout" role="note">
        {hero.emergencyNotice}
      </div>
    </section>
  );
}

export default Hero;
