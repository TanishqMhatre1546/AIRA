import React from "react";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faCompass } from "@fortawesome/free-solid-svg-icons";

export default function StatusLine({ loading, isSlow }) {
  if (!loading) {
    return null;
  }

  return (
    <div
      className="status-line"
      role="status"
      aria-live="polite"
      aria-atomic="true"
    >
      <div className="status-text">
        <FontAwesomeIcon icon={faCompass} aria-hidden="true" className="status-icon" />
        <span>Checking guidelines...</span>
      </div>
      {isSlow && (
        <p className="status-slow-note">
          Waking the server, this may take a few seconds on a cold start.
        </p>
      )}
    </div>
  );
}
