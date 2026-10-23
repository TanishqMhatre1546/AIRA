import React from "react";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import {
  faArrowRight,
  faXmark,
  faMicrophone,
  faMicrophoneSlash,
  faCheck,
  faCircleExclamation,
} from "@fortawesome/free-solid-svg-icons";
import { useT } from "../i18n/useT";
import { useSpeechRecognition } from "../hooks/useSpeechRecognition";

export default function SymptomForm({
  message,
  setMessage,
  onSubmit,
  loading,
}) {
  const { t, language } = useT();
  const trimmed = message.trim();
  const charCount = message.length;
  const isValidLength = trimmed.length >= 2 && trimmed.length <= 500;
  const isNearLimit = charCount >= 450 && charCount < 500;
  const isAtLimit = charCount >= 500;

  const {
    isSupported,
    state: voiceState,
    isListening,
    toggleListening,
  } = useSpeechRecognition({
    language,
    message,
    setMessage,
    maxLength: 500,
  });

  const handleChange = (e) => {
    const nextVal = e.target.value;
    if (nextVal.length <= 500) {
      setMessage(nextVal);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (isValidLength && !loading) {
        onSubmit(trimmed);
      }
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (isValidLength && !loading) {
      onSubmit(trimmed);
    }
  };

  let counterClass = "char-counter";
  if (isAtLimit) {
    counterClass += " limit-reached";
  } else if (isNearLimit) {
    counterClass += " limit-near";
  }

  // Determine static feedback info for voice states
  let statusFeedback = null;
  if (voiceState === "listening") {
    statusFeedback = {
      icon: faMicrophone,
      text: t("voiceInput.listening"),
      type: "info",
    };
  } else if (voiceState === "got_it") {
    statusFeedback = {
      icon: faCheck,
      text: t("voiceInput.gotIt"),
      type: "success",
    };
  } else if (voiceState === "no_speech") {
    statusFeedback = {
      icon: faMicrophoneSlash,
      text: t("voiceInput.noSpeech"),
      type: "warning",
    };
  } else if (voiceState === "blocked") {
    statusFeedback = {
      icon: faCircleExclamation,
      text: t("voiceInput.blocked"),
      type: "error",
    };
  }

  return (
    <form className="symptom-form" onSubmit={handleSubmit} noValidate>
      <label htmlFor="symptom-input" className="form-label">
        {t("symptomForm.label")}
      </label>

      <div className="symptom-textarea-wrap">
        <textarea
          id="symptom-input"
          className="symptom-textarea"
          value={message}
          onChange={handleChange}
          onKeyDown={handleKeyDown}
          placeholder={t("symptomForm.placeholder")}
          rows={6}
          maxLength={500}
          disabled={loading}
          aria-describedby="symptom-char-counter symptom-hint"
        />

        {isSupported && (
          <div className="symptom-voice-col">
            <button
              type="button"
              className={`voice-button ${isListening ? "is-listening" : ""}`}
              onClick={toggleListening}
              disabled={loading}
              aria-label={t("voiceInput.speak")}
              data-testid="voice-input-button"
            >
              <FontAwesomeIcon icon={faMicrophone} aria-hidden="true" />
              <span>{isListening ? t("voiceInput.listening") : t("voiceInput.speak")}</span>
            </button>
          </div>
        )}
      </div>

      {statusFeedback && (
        <div
          className={`voice-status-feedback voice-status-${voiceState}`}
          role="status"
          aria-live="polite"
          data-testid="voice-status-feedback"
        >
          <FontAwesomeIcon icon={statusFeedback.icon} aria-hidden="true" />
          <span>{statusFeedback.text}</span>
        </div>
      )}

      {!isSupported && (
        <div
          className="voice-unsupported-note"
          role="status"
          data-testid="voice-unsupported-note"
        >
          {t("voiceInput.notSupported")}
        </div>
      )}

      <div className="form-footer">
        <div className="form-counter-group">
          <div id="symptom-char-counter" className={counterClass} aria-live="polite">
            {t("symptomForm.charCount", { count: charCount })}
          </div>
          {charCount > 0 && !loading && (
            <button
              type="button"
              className="clear-button"
              onClick={() => setMessage("")}
              aria-label={t("symptomForm.clearAria")}
            >
              <FontAwesomeIcon icon={faXmark} aria-hidden="true" />
              <span>{t("symptomForm.clear")}</span>
            </button>
          )}
        </div>
        <button
          type="submit"
          className="submit-button"
          disabled={!isValidLength || loading}
          aria-disabled={!isValidLength || loading}
        >
          <span>{t("symptomForm.submit")}</span>
          <FontAwesomeIcon icon={faArrowRight} aria-hidden="true" />
        </button>
      </div>
      <span id="symptom-hint" className="sr-only">
        {t("symptomForm.submitHint")}
      </span>
    </form>
  );
}
