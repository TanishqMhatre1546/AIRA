import React from "react";

export default function Privacy() {
  return (
    <div className="page-container">
      <h1 className="triage-meaning" style={{ fontSize: "var(--font-size-2xl)", fontWeight: 700 }}>
        Privacy Policy
      </h1>

      <p className="page-intro">
        AIRA is built around strict data minimization and privacy by design. We do not track, profile, or retain personal health information.
      </p>

      <section className="step-card">
        <h2 className="step-title">No Query Storage</h2>
        <p className="step-description">
          The text you enter into AIRA is processed transiently in memory to match clinical guidelines and return navigation advice. Your queries are never saved to a database, persistent disk, or user history log.
        </p>
      </section>

      <section className="step-card">
        <h2 className="step-title">No Personal Identification</h2>
        <p className="step-description">
          AIRA does not require user accounts, email addresses, phone numbers, or identity verification. We do not set tracking cookies or use advertising analytics.
        </p>
      </section>

      <section className="step-card">
        <h2 className="step-title">Server Logs and Anonymity</h2>
        <p className="step-description">
          Server operations logs record only operational metadata (such as timestamp, HTTP status code, and random request ID). User symptom inputs are explicitly scrubbed from all system logs.
        </p>
      </section>

      <section className="step-card">
        <h2 className="step-title">Rate Limiting</h2>
        <p className="step-description">
          To protect service availability, incoming IP addresses are tracked solely in a short-lived in-memory sliding window for rate limiting. These IP records are not stored permanently.
        </p>
      </section>
    </div>
  );
}
