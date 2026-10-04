import React, { useState } from "react";
import SymptomForm from "../components/SymptomForm";
import ExamplePrompts from "../components/ExamplePrompts";
import StatusLine from "../components/StatusLine";
import ResultCard from "../components/ResultCard";
import { IntakeForm } from "../components/IntakeForm";
import { useTriage } from "../hooks/useTriage";

export default function Home() {
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
      <p className="purpose-paragraph">
        AIRA tells an adult in India what Indian government health guidelines say about
        everyday symptoms, how urgent the symptoms are, and what to watch for. It is a
        guideline navigator, not a doctor. In an emergency call 112.
      </p>

      {!hasResultOrError && !isFollowUp && (
        <>
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
