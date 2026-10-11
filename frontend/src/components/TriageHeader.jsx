import React from "react";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import {
  faHouseUser,
  faUserDoctor,
  faQuestion,
  faTriangleExclamation,
} from "@fortawesome/free-solid-svg-icons";
import { useT } from "../i18n/useT";

export default function TriageHeader({ level }) {
  const { t } = useT();

  const TRIAGE_CONFIG = {
    SELF_CARE: {
      icon: faHouseUser,
      label: t("triage.selfCareLabel"),
      meaning: t("triage.selfCareMeaning"),
      cssClass: "self_care",
    },
    SEE_DOCTOR: {
      icon: faUserDoctor,
      label: t("triage.seeDoctorLabel"),
      meaning: t("triage.seeDoctorMeaning"),
      cssClass: "see_doctor",
    },
    UNKNOWN: {
      icon: faQuestion,
      label: t("triage.unknownLabel"),
      meaning: t("triage.unknownMeaning"),
      cssClass: "unknown",
    },
    EMERGENCY: {
      icon: faTriangleExclamation,
      label: t("triage.emergencyLabel"),
      meaning: t("triage.emergencyMeaning"),
      cssClass: "emergency",
    },
  };

  const config = TRIAGE_CONFIG[level] || TRIAGE_CONFIG.UNKNOWN;

  return (
    <div className={`triage-header triage-header-${config.cssClass}`}>
      <div className={`triage-badge ${config.cssClass}`} data-testid="triage-badge">
        <FontAwesomeIcon icon={config.icon} aria-hidden="true" />
        <span>{config.label}</span>
      </div>
      <p className="triage-meaning">{config.meaning}</p>
    </div>
  );
}
