import React from "react";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import {
  faHouseUser,
  faUserDoctor,
  faQuestion,
  faTriangleExclamation,
} from "@fortawesome/free-solid-svg-icons";

const TRIAGE_CONFIG = {
  SELF_CARE: {
    icon: faHouseUser,
    label: "Self care at home",
    meaning: "Guideline suggests home care while monitoring symptoms.",
    cssClass: "self_care",
  },
  SEE_DOCTOR: {
    icon: faUserDoctor,
    label: "See a doctor",
    meaning: "Guideline recommends consultation with a healthcare provider.",
    cssClass: "see_doctor",
  },
  UNKNOWN: {
    icon: faQuestion,
    label: "Guideline navigation",
    meaning: "General information from standard guidelines.",
    cssClass: "unknown",
  },
  EMERGENCY: {
    icon: faTriangleExclamation,
    label: "Emergency symptoms detected",
    meaning: "Immediate in-person emergency care is required.",
    cssClass: "emergency",
  },
};

export default function TriageHeader({ level }) {
  const config = TRIAGE_CONFIG[level] || TRIAGE_CONFIG.UNKNOWN;

  return (
    <div className="triage-header">
      <div className={`triage-badge ${config.cssClass}`} data-testid="triage-badge">
        <FontAwesomeIcon icon={config.icon} aria-hidden="true" />
        <span>{config.label}</span>
      </div>
      <p className="triage-meaning">{config.meaning}</p>
    </div>
  );
}
