import React, { useEffect, useState } from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import Header from "./components/Header";
import Footer from "./components/Footer";
import Landing from "./routes/Landing";
import Assistant from "./routes/Assistant";
import Sources from "./routes/Sources";
import NotFound from "./routes/NotFound";
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
          <Route path="/" element={<Landing />} />
          <Route path="/app" element={<Assistant />} />
          <Route path="/sources" element={<Sources />} />
          <Route
            path="/how-it-works"
            element={<Navigate to="/#how-it-works" replace />}
          />
          <Route
            path="/privacy"
            element={<Navigate to="/#privacy" replace />}
          />
          <Route
            path="/terms"
            element={<Navigate to="/#terms" replace />}
          />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </main>
      <Footer />
    </div>
  );
}
