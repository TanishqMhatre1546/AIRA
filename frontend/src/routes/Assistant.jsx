import React, { useEffect, useState } from "react";
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

  return (
    <div className="home-container">
      {!hasResultOrError && !isFollowUp && (
        <>
          <p className="assistant-lead">
            AIRA shows what Indian health guidelines say. It does not diagnose or give medicine doses.
          </p>

          <SymptomForm
            message={message}
            setMessage={setMessage}
            onSubmit={submitQuery}
            loading={isLoading}
          />

          <StatusLine loading={isLoading} isSlow={isSlow} />

          {!isLoading && (
            <ExamplePrompts
              onSelectPrompt={handleSelectPrompt}
              disabled={isLoading}
            />
          )}
        </>
      )}

      {isFollowUp && (
        <>
          <IntakeForm
            questions={followUp.questions}
            onSubmit={submitIntake}
            onSkip={skipIntake}
            isLoading={isLoading}
          />
          {isLoading && <StatusLine loading={isLoading} isSlow={isSlow} />}
        </>
      )}

      {isLoading && hasResultOrError && (
        <StatusLine loading={isLoading} isSlow={isSlow} />
      )}

      {hasResultOrError && (
        <ResultCard
          result={result}
          error={error}
          userQuery={lastQuery || message}
          onReset={handleReset}
          onRetry={handleRetry}
        />
      )}
    </div>
  );
}
