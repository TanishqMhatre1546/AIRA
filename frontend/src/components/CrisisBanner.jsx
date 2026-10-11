import React, { useEffect, useRef } from "react";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faHandHoldingHeart, faPhone } from "@fortawesome/free-solid-svg-icons";
import { useT } from "../i18n/useT";

export default function CrisisBanner({ message, helplines = [] }) {
  const { t } = useT();
  const bannerRef = useRef(null);

  useEffect(() => {
    if (bannerRef.current) {
      bannerRef.current.focus();
    }
  }, []);

  const defaultHelplines = [
    { label: t("crisisBanner.telemanas"), number: "14416" },
    { label: t("crisisBanner.nationalHelpline"), number: "112" },
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
        <span>{t("crisisBanner.heading")}</span>
      </h2>
      <p className="crisis-message">
        {message || t("crisisBanner.defaultMessage")}
      </p>
      <div className="helplines-grid">
        {displayHelplines.map((item, idx) => (
          <a
            key={idx}
            href={`tel:${item.number}`}
            className="crisis-helpline-button"
            aria-label={t("crisisBanner.callAria", { label: item.label, number: item.number })}
          >
            <span>
              <FontAwesomeIcon icon={faPhone} aria-hidden="true" /> {t("crisisBanner.call", { number: item.number })}
            </span>
            <span className="helpline-name">{item.label}</span>
          </a>
        ))}
      </div>
    </div>
  );
}
