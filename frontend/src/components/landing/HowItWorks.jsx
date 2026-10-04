import React, { useEffect, useState } from "react";
import { getMeta } from "../../api/client";
import { landingContent } from "../../content/landing";

export function HowItWorks() {
  const { howItWorks } = landingContent;
  const [reviewSentence, setReviewSentence] = useState(howItWorks.reviewPending);

  useEffect(() => {
    let active = true;
    getMeta()
      .then((data) => {
        if (!active) return;
        const review = data?.clinical_review_status || data?.clinical_review;
        if (review && review.reviewed) {
          const reviewer = review.reviewer || "expert";
          const date = review.date || "recent";
          setReviewSentence(`${howItWorks.reviewDonePrefix}${reviewer} on ${date}.`);
        } else {
          setReviewSentence(howItWorks.reviewPending);
        }
      })
      .catch(() => {
        if (active) {
          setReviewSentence(howItWorks.reviewPending);
        }
      });

    return () => {
      active = false;
    };
  }, [howItWorks.reviewDonePrefix, howItWorks.reviewPending]);

  return (
    <section id="how-it-works" className="landing-section">
      <span className="section-kicker">SAFETY AND PROCESS</span>
      <h2 className="landing-section-title">{howItWorks.heading}</h2>
      <ol className="how-it-works-grid landing-steps-list">
        {howItWorks.steps.map((step, index) => (
          <li key={index} className="how-step-card landing-step-item">
            <div className="how-step-num" aria-hidden="true">
              0{index + 1}
            </div>
            <p className="how-step-text">{step}</p>
          </li>
        ))}
      </ol>
      <div className="landing-review-status" data-testid="landing-review-status">
        {reviewSentence}
      </div>
    </section>
  );
}

export default HowItWorks;
