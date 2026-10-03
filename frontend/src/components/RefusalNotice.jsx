import React from "react";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faLock } from "@fortawesome/free-solid-svg-icons";

export default function RefusalNotice({ message }) {
  return (
    <div className="refusal-notice" role="region" aria-label="Guideline scope notice">
      <div className="refusal-header">
        <FontAwesomeIcon icon={faLock} aria-hidden="true" />
        <span>Outside Guideline Scope</span>
      </div>
      <p className="refusal-message">
        {message ||
          "AIRA does not provide medical diagnoses, medication dosages, or prescription drug advice."}
      </p>
      <p className="refusal-action">A doctor or pharmacist can answer this.</p>
    </div>
  );
}
