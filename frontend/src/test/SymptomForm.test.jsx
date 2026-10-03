import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import SymptomForm from "../components/SymptomForm";

describe("SymptomForm", () => {
  it("displays live character count and respects 500 character limit", () => {
    let msg = "Headache and fever";
    const setMessage = vi.fn((val) => {
      msg = val;
    });

    render(
      <SymptomForm
        message={msg}
        setMessage={setMessage}
        onSubmit={vi.fn()}
        loading={false}
      />
    );

    expect(screen.getByText("18/500 characters")).toBeInTheDocument();
    const textarea = screen.getByRole("textbox");
    expect(textarea).toHaveValue("Headache and fever");
  });

  it("submits on Enter when message is valid", () => {
    const onSubmit = vi.fn();
    const setMessage = vi.fn();

    render(
      <SymptomForm
        message="Sore throat for 2 days"
        setMessage={setMessage}
        onSubmit={onSubmit}
        loading={false}
      />
    );

    const textarea = screen.getByRole("textbox");
    fireEvent.keyDown(textarea, { key: "Enter", shiftKey: false });

    expect(onSubmit).toHaveBeenCalledWith("Sore throat for 2 days");
  });

  it("does not submit on Shift+Enter (allows newline)", () => {
    const onSubmit = vi.fn();
    const setMessage = vi.fn();

    render(
      <SymptomForm
        message="Sore throat for 2 days"
        setMessage={setMessage}
        onSubmit={onSubmit}
        loading={false}
      />
    );

    const textarea = screen.getByRole("textbox");
    fireEvent.keyDown(textarea, { key: "Enter", shiftKey: true });

    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("disables submit button when message is too short or empty", () => {
    const onSubmit = vi.fn();
    const setMessage = vi.fn();

    const { rerender } = render(
      <SymptomForm
        message=""
        setMessage={setMessage}
        onSubmit={onSubmit}
        loading={false}
      />
    );

    const submitBtn = screen.getByRole("button", { name: /Check guidelines/i });
    expect(submitBtn).toBeDisabled();

    // With 1 character
    rerender(
      <SymptomForm
        message="a"
        setMessage={setMessage}
        onSubmit={onSubmit}
        loading={false}
      />
    );
    expect(submitBtn).toBeDisabled();

    // With 2 characters
    rerender(
      <SymptomForm
        message="hi"
        setMessage={setMessage}
        onSubmit={onSubmit}
        loading={false}
      />
    );
    expect(submitBtn).not.toBeDisabled();
  });
});
