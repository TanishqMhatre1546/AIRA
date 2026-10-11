import React from "react";
import { useT } from "../i18n/useT";

export default function ExamplePrompts({ onSelectPrompt, disabled }) {
  const { t } = useT();

  const examples = [
    t("examplePrompts.prompt1"),
    t("examplePrompts.prompt2"),
    t("examplePrompts.prompt3"),
    t("examplePrompts.prompt4"),
  ];

  return (
    <section className="example-prompts-section" aria-label="Example symptom questions">
      <div className="examples-heading">{t("examplePrompts.heading")}</div>
      <div className="examples-grid">
        {examples.map((example, idx) => (
          <button
            key={idx}
            type="button"
            className="example-button"
            onClick={() => onSelectPrompt(example)}
            disabled={disabled}
          >
            {example}
          </button>
        ))}
      </div>
    </section>
  );
}
