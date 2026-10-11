import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import { describe, it, expect, beforeEach, vi } from "vitest";
import { MemoryRouter } from "react-router-dom";
import App from "../App";
import EmergencyBanner from "../components/EmergencyBanner";
import { LanguageProvider, STORAGE_KEY } from "../i18n/LanguageContext";
import * as client from "../api/client";

vi.mock("../api/client", () => ({
  checkHealth: vi.fn(),
  getMeta: vi.fn(),
  getSources: vi.fn(),
  triageSymptoms: vi.fn(),
}));

describe("Localization and Raw Key Verification", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
    client.checkHealth.mockResolvedValue(true);
    client.getSources.mockResolvedValue({
      sources: [
        {
          title: "STW - Acute Diarrhea in Adults",
          publisher: "Indian Council of Medical Research (ICMR)",
          edition_year: "2022",
          conditions: ["Acute Diarrhea"],
        },
      ],
    });
    client.getMeta.mockResolvedValue({
      content_verification: "verified",
      supported_conditions: ["Acute Diarrhea", "Dengue Fever"],
      clinical_review_status: { reviewed: false },
    });
  });

  const routes = ["/", "/app", "/sources", "/not-a-real-page-404"];
  const languages = ["en", "hi", "mr"];

  // Helper regex to detect raw i18n dot-notation keys (e.g. "landing.hero.title" or "triage.selfCareLabel")
  const rawKeyRegex = /\b[a-z]+(\.[a-z_0-9]+){1,3}\b/;

  languages.forEach((lang) => {
    routes.forEach((route) => {
      it(`renders route ${route} in language "${lang}" without displaying raw keys`, async () => {
        localStorage.setItem(STORAGE_KEY, lang);

        const { container } = render(
          <MemoryRouter initialEntries={[route]}>
            <App />
          </MemoryRouter>
        );

        // Wait for asynchronous data loading on pages like Sources or Landing
        if (route === "/" || route === "/sources") {
          await waitFor(() => {
            expect(container).toBeInTheDocument();
          });
        }

        // Verify HTML lang attribute
        expect(document.documentElement.lang).toBe(lang);

        // Extract all text content and inspect for raw untranslated keys
        const allText = container.textContent || "";
        const matches = allText.match(rawKeyRegex);

        // Disallow untranslated keys
        expect(matches).toBeNull();
      });
    });
  });

  it("renders translation review notice in footer when Hindi or Marathi is selected", async () => {
    // 1. Hindi notice
    localStorage.setItem(STORAGE_KEY, "hi");
    const { unmount } = render(
      <MemoryRouter initialEntries={["/"]}>
        <App />
      </MemoryRouter>
    );

    const hiNotice = screen.getByTestId("translation-review-notice");
    expect(hiNotice).toBeInTheDocument();
    expect(hiNotice).toHaveTextContent("हिंदी अनुवाद की समीक्षा जारी है।");
    unmount();

    // 2. Marathi notice
    localStorage.setItem(STORAGE_KEY, "mr");
    render(
      <MemoryRouter initialEntries={["/"]}>
        <App />
      </MemoryRouter>
    );

    const mrNotice = screen.getByTestId("translation-review-notice");
    expect(mrNotice).toBeInTheDocument();
    expect(mrNotice).toHaveTextContent("मराठी भाषांतराचे पुनरावलोकन सुरू आहे.");
  });

  it("does not render translation review notice in footer when English is selected", () => {
    localStorage.setItem(STORAGE_KEY, "en");
    render(
      <MemoryRouter initialEntries={["/"]}>
        <App />
      </MemoryRouter>
    );

    expect(screen.queryByTestId("translation-review-notice")).not.toBeInTheDocument();
  });
});

describe("Emergency Banner Synchronous Rendering", () => {
  it("renders emergency banner synchronously in English with 112 without network hop", () => {
    localStorage.setItem(STORAGE_KEY, "en");
    render(
      <LanguageProvider>
        <EmergencyBanner message="Severe chest pain detected." />
      </LanguageProvider>
    );

    expect(screen.getByRole("alert")).toBeInTheDocument();
    expect(screen.getByText("Emergency Warning")).toBeInTheDocument();
    expect(screen.getByText("Severe chest pain detected.")).toBeInTheDocument();
    expect(screen.getByText(/112/)).toBeInTheDocument();
    expect(screen.getByText(/108/)).toBeInTheDocument();
  });

  it("renders emergency banner synchronously in Hindi with 112 without network hop", () => {
    localStorage.setItem(STORAGE_KEY, "hi");
    render(
      <LanguageProvider>
        <EmergencyBanner message="सीने में गंभीर दर्द।" />
      </LanguageProvider>
    );

    expect(screen.getByRole("alert")).toBeInTheDocument();
    expect(screen.getByText("आपातकालीन चेतावनी")).toBeInTheDocument();
    expect(screen.getByText("सीने में गंभीर दर्द।")).toBeInTheDocument();
    expect(screen.getByText(/112/)).toBeInTheDocument();
    expect(screen.getByText(/108/)).toBeInTheDocument();
  });

  it("renders emergency banner synchronously in Marathi with 112 without network hop", () => {
    localStorage.setItem(STORAGE_KEY, "mr");
    render(
      <LanguageProvider>
        <EmergencyBanner message="छातीत तीव्र वेदना." />
      </LanguageProvider>
    );

    expect(screen.getByRole("alert")).toBeInTheDocument();
    expect(screen.getByText("आणीबाणीची चेतावणी")).toBeInTheDocument();
    expect(screen.getByText("छातीत तीव्र वेदना.")).toBeInTheDocument();
    expect(screen.getByText(/112/)).toBeInTheDocument();
    expect(screen.getByText(/108/)).toBeInTheDocument();
  });
});
