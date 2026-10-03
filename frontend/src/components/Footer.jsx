import React, { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { getMeta } from "../api/client";

export default function Footer() {
  const [reviewStatus, setReviewStatus] = useState("Clinical review: pending expert panel");

  useEffect(() => {
    let active = true;
    getMeta()
      .then((data) => {
        if (!active) return;
        if (data && data.clinical_review && data.clinical_review.reviewed) {
          const rev = data.clinical_review;
          setReviewStatus(`Clinically reviewed: yes, by ${rev.reviewer || "expert"} on ${rev.date || "recent"}`);
        } else {
          setReviewStatus("Clinical review: pending expert panel");
        }
      })
      .catch(() => {
        if (active) {
          setReviewStatus("Clinical review: pending expert panel");
        }
      });

    return () => {
      active = false;
    };
  }, []);

  return (
    <footer className="site-footer" role="contentinfo">
      <div className="footer-container">
        <div className="footer-emergency">
          In an emergency call <a href="tel:112">112</a>.
        </div>
        <nav className="footer-links" aria-label="Secondary navigation">
          <Link to="/privacy" className="footer-link">
            Privacy
          </Link>
          <Link to="/terms" className="footer-link">
            Terms
          </Link>
        </nav>
        <div className="footer-status" data-testid="clinical-review-status">
          {reviewStatus}
        </div>
      </div>
    </footer>
  );
}
