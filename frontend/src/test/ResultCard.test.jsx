import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, it, expect, vi } from "vitest";
import ResultCard from "../components/ResultCard";

describe("ResultCard", () => {
  it("renders ANSWER variant with triage header, claims, sources, and print summary elements", () => {
    const printSpy = vi.spyOn(window, "print").mockImplementation(() => {});

    const mockAnswer = {
      response_type: "ANSWER",
      triage_level: "SELF_CARE",
      message: "",
      sections: {
        guidelines_say: [{ text: "Maintain oral hydration with fluids.", citation_ids: [1] }],
        do_now: [{ text: "Drink oral rehydration solution frequently.", citation_ids: [1] }],
        watch_for: [{ text: "Watch for signs of severe dehydration or high fever.", citation_ids: [1] }],
      },
      citations: [
        {
          id: 1,
          title: "ICMR STW Acute Diarrhea",
          publisher: "ICMR",
          year: "2022",
          page: 4,
          url: "https://main.icmr.nic.in/",
        },
      ],
      mode: "model",
      disclaimer: "AIRA is not a doctor. In an emergency call 112.",
    };

    render(
      <MemoryRouter>
        <ResultCard
          result={mockAnswer}
          userQuery="I have had loose stools 3 times today, no blood"
          onReset={vi.fn()}
        />
      </MemoryRouter>
    );

    expect(screen.getByTestId("triage-badge")).toHaveTextContent("Self care at home");
    expect(screen.getByText(/Maintain oral hydration with fluids/i)).toBeInTheDocument();
    expect(screen.getByText(/What to do now/i)).toBeInTheDocument();
    expect(screen.getByText(/Watch for these signs/i)).toBeInTheDocument();
    expect(screen.getByText(/ICMR STW Acute Diarrhea/i)).toBeInTheDocument();

    // Verify Print Summary button
    const printBtn = screen.getByTestId("print-summary-button");
    expect(printBtn).toBeInTheDocument();
    expect(printBtn).toHaveTextContent("Print summary");

    fireEvent.click(printBtn);
    expect(printSpy).toHaveBeenCalledTimes(1);

    // Verify Printable Handover Summary elements
    expect(screen.getByTestId("print-header")).toBeInTheDocument();
    expect(screen.getByTestId("print-user-description")).toHaveTextContent(
      "I have had loose stools 3 times today, no blood"
    );
    expect(screen.getByTestId("print-date")).toHaveTextContent(/Date: \d{4}-\d{2}-\d{2}/);
    expect(screen.getByTestId("print-disclaimer")).toHaveTextContent(
      "This is a summary of public guidelines, not a diagnosis."
    );

    // Verify no emergency helplines duplication inside answer card
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();

    printSpy.mockRestore();
  });

  it("does not render print summary button on non-ANSWER results", () => {
    const mockEmergency = {
      response_type: "EMERGENCY",
      message: "Severe chest pain requires urgent emergency care.",
      helplines: [{ label: "National Emergency Helpline", number: "112" }],
    };

    render(
      <MemoryRouter>
        <ResultCard result={mockEmergency} onReset={vi.fn()} />
      </MemoryRouter>
    );

    expect(screen.queryByTestId("print-summary-button")).not.toBeInTheDocument();
  });

  it("renders EMERGENCY variant with alert banner and call 112 link", () => {
    const mockEmergency = {
      response_type: "EMERGENCY",
      message: "Severe chest pain requires urgent emergency care.",
      helplines: [{ label: "National Emergency Helpline", number: "112" }],
    };

    render(
      <MemoryRouter>
        <ResultCard result={mockEmergency} onReset={vi.fn()} />
      </MemoryRouter>
    );

    expect(screen.getByRole("alert")).toBeInTheDocument();
    expect(screen.getByText(/Severe chest pain requires urgent emergency care/i)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Call National Emergency Helpline at 112/i })).toHaveAttribute(
      "href",
      "tel:112"
    );
  });

  it("renders CRISIS variant with Tele-MANAS helpline", () => {
    const mockCrisis = {
      response_type: "CRISIS",
      message: "Support is available 24/7.",
      helplines: [{ label: "Tele-MANAS Helpline", number: "14416" }],
    };

    render(
      <MemoryRouter>
        <ResultCard result={mockCrisis} onReset={vi.fn()} />
      </MemoryRouter>
    );

    expect(screen.getByRole("heading", { name: /Support Is Available/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Call Tele-MANAS Helpline at 14416/i })).toHaveAttribute(
      "href",
      "tel:14416"
    );
  });

  it("renders REFUSAL variant with doctor advice", () => {
    const mockRefusal = {
      response_type: "REFUSAL",
      message: "AIRA cannot recommend prescription drug dosages.",
    };

    render(
      <MemoryRouter>
        <ResultCard result={mockRefusal} onReset={vi.fn()} />
      </MemoryRouter>
    );

    expect(screen.getByText(/Outside Guideline Scope/i)).toBeInTheDocument();
    expect(screen.getByText(/A doctor or pharmacist can answer this/i)).toBeInTheDocument();
  });

  it("renders OUT_OF_SCOPE variant for pediatric questions", () => {
    const mockOutOfScope = {
      response_type: "OUT_OF_SCOPE",
      message: "AIRA covers adult clinical guidelines only.",
    };

    render(
      <MemoryRouter>
        <ResultCard result={mockOutOfScope} onReset={vi.fn()} />
      </MemoryRouter>
    );

    expect(screen.getByText(/Adult Guidelines Only/i)).toBeInTheDocument();
  });

  it("renders NO_MATCH variant linking to /sources", () => {
    const mockNoMatch = {
      response_type: "NO_MATCH",
      message: "No matching guideline found.",
    };

    render(
      <MemoryRouter>
        <ResultCard result={mockNoMatch} onReset={vi.fn()} />
      </MemoryRouter>
    );

    expect(screen.getByText(/Condition Not Covered/i)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /15 supported conditions and sources/i })).toHaveAttribute(
      "href",
      "/sources"
    );
  });

  it("renders ERROR state with 112 helpline and retry button", () => {
    const onRetry = vi.fn();

    render(
      <MemoryRouter>
        <ResultCard error="Network failed" onRetry={onRetry} onReset={vi.fn()} />
      </MemoryRouter>
    );

    expect(screen.getByRole("alert")).toBeInTheDocument();
    expect(screen.getByText(/Could not reach AIRA. If this is an emergency call 112/i)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Call 112 \(Emergency\)/i })).toHaveAttribute(
      "href",
      "tel:112"
    );
  });
});
