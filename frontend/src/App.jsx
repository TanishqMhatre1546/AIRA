import React, { useEffect, useState } from "react";
import { Routes, Route } from "react-router-dom";
import Header from "./components/Header";
import Footer from "./components/Footer";
import Home from "./routes/Home";
import HowItWorks from "./routes/HowItWorks";
import Sources from "./routes/Sources";
import Privacy from "./routes/Privacy";
import Terms from "./routes/Terms";
import { checkHealth, getMeta } from "./api/client";

export default function App() {
  const [contentVerification, setContentVerification] = useState("verified");

  useEffect(() => {
    // Wake up backend on initial load
    checkHealth().catch(() => {
      // Ignore background warmup failure
    });
    getMeta()
      .then((meta) => {
        if (meta?.content_verification) {
          setContentVerification(meta.content_verification);
        }
      })
      .catch(() => {
        // Ignore metadata fetch error
      });
  }, []);

  return (
    <div className="app-layout">
      {contentVerification === "unverified" && (
        <div className="prototype-banner" role="status" aria-live="polite">
          <div className="container">
            <p className="prototype-banner-text">
              Prototype. The guideline content has not been checked against the source documents yet.
            </p>
          </div>
        </div>
      )}
      <Header />
      <main id="main-content" className="main-content" tabIndex={-1}>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/how-it-works" element={<HowItWorks />} />
          <Route path="/sources" element={<Sources />} />
          <Route path="/privacy" element={<Privacy />} />
          <Route path="/terms" element={<Terms />} />
        </Routes>
      </main>
      <Footer />
    </div>
  );
}
