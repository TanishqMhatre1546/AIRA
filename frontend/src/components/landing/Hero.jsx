import React from "react";
import { Link } from "react-router-dom";
import { sampleEpistaxisResult } from "../../content/landing";
import ResultCard from "../ResultCard";
import { useT } from "../../i18n/useT";

export function Hero() {
  const { t } = useT();

  return (
    <section className="landing-hero" aria-labelledby="landing-hero-heading">
      <div className="landing-hero-grid">
        <div className="landing-hero-content">
          <h1 id="landing-hero-heading" className="landing-hero-title">
            {t("landing.hero.title")}
          </h1>
          <p className="landing-hero-lead">{t("landing.hero.paragraph")}</p>
          <div className="landing-hero-actions">
            <Link to="/app" className="landing-primary-button">
              {t("landing.hero.checkSymptomsButton")}
            </Link>
            <a href="#how-it-works" className="landing-text-link">
              {t("landing.hero.howItWorksLink")}
            </a>
          </div>
          <div className="landing-emergency-callout" role="note">
            {t("landing.hero.emergencyNotice")}
          </div>
        </div>
        <div className="landing-hero-preview" aria-label="Example guideline output">
          <div className="example-badge-bar">
            <span className="example-badge">{t("landing.hero.exampleBadge")}</span>
            <span className="example-caption">{t("landing.hero.exampleCaption")}</span>
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
