import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { MemoryRouter } from "react-router-dom";
import Sources from "../routes/Sources";
import SourceStrip from "../components/landing/SourceStrip";
import SymptomForm from "../components/SymptomForm";
import Assistant from "../routes/Assistant";
import * as client from "../api/client";

vi.mock("../api/client", () => ({
  checkHealth: vi.fn(),
  getMeta: vi.fn(),
  getSources: vi.fn(),
  triageQuery: vi.fn(),
}));

describe("UI Refinement Tests", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    client.checkHealth.mockResolvedValue(true);
    client.getMeta.mockResolvedValue({
      content_verification: "verified",
      clinical_review_status: { reviewed: false },
    });
  });

  describe("Sources Search Filter", () => {
    const mockSources = [
      {
        title: "STW - Acute Diarrhea in Adults",
        publisher: "ICMR",
        edition_year: "2022",
        url: "https://main.icmr.nic.in/",
        conditions: ["Acute Diarrhea"],
      },
      {
        title: "STW - Dengue Fever",
        publisher: "MOHFW",
        edition_year: "2022",
        url: "https://main.icmr.nic.in/",
        conditions: ["Dengue Fever"],
      },
      {
        title: "STW - Epistaxis (Nosebleed)",
        publisher: "ICMR",
        edition_year: "2019",
        url: "https://main.icmr.nic.in/",
        conditions: ["Epistaxis"],
      },
    ];

    it("filters sources by condition name or publisher in real-time", async () => {
      client.getSources.mockResolvedValue({ sources: mockSources });

      render(
        <MemoryRouter>
          <Sources />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getAllByText("Acute Diarrhea").length).toBeGreaterThan(0);
        expect(screen.getAllByText("Dengue Fever").length).toBeGreaterThan(0);
        expect(screen.getAllByText("Epistaxis").length).toBeGreaterThan(0);
      });

      const searchInput = screen.getByRole("searchbox", { name: /Filter clinical sources/i });
      fireEvent.change(searchInput, { target: { value: "dengue" } });

      expect(screen.getAllByText("Dengue Fever").length).toBeGreaterThan(0);
      expect(screen.queryByText("Acute Diarrhea")).not.toBeInTheDocument();
      expect(screen.queryByText("Epistaxis")).not.toBeInTheDocument();
      expect(screen.getByText("Showing 1 of 3 guidelines")).toBeInTheDocument();

      // Clear search
      const clearBtn = screen.getByRole("button", { name: /Clear sources search/i });
      fireEvent.click(clearBtn);

      expect(screen.getAllByText("Acute Diarrhea").length).toBeGreaterThan(0);
      expect(screen.getAllByText("Dengue Fever").length).toBeGreaterThan(0);
      expect(screen.getAllByText("Epistaxis").length).toBeGreaterThan(0);
    });

    it("shows no-match message when query matches nothing", async () => {
      client.getSources.mockResolvedValue({ sources: mockSources });

      render(
        <MemoryRouter>
          <Sources />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getAllByText("Acute Diarrhea").length).toBeGreaterThan(0);
      });

      const searchInput = screen.getByRole("searchbox", { name: /Filter clinical sources/i });
      fireEvent.change(searchInput, { target: { value: "heart attack" } });

      expect(screen.getByText("No clinical guidelines match your search.")).toBeInTheDocument();
      expect(screen.getByText("Showing 0 of 3 guidelines")).toBeInTheDocument();
    });
  });

  describe("SourceStrip Graceful Degradation", () => {
    it("renders unique publishers when API resolves successfully", async () => {
      client.getSources.mockResolvedValue({
        sources: [
          { publisher: "ICMR" },
          { publisher: "MOHFW" },
          { publisher: "ICMR" },
        ],
      });

      render(<SourceStrip />);

      await waitFor(() => {
        expect(screen.getByTestId("source-strip")).toBeInTheDocument();
        expect(screen.getByText("Based on documents from:")).toBeInTheDocument();
        expect(screen.getByText("ICMR, MOHFW")).toBeInTheDocument();
      });
    });

    it("does not render or crash when API rejects", async () => {
      client.getSources.mockRejectedValue(new Error("Network failed"));

      const { container } = render(<SourceStrip />);

      // Wait a tick for promise rejection to handle
      await waitFor(() => {
        expect(container.firstChild).toBeNull();
      });
    });
  });

  describe("SymptomForm Clear Button", () => {
    it("renders clear button when message is not empty and clears on click", () => {
      const setMessage = vi.fn();

      const { rerender } = render(
        <SymptomForm
          message=""
          setMessage={setMessage}
          onSubmit={vi.fn()}
          loading={false}
        />
      );

      expect(screen.queryByRole("button", { name: /Clear symptoms text/i })).not.toBeInTheDocument();

      rerender(
        <SymptomForm
          message="Runny nose"
          setMessage={setMessage}
          onSubmit={vi.fn()}
          loading={false}
        />
      );

      const clearBtn = screen.getByRole("button", { name: /Clear symptoms text/i });
      expect(clearBtn).toBeInTheDocument();

      fireEvent.click(clearBtn);
      expect(setMessage).toHaveBeenCalledWith("");
    });
  });

  describe("Assistant Empty State", () => {
    it("renders empty state card with guidance and emergency callout", () => {
      render(
        <MemoryRouter>
          <Assistant />
        </MemoryRouter>
      );

      expect(screen.getByTestId("empty-result-card")).toBeInTheDocument();
      expect(screen.getByText("Your result will appear here.")).toBeInTheDocument();
      expect(
        screen.getByText("Enter your symptoms to check official Indian clinical guidelines.")
      ).toBeInTheDocument();
    });
  });
});
