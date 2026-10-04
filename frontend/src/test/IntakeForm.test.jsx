import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { IntakeForm } from "../components/IntakeForm";

describe("IntakeForm", () => {
  const mockQuestions = [
    {
      id: "Q_DURATION",
      type: "single_select",
      text: "How long has this been going on?",
      options: [
        { id: "dur_1", label: "Since today" },
        { id: "dur_2", label: "1 to 2 days" },
      ],
    },
    {
      id: "Q_RISK",
      type: "multi_select",
      text: "Do any of these apply to you?",
      options: [
        { id: "risk_pregnant", label: "I am pregnant" },
        { id: "risk_diabetes", label: "I have diabetes" },
        { id: "risk_none", label: "None of these", exclusive: true },
      ],
    },
  ];

  it("renders questions with legends, radios, and checkboxes", () => {
    render(
      <IntakeForm
        questions={mockQuestions}
        onSubmit={vi.fn()}
        onSkip={vi.fn()}
        isLoading={false}
      />
    );

    expect(screen.getByRole("region", { name: "Guided questions" })).toBeInTheDocument();
    expect(screen.getByText("Question 1 of 2:")).toBeInTheDocument();
    expect(screen.getByText("How long has this been going on?")).toBeInTheDocument();
    expect(screen.getByText("Question 2 of 2:")).toBeInTheDocument();
    expect(screen.getByText("Do any of these apply to you?")).toBeInTheDocument();

    const radio1 = screen.getByLabelText("Since today");
    const radio2 = screen.getByLabelText("1 to 2 days");
    expect(radio1).toHaveAttribute("type", "radio");
    expect(radio2).toHaveAttribute("type", "radio");

    const check1 = screen.getByLabelText("I am pregnant");
    const check2 = screen.getByLabelText("I have diabetes");
    const checkNone = screen.getByLabelText("None of these");
    expect(check1).toHaveAttribute("type", "checkbox");
    expect(check2).toHaveAttribute("type", "checkbox");
    expect(checkNone).toHaveAttribute("type", "checkbox");
  });

  it("handles single-select radio button selection", () => {
    render(
      <IntakeForm
        questions={mockQuestions}
        onSubmit={vi.fn()}
        onSkip={vi.fn()}
        isLoading={false}
      />
    );

    const radio1 = screen.getByLabelText("Since today");
    const radio2 = screen.getByLabelText("1 to 2 days");

    expect(radio1).not.toBeChecked();
    expect(radio2).not.toBeChecked();

    fireEvent.click(radio1);
    expect(radio1).toBeChecked();
    expect(radio2).not.toBeChecked();

    fireEvent.click(radio2);
    expect(radio1).not.toBeChecked();
    expect(radio2).toBeChecked();
  });

  it("enforces mutual exclusivity for None of these in multi-select", () => {
    render(
      <IntakeForm
        questions={mockQuestions}
        onSubmit={vi.fn()}
        onSkip={vi.fn()}
        isLoading={false}
      />
    );

    const checkPregnant = screen.getByLabelText("I am pregnant");
    const checkDiabetes = screen.getByLabelText("I have diabetes");
    const checkNone = screen.getByLabelText("None of these");

    // Select regular option
    fireEvent.click(checkPregnant);
    expect(checkPregnant).toBeChecked();
    expect(checkNone).not.toBeChecked();

    // Select another regular option
    fireEvent.click(checkDiabetes);
    expect(checkPregnant).toBeChecked();
    expect(checkDiabetes).toBeChecked();
    expect(checkNone).not.toBeChecked();

    // Now select 'None of these' -> clears previous regular selections
    fireEvent.click(checkNone);
    expect(checkNone).toBeChecked();
    expect(checkPregnant).not.toBeChecked();
    expect(checkDiabetes).not.toBeChecked();

    // Now select a regular option again -> clears 'None of these'
    fireEvent.click(checkPregnant);
    expect(checkPregnant).toBeChecked();
    expect(checkNone).not.toBeChecked();
  });

  it("limits extra text to 300 characters and updates live counter", () => {
    render(
      <IntakeForm
        questions={mockQuestions}
        onSubmit={vi.fn()}
        onSkip={vi.fn()}
        isLoading={false}
      />
    );

    const textarea = screen.getByRole("textbox", { name: /Anything else to add/i });
    expect(screen.getByText("300 characters remaining")).toBeInTheDocument();

    fireEvent.change(textarea, { target: { value: "Mild fever at night" } });
    expect(textarea).toHaveValue("Mild fever at night");
    expect(screen.getByText("281 characters remaining")).toBeInTheDocument();
  });

  it("submits selected answers and extra text when See guidelines is clicked", () => {
    const onSubmit = vi.fn();
    render(
      <IntakeForm
        questions={mockQuestions}
        onSubmit={onSubmit}
        onSkip={vi.fn()}
        isLoading={false}
      />
    );

    fireEvent.click(screen.getByLabelText("Since today"));
    fireEvent.click(screen.getByLabelText("I have diabetes"));
    fireEvent.change(screen.getByRole("textbox", { name: /Anything else to add/i }), {
      target: { value: "Also mild cough" },
    });

    const submitBtn = screen.getByRole("button", { name: "See guidelines" });
    fireEvent.click(submitBtn);

    expect(onSubmit).toHaveBeenCalledTimes(1);
    expect(onSubmit).toHaveBeenCalledWith(
      [
        { question_id: "Q_DURATION", selected_option_ids: ["dur_1"] },
        { question_id: "Q_RISK", selected_option_ids: ["risk_diabetes"] },
      ],
      "Also mild cough"
    );
  });

  it("calls onSkip when Skip and show result is clicked", () => {
    const onSkip = vi.fn();
    const onSubmit = vi.fn();

    render(
      <IntakeForm
        questions={mockQuestions}
        onSubmit={onSubmit}
        onSkip={onSkip}
        isLoading={false}
      />
    );

    const skipBtn = screen.getByRole("button", { name: "Skip and show result" });
    fireEvent.click(skipBtn);

    expect(onSkip).toHaveBeenCalledTimes(1);
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("disables buttons and inputs when isLoading is true", () => {
    render(
      <IntakeForm
        questions={mockQuestions}
        onSubmit={vi.fn()}
        onSkip={vi.fn()}
        isLoading={true}
      />
    );

    expect(screen.getByRole("button", { name: "Checking guidelines..." })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Skip and show result" })).toBeDisabled();
    expect(screen.getByLabelText("Since today")).toBeDisabled();
    expect(screen.getByLabelText("I have diabetes")).toBeDisabled();
    expect(screen.getByRole("textbox", { name: /Anything else to add/i })).toBeDisabled();
  });
});
