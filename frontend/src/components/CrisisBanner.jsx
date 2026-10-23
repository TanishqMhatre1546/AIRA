import React, { useEffect, useRef } from "react";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import {
  faHandHoldingHeart,
  faPhone,
  faVolumeHigh,
  faStop,
} from "@fortawesome/free-solid-svg-icons";
import { useT } from "../i18n/useT";
import { useSpeechSynthesis } from "../hooks/useSpeechSynthesis";
import { buildCrisisSpeechText } from "../utils/speechText";

export default function CrisisBanner({ message, helplines = [] }) {
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
    { label: t("crisisBanner.telemanas"), number: "14416" },
    { label: t("crisisBanner.nationalHelpline"), number: "112" },
  ];

  const displayHelplines = helplines.length > 0 ? helplines : defaultHelplines;

  const handleToggleSpeak = () => {
    if (isSpeaking) {
      stop();
    } else {
      const speechText = buildCrisisSpeechText(message, displayHelplines, t);
      speak(speechText);
    }
  };

  return (
    <div
      ref={bannerRef}
      className="crisis-banner"
      role="alert"
      tabIndex={-1}
      aria-live="assertive"
    >
      <div className="banner-top-row">
        <h2>
          <FontAwesomeIcon icon={faHandHoldingHeart} aria-hidden="true" />
          <span>{t("crisisBanner.heading")}</span>
        </h2>
        {isSupported && hasVoiceForLanguage && (
          <button
            type="button"
            className="banner-listen-button"
            onClick={handleToggleSpeak}
            aria-label={isSpeaking ? t("readAloud.stop") : t("readAloud.listenAria")}
            data-testid="crisis-listen-button"
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
