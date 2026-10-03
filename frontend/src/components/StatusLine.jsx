import React from "react";

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
      <div className="status-text">Checking clinical guidelines...</div>
      {isSlow && (
        <p className="status-slow-note">
          Waking the server, this may take a few seconds on a cold start...
        </p>
      )}
    </div>
  );
}
