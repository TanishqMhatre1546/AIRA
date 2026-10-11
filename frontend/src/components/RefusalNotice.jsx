import React from "react";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faLock } from "@fortawesome/free-solid-svg-icons";
import { useT } from "../i18n/useT";

export default function RefusalNotice({ message }) {
  const { t } = useT();

  return (
    <div className="refusal-notice" role="region" aria-label="Guideline scope notice">
      <div className="refusal-header">
        <FontAwesomeIcon icon={faLock} aria-hidden="true" />
        <span>{t("refusalNotice.heading")}</span>
      </div>
      <p className="refusal-message">
        {message || t("refusalNotice.defaultMessage")}
      </p>
      <p className="refusal-action">{t("refusalNotice.action")}</p>
    </div>
  );
}
