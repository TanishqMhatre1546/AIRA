import React, { useState, useEffect } from "react";
import { Link, useLocation } from "react-router-dom";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faPhone } from "@fortawesome/free-solid-svg-icons";
import { getMeta } from "../api/client";

export default function Footer() {
  const [reviewStatus, setReviewStatus] = useState("Clinical review: pending");
  const location = useLocation();
  const isLanding = location.pathname === "/";

  useEffect(() => {
    let active = true;
    getMeta()
      .then((data) => {
        if (!active) return;
        const review = data?.clinical_review_status || data?.clinical_review;
        if (review && review.reviewed) {
          const reviewer = review.reviewer || "expert";
          const date = review.date || "recent";
          setReviewStatus(`Clinically reviewed: yes, by ${reviewer} on ${date}`);
        } else {
          setReviewStatus("Clinical review: pending");
        }
      })
      .catch(() => {
        if (active) {
          setReviewStatus("Clinical review: pending");
        }
      });

    return () => {
      active = false;
    };
  }, []);

  return (
    <footer className="site-footer" role="contentinfo">
      <div className="footer-container">
        <div className="footer-emergency-strip">
          <FontAwesomeIcon icon={faPhone} className="footer-phone-icon" aria-hidden="true" />
          <span>
            In an emergency call <a href="tel:112">112</a>.
          </span>
        </div>

        <div className="footer-status" data-testid="clinical-review-status">
          {reviewStatus}
        </div>

        {!isLanding && (
          <div className="footer-secondary">
            <Link to="/#privacy" className="footer-small-link">
              Privacy and terms
            </Link>
          </div>
        )}
      </div>
    </footer>
  );
}
