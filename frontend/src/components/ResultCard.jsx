import React from "react";
import { Link } from "react-router-dom";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import {
  faRotateRight,
  faBookMedical,
  faPhone,
  faChild,
  faPrint,
} from "@fortawesome/free-solid-svg-icons";

import TriageHeader from "./TriageHeader";
import SectionList from "./SectionList";
import SourceList from "./SourceList";
import EmergencyBanner from "./EmergencyBanner";
import CrisisBanner from "./CrisisBanner";
import RefusalNotice from "./RefusalNotice";

export default function ResultCard({
  result,
  error,
  userQuery,
  onReset,
  onRetry,
}) {
  if (error) {
    return (
      <div className="error-card" role="alert">
        <h3 className="error-heading">Connection Error</h3>
        <p className="error-message">
          Could not reach AIRA. If this is an emergency call 112.
        </p>
        <div className="emergency-message">
          <a href="tel:112" className="helpline-button">
            <span>
              <FontAwesomeIcon icon={faPhone} aria-hidden="true" /> Call 112 (Emergency)
            </span>
            <span className="helpline-name">National Helpline</span>
          </a>
        </div>
        <div className="error-actions">
          {onRetry && (
            <button type="button" className="retry-button" onClick={onRetry}>
              <FontAwesomeIcon icon={faRotateRight} aria-hidden="true" />
              <span>Try again</span>
            </button>
          )}
          {onReset && (
            <button type="button" className="reset-button" onClick={onReset}>
              <span>Clear query</span>
            </button>
          )}
        </div>
      </div>
    );
  }

  if (!result) {
    return null;
  }

  const { response_type, triage_level, message, helplines, sections, citations, mode, disclaimer } = result;
  const todayDate = new Date().toISOString().split("T")[0];

  const handlePrint = () => {
    if (typeof window !== "undefined" && window.print) {
      window.print();
    }
  };

  const renderContent = () => {
    switch (response_type) {
      case "EMERGENCY":
        return <EmergencyBanner message={message} helplines={helplines} />;

      case "CRISIS":
        return <CrisisBanner message={message} helplines={helplines} />;

      case "REFUSAL":
        return <RefusalNotice message={message} />;

      case "OUT_OF_SCOPE":
        return (
          <div className="refusal-notice" role="region" aria-label="Pediatric and out of scope notice">
            <div className="refusal-header">
              <FontAwesomeIcon icon={faChild} aria-hidden="true" />
              <span>Adult Guidelines Only</span>
            </div>
            <p className="refusal-message">
              {message ||
                "AIRA covers adult primary care guidelines only. For infants, children, or specialized conditions, please consult a pediatrician or doctor immediately."}
            </p>
            <p className="refusal-action">In an emergency call 112.</p>
          </div>
        );

      case "NO_MATCH":
        return (
          <div className="refusal-notice" role="region" aria-label="No matching condition notice">
            <div className="refusal-header">
              <FontAwesomeIcon icon={faBookMedical} aria-hidden="true" />
              <span>Condition Not Covered</span>
            </div>
            <p className="refusal-message">
              {message ||
                "AIRA did not find guidance for these symptoms in its 15 supported clinical guidelines."}
            </p>
            <p className="refusal-action">
              View all <Link to="/sources">15 supported conditions and sources</Link> or consult a doctor.
            </p>
          </div>
        );

      case "ANSWER":
      default:
        return (
          <div className="result-card" data-testid="triage-result-card">
            <div className="print-only print-header" data-testid="print-header">
              <h2 className="print-title">AIRA Clinical Guideline Summary</h2>
              <div className="print-meta" data-testid="print-date">Date: {todayDate}</div>
              {userQuery && (
                <div className="print-user-description" data-testid="print-user-description">
                  <strong>User description:</strong> {userQuery}
                </div>
              )}
              {result.answers_summary && result.answers_summary.length > 0 && (
                <div className="print-answers-summary" data-testid="print-answers-summary">
                  <strong>Answers given:</strong>
                  <ul>
                    {result.answers_summary.map((item, idx) => (
                      <li key={idx}>{item}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>

            {triage_level && <TriageHeader level={triage_level} />}

            {result.answers_summary && result.answers_summary.length > 0 && (
              <div className="answers-summary-box" data-testid="answers-summary">
                <h4 className="answers-summary-heading">Based on your answers:</h4>
                <ul className="answers-summary-list">
                  {result.answers_summary.map((item, idx) => (
                    <li key={idx}>{item}</li>
                  ))}
                </ul>
              </div>
            )}

            <SectionList sections={sections} mode={mode} />
            <SourceList citations={citations} />

            {disclaimer && (
              <p className="mode-notice" style={{ marginTop: "1.5rem" }}>
                {disclaimer}
              </p>
            )}

            <div className="print-only print-disclaimer" data-testid="print-disclaimer">
              This is a summary of public guidelines, not a diagnosis.
            </div>
          </div>
        );
    }
  };

  return (
    <div className="result-wrapper">
      <div className="reset-area">
        {response_type === "ANSWER" && (
          <button
            type="button"
            className="print-button"
            onClick={handlePrint}
            aria-label="Print clinical summary for doctor or health worker"
            data-testid="print-summary-button"
          >
            <FontAwesomeIcon icon={faPrint} aria-hidden="true" />
            <span>Print summary</span>
          </button>
        )}
        <button
          type="button"
          className="reset-button"
          onClick={onReset}
          aria-label="Start a new symptom query"
        >
          <FontAwesomeIcon icon={faRotateRight} aria-hidden="true" />
          <span>New query</span>
        </button>
      </div>
      {renderContent()}
    </div>
  );
}
