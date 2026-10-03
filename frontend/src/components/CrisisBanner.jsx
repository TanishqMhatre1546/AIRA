import React, { useEffect, useRef } from "react";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faHandHoldingHeart, faPhone } from "@fortawesome/free-solid-svg-icons";

export default function CrisisBanner({ message, helplines = [] }) {
  const bannerRef = useRef(null);

  useEffect(() => {
    if (bannerRef.current) {
      bannerRef.current.focus();
    }
  }, []);

  const defaultHelplines = [
    { label: "Tele-MANAS Mental Health Helpline", number: "14416" },
    { label: "National Emergency Helpline", number: "112" },
  ];

  const displayHelplines = helplines.length > 0 ? helplines : defaultHelplines;

  return (
    <div
      ref={bannerRef}
      className="crisis-banner"
      role="alert"
      tabIndex={-1}
      aria-live="assertive"
    >
      <h2>
        <FontAwesomeIcon icon={faHandHoldingHeart} aria-hidden="true" />
        <span>Support Is Available</span>
      </h2>
      <p className="crisis-message">
        {message ||
          "If you or someone you know is in distress or needs mental health support, trained counselors are available 24/7."}
      </p>
      <div className="helplines-grid">
        {displayHelplines.map((item, idx) => (
          <a
            key={idx}
            href={`tel:${item.number}`}
            className="crisis-helpline-button"
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
