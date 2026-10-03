import React from "react";

const EXAMPLES = [
  "I have had a runny nose and mild headache for 2 days",
  "My left eye is red and has yellow discharge",
  "I have had loose stools 3 times today, no blood",
  "My throat hurts when I swallow and I have a fever",
];

export default function ExamplePrompts({ onSelectPrompt, disabled }) {
  return (
    <section className="example-prompts-section" aria-label="Example symptom questions">
      <div className="examples-heading">Or try an example question:</div>
      <div className="examples-grid">
        {EXAMPLES.map((example, idx) => (
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
