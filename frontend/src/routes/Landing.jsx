import React, { useEffect } from "react";
import Hero from "../components/landing/Hero";
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
      <Hero />
      <WhatYouGet />
      <WhoFor />
      <Coverage />
      <HowItWorks />
      <Limits />
      <Privacy />
      <Terms />
    </div>
  );
}

export default Landing;
