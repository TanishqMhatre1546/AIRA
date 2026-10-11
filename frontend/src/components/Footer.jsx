import React, { useState, useEffect } from "react";
import { Link, useLocation } from "react-router-dom";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faPhone } from "@fortawesome/free-solid-svg-icons";
import { getMeta } from "../api/client";
import { useT } from "../i18n/useT";

export default function Footer() {
  const { language, t } = useT();
  const [reviewStatus, setReviewStatus] = useState(() => t("footer.clinicalReviewPending"));
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
          setReviewStatus(t("footer.clinicalReviewed", { reviewer, date }));
        } else {
          setReviewStatus(t("footer.clinicalReviewPending"));
        }
      })
      .catch(() => {
        if (active) {
          setReviewStatus(t("footer.clinicalReviewPending"));
        }
      });

    return () => {
      active = false;
    };
  }, [language, t]);

  const emergencyString = t("footer.emergency", { helpline: "112" });
  const emergencyParts = emergencyString.includes("112")
    ? emergencyString.split("112")
    : [emergencyString, ""];

  return (
    <footer className="site-footer" role="contentinfo">
      <div className="footer-container">
        <div className="footer-emergency-strip">
          <FontAwesomeIcon icon={faPhone} className="footer-phone-icon" aria-hidden="true" />
          <span>
            {emergencyParts[0]}
            <a href="tel:112">112</a>
            {emergencyParts[1]}
          </span>
        </div>

        <div className="footer-status" data-testid="clinical-review-status">
          {reviewStatus}
        </div>

        {language !== "en" && (
          <div className="footer-translation-review" data-testid="translation-review-notice">
            {t("translation_review_notice")}
          </div>
        )}

        {!isLanding && (
          <div className="footer-secondary">
            <Link to="/#privacy" className="footer-small-link">
              {t("footer.privacyAndTerms")}
            </Link>
          </div>
        )}
      </div>
    </footer>
  );
}
