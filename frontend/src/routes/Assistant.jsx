import React, { useEffect, useState } from "react";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faStethoscope } from "@fortawesome/free-solid-svg-icons";
import SymptomForm from "../components/SymptomForm";
import ExamplePrompts from "../components/ExamplePrompts";
import StatusLine from "../components/StatusLine";
import ResultCard from "../components/ResultCard";
import { IntakeForm } from "../components/IntakeForm";
import { useTriage } from "../hooks/useTriage";
import { useT } from "../i18n/useT";

export default function Assistant() {
  const { t } = useT();
  const [message, setMessage] = useState("");
  const {
    status,
    result,
    followUp,
    error,
    isSlow,
    submitQuery,
    submitIntake,
    skipIntake,
    reset,
    lastQuery,
  } = useTriage();

  useEffect(() => {
    document.title = `${t("header.brandName")}: ${t("header.brandTagline")}`;
    return () => {
      if (typeof window !== "undefined" && window.speechSynthesis) {
        window.speechSynthesis.cancel();
      }
    };
  }, [t]);

  const cancelSpeech = () => {
    if (typeof window !== "undefined" && window.speechSynthesis) {
      window.speechSynthesis.cancel();
    }
  };

  const handleSelectPrompt = (promptText) => {
    cancelSpeech();
    setMessage(promptText);
    submitQuery(promptText);
  };

  const handleReset = () => {
    cancelSpeech();
    setMessage("");
    reset();
  };

  const handleRetry = () => {
    cancelSpeech();
    const q = lastQuery || message.trim();
    if (q.length >= 2) {
      submitQuery(q);
    }
  };

  const handleSubmit = (q) => {
    cancelSpeech();
    submitQuery(q);
  };

  const isLoading = status === "loading";
  const isFollowUp = status === "follow_up" && Boolean(followUp);
  const hasResultOrError = Boolean(result || error);
  const isEmergencyOrCrisis =
    Boolean(result) &&
    (result.response_type === "EMERGENCY" || result.response_type === "CRISIS");

  return (
    <div className="home-container assistant-container">
      {isEmergencyOrCrisis && (
        <div className="assistant-banner-top">
          <ResultCard
            result={result}
            error={error}
            userQuery={lastQuery || message}
            onReset={handleReset}
            onRetry={handleRetry}
          />
        </div>
      )}

      <div className="assistant-columns">
        <section className="assistant-input-column" aria-label="Symptom input">
          <div className="assistant-input-card">
            <p className="assistant-lead">
              {t("assistant.lead")}
            </p>

            <SymptomForm
              message={message}
              setMessage={setMessage}
              onSubmit={handleSubmit}
              loading={isLoading}
            />

            {!isLoading && (
              <ExamplePrompts
                onSelectPrompt={handleSelectPrompt}
                disabled={isLoading}
              />
            )}
          </div>
        </section>

        <section className="assistant-result-column" aria-label="Guideline results">
          {!hasResultOrError && !isFollowUp && !isLoading && (
            <div className="result-card empty-result-card" data-testid="empty-result-card">
              <div className="empty-result-icon" aria-hidden="true">
                <FontAwesomeIcon icon={faStethoscope} />
              </div>
              <h3 className="empty-result-heading">{t("assistant.emptyHeading")}</h3>
              <p className="empty-result-hint">
                {t("assistant.emptyHint")}
              </p>
              <div className="empty-result-emergency">
                {t("assistant.emptyEmergency")}
              </div>
            </div>
          )}

          {isLoading && (
            <div className="result-card loading-result-card">
              <StatusLine loading={isLoading} isSlow={isSlow} />
            </div>
          )}

          {isFollowUp && (
            <div className="result-card follow-up-result-card">
              <IntakeForm
                questions={followUp.questions}
                onSubmit={submitIntake}
                onSkip={skipIntake}
                isLoading={isLoading}
              />
              {isLoading && <StatusLine loading={isLoading} isSlow={isSlow} />}
            </div>
          )}

          {hasResultOrError && !isEmergencyOrCrisis && (
            <ResultCard
              result={result}
              error={error}
              userQuery={lastQuery || message}
              onReset={handleReset}
              onRetry={handleRetry}
            />
          )}
        </section>
      </div>
    </div>
  );
}
