import React, { useEffect } from "react";
import { Routes, Route } from "react-router-dom";
import Header from "./components/Header";
import Footer from "./components/Footer";
import Home from "./routes/Home";
import HowItWorks from "./routes/HowItWorks";
import Sources from "./routes/Sources";
import Privacy from "./routes/Privacy";
import Terms from "./routes/Terms";
import { checkHealth } from "./api/client";

export default function App() {
  useEffect(() => {
    // Wake up backend on initial load
    checkHealth().catch(() => {
      // Ignore background warmup failure
    });
  }, []);

  return (
    <div className="app-layout">
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
