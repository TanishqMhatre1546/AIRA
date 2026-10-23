import React, { useEffect, useRef } from "react";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import {
  faTriangleExclamation,
  faPhone,
  faVolumeHigh,
  faStop,
} from "@fortawesome/free-solid-svg-icons";
import { useT } from "../i18n/useT";
import { useSpeechSynthesis } from "../hooks/useSpeechSynthesis";
import { buildEmergencySpeechText } from "../utils/speechText";

export default function EmergencyBanner({ message, helplines = [] }) {
  const { t, language } = useT();
  const bannerRef = useRef(null);

  const { isSupported, hasVoiceForLanguage, isSpeaking, speak, stop } =
    useSpeechSynthesis({ language });

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

  const handleToggleSpeak = () => {
    if (isSpeaking) {
      stop();
    } else {
      const speechText = buildEmergencySpeechText(message, displayHelplines, t);
      speak(speechText);
    }
  };

  return (
    <div
      ref={bannerRef}
      className="emergency-banner"
      role="alert"
      tabIndex={-1}
      aria-live="assertive"
    >
      <div className="banner-top-row">
        <h2>
          <FontAwesomeIcon icon={faTriangleExclamation} aria-hidden="true" />
          <span>{t("emergencyBanner.heading")}</span>
        </h2>
        {isSupported && hasVoiceForLanguage && (
          <button
            type="button"
            className="banner-listen-button"
            onClick={handleToggleSpeak}
            aria-label={isSpeaking ? t("readAloud.stop") : t("readAloud.listenAria")}
            data-testid="emergency-listen-button"
          >
            <FontAwesomeIcon icon={isSpeaking ? faStop : faVolumeHigh} aria-hidden="true" />
            <span>{isSpeaking ? t("readAloud.stop") : t("readAloud.listen")}</span>
          </button>
        )}
        {isSupported && !hasVoiceForLanguage && (
          <span className="no-voice-note banner-no-voice" data-testid="no-voice-note">
            {t("readAloud.noVoice")}
          </span>
        )}
      </div>
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
