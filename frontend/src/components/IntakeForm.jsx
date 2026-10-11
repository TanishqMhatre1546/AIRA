import { useState, useRef, useEffect } from "react";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faCheck } from "@fortawesome/free-solid-svg-icons";
import { useT } from "../i18n/useT";

export function IntakeForm({ questions = [], onSubmit, onSkip, isLoading = false }) {
  const { language, t } = useT();
  const [selectedOptions, setSelectedOptions] = useState({});
  const [extraText, setExtraText] = useState("");
  const headingRef = useRef(null);

  useEffect(() => {
    if (headingRef.current) {
      headingRef.current.focus();
    }
  }, []);

  const getQuestionText = (q) => {
    if (language !== "en") {
      if (q.id === "Q_DURATION") return t("intake.durationQuestion");
      if (q.id === "Q_RISK") return t("intake.riskQuestion");
    }
    return q.text;
  };

  const getOptionLabel = (opt) => {
    if (language !== "en") {
      if (opt.id === "dur_1") return t("intake.dur1");
      if (opt.id === "dur_2") return t("intake.dur2");
      if (opt.id === "dur_6") return t("intake.dur6");
      if (opt.id === "dur_14") return t("intake.dur14");
      if (opt.id === "dur_15") return t("intake.dur15");
      if (opt.id === "risk_pregnant") return t("intake.riskPregnant");
      if (opt.id === "risk_diabetes") return t("intake.riskDiabetes");
      if (opt.id === "risk_immune") return t("intake.riskImmune");
      if (opt.id === "risk_65") return t("intake.risk65");
      if (opt.id === "risk_none" || opt.label.toLowerCase().includes("none")) {
        return t("intake.riskNone");
      }
    }
    return opt.label;
  };

  const handleOptionToggle = (question, option) => {
    const qid = question.id;
    const isSingle = question.type === "single_select";
    const isExclusive = Boolean(
      option.exclusive ||
        option.id.endsWith("_none") ||
        option.label.toLowerCase().includes("none")
    );

    setSelectedOptions((prev) => {
      const current = prev[qid] || [];

      if (isSingle) {
        return { ...prev, [qid]: [option.id] };
      }

      // Multi-select handling
      if (isExclusive) {
        // If clicking exclusive option: select ONLY it
        const alreadySelected = current.includes(option.id);
        return {
          ...prev,
          [qid]: alreadySelected ? [] : [option.id],
        };
      }

      // Regular option: uncheck any exclusive option in this question
      const withoutExclusive = current.filter((id) => {
        const optObj = question.options?.find((o) => o.id === id);
        return !(
          optObj?.exclusive ||
          id.endsWith("_none") ||
          optObj?.label?.toLowerCase().includes("none")
        );
      });

      const exists = withoutExclusive.includes(option.id);
      const next = exists
        ? withoutExclusive.filter((id) => id !== option.id)
        : [...withoutExclusive, option.id];

      return { ...prev, [qid]: next };
    });
  };

  const handleTextChange = (e) => {
    const val = e.target.value;
    if (val.length <= 300) {
      setExtraText(val);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (isLoading) return;

    const answers = Object.entries(selectedOptions)
      .filter(([_, optIds]) => optIds && optIds.length > 0)
      .map(([qid, optIds]) => ({
        question_id: qid,
        selected_option_ids: optIds,
      }));

    onSubmit(answers, extraText.trim() ? extraText.trim() : null);
  };

  const handleSkip = (e) => {
    e.preventDefault();
    if (isLoading) return;
    onSkip();
  };

  const remainingChars = 300 - extraText.length;

  return (
    <div className="intake-form-container" role="region" aria-label="Guided questions">
      <h2 ref={headingRef} tabIndex={-1} className="intake-heading">
        {t("intake.heading")}
      </h2>
      <p className="intake-subheading">
        {t("intake.subheading")}
      </p>

      <form onSubmit={handleSubmit} noValidate>
        {questions.map((q, qIndex) => {
          const isSingle = q.type === "single_select";
          const currentSelected = selectedOptions[q.id] || [];

          return (
            <fieldset key={q.id} className="intake-fieldset">
              <legend className="intake-legend">
                <span className="question-number">
                  {t("intake.questionNumber", { current: qIndex + 1, total: questions.length })}
                </span>{" "}
                {getQuestionText(q)}
              </legend>

              <div className="intake-options-group" role={isSingle ? "radiogroup" : "group"}>
                {q.options?.map((opt) => {
                  const isChecked = currentSelected.includes(opt.id);
                  const inputId = `opt-${q.id}-${opt.id}`;

                  return (
                    <label
                      key={opt.id}
                      htmlFor={inputId}
                      className={`intake-option-label ${isChecked ? "selected" : ""}`}
                    >
                      <input
                        id={inputId}
                        type={isSingle ? "radio" : "checkbox"}
                        name={`question-${q.id}`}
                        value={opt.id}
                        checked={isChecked}
                        onChange={() => handleOptionToggle(q, opt)}
                        className="intake-option-input"
                        disabled={isLoading}
                      />
                      {isChecked && (
                        <FontAwesomeIcon
                          icon={faCheck}
                          aria-hidden="true"
                          className="intake-check-icon"
                        />
                      )}
                      <span className="intake-option-text">{getOptionLabel(opt)}</span>
                    </label>
                  );
                })}
              </div>
            </fieldset>
          );
        })}

        <div className="intake-textarea-block">
          <label htmlFor="intake-extra-text" className="form-label">
            {t("intake.extraTextLabel")}
          </label>
          <textarea
            id="intake-extra-text"
            className="intake-textarea"
            value={extraText}
            onChange={handleTextChange}
            placeholder={t("intake.extraTextPlaceholder")}
            maxLength={300}
            rows={3}
            disabled={isLoading}
          />
          <div className="form-footer">
            <span
              className={`char-counter ${
                remainingChars <= 20 ? "limit-near" : ""
              } ${remainingChars === 0 ? "limit-reached" : ""}`}
              aria-live="polite"
            >
              {t("intake.charsRemaining", { count: remainingChars })}
            </span>
          </div>
        </div>

        <div className="intake-actions">
          <button
            type="submit"
            className="intake-submit-btn"
            disabled={isLoading}
          >
            {isLoading ? t("intake.checkingGuidelines") : t("intake.seeGuidelines")}
          </button>
          <button
            type="button"
            onClick={handleSkip}
            className="intake-skip-btn"
            disabled={isLoading}
          >
            {t("intake.skipAndShowResult")}
          </button>
        </div>
      </form>
    </div>
  );
}
