import React, { useEffect } from "react";
import Hero from "../components/landing/Hero";
import SourceStrip from "../components/landing/SourceStrip";
import WhatYouGet from "../components/landing/WhatYouGet";
import WhoFor from "../components/landing/WhoFor";
import Coverage from "../components/landing/Coverage";
import HowItWorks from "../components/landing/HowItWorks";
import Limits from "../components/landing/Limits";
import Privacy from "../components/landing/Privacy";
import Terms from "../components/landing/Terms";
import { useHashScroll } from "../hooks/useHashScroll";

export function Landing() {
  useHashScroll();

  useEffect(() => {
    document.title = "AIRA: Clinical guidelines assistant";
  }, []);

  return (
    <div className="landing-container">
      <div className="landing-band landing-band-surface">
        <div className="landing-band-inner">
          <Hero />
        </div>
      </div>

      <div className="landing-band landing-band-tint">
        <div className="landing-band-inner">
          <SourceStrip />
          <WhatYouGet />
        </div>
      </div>

      <div className="landing-band landing-band-surface">
        <div className="landing-band-inner">
          <WhoFor />
          <Coverage />
        </div>
      </div>

      <div className="landing-band landing-band-tint">
        <div className="landing-band-inner">
          <HowItWorks />
        </div>
      </div>

      <div className="landing-band landing-band-surface">
        <div className="landing-band-inner">
          <Limits />
        </div>
      </div>

      <div className="landing-band landing-band-tint">
        <div className="landing-band-inner landing-band-prose">
          <Privacy />
          <Terms />
        </div>
      </div>
    </div>
  );
}

export default Landing;
