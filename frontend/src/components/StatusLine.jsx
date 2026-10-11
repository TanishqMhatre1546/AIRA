import React from "react";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faCompass } from "@fortawesome/free-solid-svg-icons";
import { useT } from "../i18n/useT";

export default function StatusLine({ loading, isSlow }) {
  const { t } = useT();

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
        <span>{t("statusLine.checking")}</span>
      </div>
      {isSlow && (
        <p className="status-slow-note">
          {t("statusLine.slow")}
        </p>
      )}
    </div>
  );
}
