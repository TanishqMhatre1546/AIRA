import React from "react";
import { Link } from "react-router-dom";

export function NotFound() {
  return (
    <div className="landing-container">
      <section className="landing-section" style={{ borderTop: "none" }}>
        <h1 className="landing-section-title">Page not found</h1>
        <p className="landing-text">
          The requested page does not exist.
        </p>
        <p className="landing-text">
          <Link to="/" className="landing-link">
            Return to the home page
          </Link>
          .
        </p>
      </section>
    </div>
  );
}

export default NotFound;
