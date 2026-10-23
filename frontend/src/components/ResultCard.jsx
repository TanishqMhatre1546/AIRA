import React from "react";
import { Link } from "react-router-dom";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import {
  faRotateRight,
  faPhone,
  faChild,
  faPrint,
  faVolumeHigh,
  faStop,
} from "@fortawesome/free-solid-svg-icons";

import TriageHeader from "./TriageHeader";
import SectionList from "./SectionList";
import SourceList from "./SourceList";
import EmergencyBanner from "./EmergencyBanner";
import CrisisBanner from "./CrisisBanner";
import RefusalNotice from "./RefusalNotice";
import { useT } from "../i18n/useT";
import { useSpeechSynthesis } from "../hooks/useSpeechSynthesis";
import {
  buildAnswerSpeechText,
  buildNoMatchSpeechText,
  buildOutOfScopeSpeechText,
} from "../utils/speechText";

export default function ResultCard({
  result,
  error,
  userQuery,
  onReset,
  onRetry,
  isStaticExample = false,
}) {
  const { t, language } = useT();
  const { isSupported, hasVoiceForLanguage, isSpeaking, speak, stop } =
    useSpeechSynthesis({ language });

  if (error) {
    return (
      <div className="error-card" role="alert">
        <h3 className="error-heading">{t("resultCard.connectionError")}</h3>
        <p className="error-message">
          {t("resultCard.connectionErrorMessage")}
        </p>
        <div className="emergency-message">
          <a href="tel:112" className="helpline-button">
            <span>
              <FontAwesomeIcon icon={faPhone} aria-hidden="true" /> {t("resultCard.call112Emergency")}
            </span>
            <span className="helpline-name">{t("resultCard.nationalHelpline")}</span>
          </a>
        </div>
        <div className="error-actions">
          {onRetry && (
            <button type="button" className="retry-button" onClick={onRetry}>
              <FontAwesomeIcon icon={faRotateRight} aria-hidden="true" />
              <span>{t("resultCard.tryAgain")}</span>
            </button>
          )}
          {onReset && (
            <button type="button" className="reset-button" onClick={onReset}>
              <span>{t("resultCard.clearQuery")}</span>
            </button>
          )}
        </div>
      </div>
    );
  }

  if (!result) {
    return null;
  }

  const {
    response_type,
    triage_level,
    message,
    helplines,
    sections,
    citations,
    mode,
    disclaimer,
    correction,
  } = result;
  const todayDate = new Date().toISOString().split("T")[0];

  const handlePrint = () => {
    if (typeof window !== "undefined" && window.print) {
      window.print();
    }
  };

  const handleToggleSpeak = () => {
    if (isSpeaking) {
      stop();
    } else {
      let speechText = "";
      if (response_type === "ANSWER") {
        speechText = buildAnswerSpeechText(result, t);
      } else if (response_type === "NO_MATCH") {
        speechText = buildNoMatchSpeechText(t);
      } else if (response_type === "OUT_OF_SCOPE") {
        speechText = buildOutOfScopeSpeechText(message, t);
      }
      if (speechText) {
        speak(speechText);
      }
    }
  };

  const renderContent = () => {
    switch (response_type) {
      case "EMERGENCY":
        return <EmergencyBanner message={message} helplines={helplines} />;

      case "CRISIS":
        return <CrisisBanner message={message} helplines={helplines} />;

      case "REFUSAL":
        return <RefusalNotice message={message} />;

      case "OUT_OF_SCOPE":
        return (
          <div className="refusal-notice" role="region" aria-label="Pediatric and out of scope notice">
            <div className="refusal-header">
              <FontAwesomeIcon icon={faChild} aria-hidden="true" />
              <span>{t("outOfScope.heading")}</span>
            </div>
            <p className="refusal-message">
              {message || t("outOfScope.defaultMessage")}
            </p>
            <p className="refusal-action">{t("outOfScope.emergency")}</p>
          </div>
        );

      case "NO_MATCH":
        return (
          <div className="result-card result-card-unknown" data-testid="triage-result-card" role="region" aria-label={t("triage.unknownLabel")}>
            <TriageHeader level="UNKNOWN" />
            <div className="no-match-content" style={{ marginTop: "1rem" }}>
              <p className="no-match-covered">
                <strong>{t("resultCard.coveredConditionsPrefix")}</strong> Acute Diarrhea, Acute Respiratory Infections, Acute Rhinosinusitis, Bacterial Skin Infections, Dengue Fever, Dermatophytosis (Ringworm), Type 2 Diabetes, Eczema / Dermatitis, Epistaxis (Nosebleed), Headache, Hypertension, Pharyngitis (Sore Throat), Scabies, Urinary Tract Infection, Urticaria / Angioedema.
              </p>
              <p className="refusal-action">
                <Link to="/sources">{t("resultCard.viewSupportedSources")}</Link>
              </p>
            </div>
            {disclaimer && (
              <p className="mode-notice" style={{ marginTop: "1.5rem" }}>
                {disclaimer}
              </p>
            )}
          </div>
        );

      case "ANSWER":
      default: {
        const levelClass = triage_level ? `result-card-${triage_level.toLowerCase()}` : "";
        return (
          <div className={`result-card ${levelClass}`} data-testid="triage-result-card">
            {!isStaticExample && (
              <div className="print-only print-header" data-testid="print-header">
                <h2 className="print-title">{t("resultCard.printTitle")}</h2>
                <div className="print-meta" data-testid="print-date">{t("resultCard.printDate", { date: todayDate })}</div>
                {userQuery && (
                  <div className="print-user-description" data-testid="print-user-description">
                    <strong>{t("resultCard.printUserDescription")}</strong> {userQuery}
                  </div>
                )}
                {result.answers_summary && result.answers_summary.length > 0 && (
                  <div className="print-answers-summary" data-testid="print-answers-summary">
                    <strong>{t("resultCard.printAnswersGiven")}</strong>
                    <ul>
                      {result.answers_summary.map((item, idx) => (
                        <li key={idx}>{item}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}

            {correction && (
              <div className="correction-notice" data-testid="correction-notice" style={{ marginBottom: "0.75rem", fontStyle: "italic", color: "var(--color-text-muted)" }}>
                {t("resultCard.correctionNotice", { phrase: correction })}
              </div>
            )}

            {triage_level && <TriageHeader level={triage_level} />}

            {result.answers_summary && result.answers_summary.length > 0 && (
              <div className="answers-summary-box" data-testid="answers-summary">
                <h4 className="answers-summary-heading">{t("resultCard.basedOnAnswers")}</h4>
                <ul className="answers-summary-list">
                  {result.answers_summary.map((item, idx) => (
                    <li key={idx}>{item}</li>
                  ))}
                </ul>
              </div>
            )}

            <SectionList
              sections={sections}
              mode={mode}
              contentLanguage={result.content_language}
              translationStatus={result.translation_status}
            />
            <SourceList citations={citations} />

            {disclaimer && (
              <p className="mode-notice" style={{ marginTop: "1.5rem" }}>
                {disclaimer}
              </p>
            )}

            {!isStaticExample && (
              <div className="print-only print-disclaimer" data-testid="print-disclaimer">
                {t("resultCard.printDisclaimer")}
              </div>
            )}
          </div>
        );
      }
    }
  };

  const showListenButton = ["ANSWER", "NO_MATCH", "OUT_OF_SCOPE"].includes(response_type);

  return (
    <div className="result-wrapper">
      {!isStaticExample && (
        <div className="reset-area">
          {showListenButton && isSupported && (
            <>
              {hasVoiceForLanguage ? (
                <button
                  type="button"
                  className="read-aloud-button"
                  onClick={handleToggleSpeak}
                  aria-label={isSpeaking ? t("readAloud.stop") : t("readAloud.listenAria")}
                  data-testid="result-listen-button"
                >
                  <FontAwesomeIcon icon={isSpeaking ? faStop : faVolumeHigh} aria-hidden="true" />
                  <span>{isSpeaking ? t("readAloud.stop") : t("readAloud.listen")}</span>
                </button>
              ) : (
                <span className="no-voice-note" data-testid="no-voice-note">
                  {t("readAloud.noVoice")}
                </span>
              )}
            </>
          )}
          {response_type === "ANSWER" && (
            <button
              type="button"
              className="print-button"
              onClick={handlePrint}
              aria-label={t("resultCard.printSummaryAria")}
              data-testid="print-summary-button"
            >
              <FontAwesomeIcon icon={faPrint} aria-hidden="true" />
              <span>{t("resultCard.printSummary")}</span>
            </button>
          )}
          {onReset && (
            <button
              type="button"
              className="reset-button"
              onClick={onReset}
              aria-label={t("resultCard.newQueryAria")}
            >
              <FontAwesomeIcon icon={faRotateRight} aria-hidden="true" />
              <span>{t("resultCard.newQuery")}</span>
            </button>
          )}
        </div>
      )}
      {renderContent()}
    </div>
  );
}
