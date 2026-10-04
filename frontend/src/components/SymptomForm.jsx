import React from "react";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faArrowRight, faXmark } from "@fortawesome/free-solid-svg-icons";

export default function SymptomForm({
  message,
  setMessage,
  onSubmit,
  loading,
}) {
  const trimmed = message.trim();
  const charCount = message.length;
  const isValidLength = trimmed.length >= 2 && trimmed.length <= 500;
  const isNearLimit = charCount >= 450 && charCount < 500;
  const isAtLimit = charCount >= 500;

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

  return (
    <form className="symptom-form" onSubmit={handleSubmit} noValidate>
      <label htmlFor="symptom-input" className="form-label">
        Describe your symptoms or ask about clinical guidelines:
      </label>
      <textarea
        id="symptom-input"
        className="symptom-textarea"
        value={message}
        onChange={handleChange}
        onKeyDown={handleKeyDown}
        placeholder="Example: I have had a runny nose and mild headache for 2 days"
        rows={6}
        maxLength={500}
        disabled={loading}
        aria-describedby="symptom-char-counter symptom-hint"
      />
      <div className="form-footer">
        <div className="form-counter-group">
          <div id="symptom-char-counter" className={counterClass} aria-live="polite">
            {charCount}/500 characters
          </div>
          {charCount > 0 && !loading && (
            <button
              type="button"
              className="clear-button"
              onClick={() => setMessage("")}
              aria-label="Clear symptoms text"
            >
              <FontAwesomeIcon icon={faXmark} aria-hidden="true" />
              <span>Clear</span>
            </button>
          )}
        </div>
        <button
          type="submit"
          className="submit-button"
          disabled={!isValidLength || loading}
          aria-disabled={!isValidLength || loading}
        >
          <span>Check guidelines</span>
          <FontAwesomeIcon icon={faArrowRight} aria-hidden="true" />
        </button>
      </div>
      <span id="symptom-hint" className="sr-only">
        Press Enter to submit or Shift+Enter for a new line. Maximum 500 characters.
      </span>
    </form>
  );
}
