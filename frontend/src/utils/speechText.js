export function buildAnswerSpeechText(result, t) {
  if (!result) return "";
  const parts = [];

  // 1. Triage level label and description
  if (result.triage_level) {
    const levelKey = result.triage_level.toLowerCase();
    const labelKeyMap = {
      emergency: "triage.emergencyLabel",
      see_doctor: "triage.seeDoctorLabel",
      self_care: "triage.selfCareLabel",
      unknown: "triage.unknownLabel",
    };
    const descKeyMap = {
      emergency: "triage.emergencyDesc",
      see_doctor: "triage.seeDoctorDesc",
      self_care: "triage.selfCareDesc",
      unknown: "triage.unknownDesc",
    };
    const label = t(labelKeyMap[levelKey] || "triage.unknownLabel");
    const desc = t(descKeyMap[levelKey] || "triage.unknownDesc");
    parts.push(`${label}. ${desc}`);
  }

  // 2. Sections: What guidelines say, What to do now, Watch for these signs
  if (result.sections && Array.isArray(result.sections)) {
    result.sections.forEach((sec) => {
      if (sec.heading) parts.push(sec.heading);
      if (sec.content) parts.push(sec.content);
      if (sec.items && Array.isArray(sec.items)) {
        sec.items.forEach((item) => parts.push(item));
      }
    });
  }

  // 3. Closing line
  parts.push(t("readAloud.disclaimer"));

  return parts.join("\n");
}

export function buildEmergencySpeechText(message, helplines, t) {
  const parts = [];
  parts.push(t("emergencyBanner.heading"));
  parts.push(message || t("emergencyBanner.defaultMessage"));

  const defaultHelplines = [
    { label: t("emergencyBanner.nationalHelpline"), number: "112" },
    { label: t("emergencyBanner.ambulance"), number: "108" },
  ];
  const list = helplines && helplines.length > 0 ? helplines : defaultHelplines;
  list.forEach((item) => {
    parts.push(`${t("emergencyBanner.call", { number: item.number })}. ${item.label}`);
  });

  parts.push(t("readAloud.disclaimer"));
  return parts.join("\n");
}

export function buildCrisisSpeechText(message, helplines, t) {
  const parts = [];
  parts.push(t("crisisBanner.heading"));
  parts.push(message || t("crisisBanner.defaultMessage"));

  const defaultHelplines = [
    { label: t("crisisBanner.telemanas"), number: "14416" },
    { label: t("crisisBanner.nationalHelpline"), number: "112" },
  ];
  const list = helplines && helplines.length > 0 ? helplines : defaultHelplines;
  list.forEach((item) => {
    parts.push(`${t("crisisBanner.call", { number: item.number })}. ${item.label}`);
  });

  parts.push(t("readAloud.disclaimer"));
  return parts.join("\n");
}

export function buildRefusalSpeechText(message, t) {
  const parts = [];
  parts.push(t("refusalNotice.heading"));
  parts.push(message || t("refusalNotice.defaultMessage"));
  parts.push(t("refusalNotice.action"));
  parts.push(t("readAloud.disclaimer"));
  return parts.join("\n");
}

export function buildOutOfScopeSpeechText(message, t) {
  const parts = [];
  parts.push(t("outOfScope.heading"));
  parts.push(message || t("outOfScope.defaultMessage"));
  parts.push(t("outOfScope.emergency"));
  parts.push(t("readAloud.disclaimer"));
  return parts.join("\n");
}

export function buildNoMatchSpeechText(t) {
  const parts = [];
  parts.push(t("triage.unknownLabel"));
  parts.push(t("triage.unknownDesc"));
  parts.push(t("resultCard.viewSupportedSources"));
  parts.push(t("readAloud.disclaimer"));
  return parts.join("\n");
}
