import React from "react";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faLock, faVolumeHigh, faStop } from "@fortawesome/free-solid-svg-icons";
import { useT } from "../i18n/useT";
import { useSpeechSynthesis } from "../hooks/useSpeechSynthesis";
import { buildRefusalSpeechText } from "../utils/speechText";

export default function RefusalNotice({ message }) {
  const { t, language } = useT();
  const { isSupported, hasVoiceForLanguage, isSpeaking, speak, stop } =
    useSpeechSynthesis({ language });

  const handleToggleSpeak = () => {
    if (isSpeaking) {
      stop();
    } else {
      const speechText = buildRefusalSpeechText(message, t);
      speak(speechText);
    }
  };

  return (
    <div className="refusal-notice" role="region" aria-label="Guideline scope notice">
      <div className="refusal-top-row">
        <div className="refusal-header">
          <FontAwesomeIcon icon={faLock} aria-hidden="true" />
          <span>{t("refusalNotice.heading")}</span>
        </div>
        {isSupported && hasVoiceForLanguage && (
          <button
            type="button"
            className="notice-listen-button"
            onClick={handleToggleSpeak}
            aria-label={isSpeaking ? t("readAloud.stop") : t("readAloud.listenAria")}
            data-testid="refusal-listen-button"
          >
            <FontAwesomeIcon icon={isSpeaking ? faStop : faVolumeHigh} aria-hidden="true" />
            <span>{isSpeaking ? t("readAloud.stop") : t("readAloud.listen")}</span>
          </button>
        )}
        {isSupported && !hasVoiceForLanguage && (
          <span className="no-voice-note" data-testid="no-voice-note">
            {t("readAloud.noVoice")}
          </span>
        )}
      </div>
      <p className="refusal-message">
        {message || t("refusalNotice.defaultMessage")}
      </p>
      <p className="refusal-action">{t("refusalNotice.action")}</p>
    </div>
  );
}
