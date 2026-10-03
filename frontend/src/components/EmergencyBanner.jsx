import React, { useEffect, useRef } from "react";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faTriangleExclamation, faPhone } from "@fortawesome/free-solid-svg-icons";

export default function EmergencyBanner({ message, helplines = [] }) {
  const bannerRef = useRef(null);

  useEffect(() => {
    if (bannerRef.current) {
      bannerRef.current.focus();
    }
  }, []);

  const defaultHelplines = [
    { label: "National Emergency Helpline", number: "112" },
    { label: "Ambulance / Emergency Relief", number: "108" },
  ];

  const displayHelplines = helplines.length > 0 ? helplines : defaultHelplines;

  return (
    <div
      ref={bannerRef}
      className="emergency-banner"
      role="alert"
      tabIndex={-1}
      aria-live="assertive"
    >
      <h2>
        <FontAwesomeIcon icon={faTriangleExclamation} aria-hidden="true" />
        <span>Emergency Warning</span>
      </h2>
      <p className="emergency-message">
        {message || "Immediate emergency care is required. Do not wait."}
      </p>
      <div className="helplines-grid">
        {displayHelplines.map((item, idx) => (
          <a
            key={idx}
            href={`tel:${item.number}`}
            className="helpline-button"
            aria-label={`Call ${item.label} at ${item.number}`}
          >
            <span>
              <FontAwesomeIcon icon={faPhone} aria-hidden="true" /> Call {item.number}
            </span>
            <span className="helpline-name">{item.label}</span>
          </a>
        ))}
      </div>
    </div>
  );
}
