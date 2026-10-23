import React, { useEffect, useState } from "react";
import { getMeta } from "../../api/client";
import { useT } from "../../i18n/useT";

export function HowItWorks() {
  const { t } = useT();
  const [reviewSentence, setReviewSentence] = useState(() => t("landing.howItWorks.reviewPending"));

  useEffect(() => {
    let active = true;
    getMeta()
      .then((data) => {
        if (!active) return;
        const review = data?.clinical_review_status || data?.clinical_review;
        if (review && review.reviewed) {
          const reviewer = review.reviewer || "expert";
          const date = review.date || "recent";
          setReviewSentence(`${t("landing.howItWorks.reviewDonePrefix")}${reviewer} on ${date}.`);
        } else {
          setReviewSentence(t("landing.howItWorks.reviewPending"));
        }
      })
      .catch(() => {
        if (active) {
          setReviewSentence(t("landing.howItWorks.reviewPending"));
        }
      });

    return () => {
      active = false;
    };
  }, [t]);

  const steps = [
    t("landing.howItWorks.step1"),
    t("landing.howItWorks.step2"),
    t("landing.howItWorks.step3"),
  ];

  return (
    <section id="how-it-works" className="landing-section">
      <span className="section-kicker">{t("landing.howItWorks.kicker")}</span>
      <h2 className="landing-section-title">{t("landing.howItWorks.heading")}</h2>
      <ol className="how-it-works-grid landing-steps-list">
        {steps.map((step, index) => (
          <li key={index} className="how-step-card landing-step-item">
            <div className="how-step-num" aria-hidden="true">
              0{index + 1}
            </div>
            <p className="how-step-text">{step}</p>
          </li>
        ))}
      </ol>
      <div className="landing-voice-note" data-testid="landing-voice-note">
        {t("landing.howItWorks.voiceFeature")}
      </div>
      <div className="landing-review-status" data-testid="landing-review-status">
        {reviewSentence}
      </div>
    </section>
  );
}

export default HowItWorks;
