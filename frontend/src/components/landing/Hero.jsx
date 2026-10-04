import React from "react";
import { Link } from "react-router-dom";
import { landingContent, sampleEpistaxisResult } from "../../content/landing";
import ResultCard from "../ResultCard";

export function Hero() {
  const { hero } = landingContent;

  return (
    <section className="landing-hero" aria-labelledby="landing-hero-heading">
      <div className="landing-hero-grid">
        <div className="landing-hero-content">
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
        </div>
        <div className="landing-hero-preview" aria-label="Example guideline output">
          <div className="example-badge-bar">
            <span className="example-badge">Example result</span>
            <span className="example-caption">Illustrative example, not medical advice</span>
          </div>
          <ResultCard
            result={sampleEpistaxisResult}
            isStaticExample={true}
          />
        </div>
      </div>
    </section>
  );
}

export default Hero;
