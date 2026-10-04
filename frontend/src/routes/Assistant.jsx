import React, { useEffect, useState } from "react";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faStethoscope } from "@fortawesome/free-solid-svg-icons";
import SymptomForm from "../components/SymptomForm";
import ExamplePrompts from "../components/ExamplePrompts";
import StatusLine from "../components/StatusLine";
import ResultCard from "../components/ResultCard";
import { IntakeForm } from "../components/IntakeForm";
import { useTriage } from "../hooks/useTriage";

export default function Assistant() {
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
    document.title = "AIRA: Clinical guidelines assistant";
  }, []);

  const handleSelectPrompt = (promptText) => {
    setMessage(promptText);
    submitQuery(promptText);
  };

  const handleReset = () => {
    setMessage("");
    reset();
  };

  const handleRetry = () => {
    const q = lastQuery || message.trim();
    if (q.length >= 2) {
      submitQuery(q);
    }
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
              AIRA shows what Indian health guidelines say. It does not diagnose or give medicine doses.
            </p>

            <SymptomForm
              message={message}
              setMessage={setMessage}
              onSubmit={submitQuery}
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
              <h3 className="empty-result-heading">Your result will appear here.</h3>
              <p className="empty-result-hint">
                Enter your symptoms to check official Indian clinical guidelines.
              </p>
              <div className="empty-result-emergency">
                In an emergency call 112.
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
