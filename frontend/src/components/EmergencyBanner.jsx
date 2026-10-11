import React, { useEffect, useRef } from "react";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faTriangleExclamation, faPhone } from "@fortawesome/free-solid-svg-icons";
import { useT } from "../i18n/useT";

export default function EmergencyBanner({ message, helplines = [] }) {
  const { t } = useT();
  const bannerRef = useRef(null);

  useEffect(() => {
    if (bannerRef.current) {
      bannerRef.current.focus();
    }
  }, []);

  const defaultHelplines = [
    { label: t("emergencyBanner.nationalHelpline"), number: "112" },
    { label: t("emergencyBanner.ambulance"), number: "108" },
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
        <span>{t("emergencyBanner.heading")}</span>
      </h2>
      <p className="emergency-message">
        {message || t("emergencyBanner.defaultMessage")}
      </p>
      <div className="helplines-grid">
        {displayHelplines.map((item, idx) => (
          <a
            key={idx}
            href={`tel:${item.number}`}
            className="helpline-button"
            aria-label={t("emergencyBanner.callAria", { label: item.label, number: item.number })}
          >
            <span>
              <FontAwesomeIcon icon={faPhone} aria-hidden="true" /> {t("emergencyBanner.call", { number: item.number })}
            </span>
            <span className="helpline-name">{item.label}</span>
          </a>
        ))}
      </div>
    </div>
  );
}
