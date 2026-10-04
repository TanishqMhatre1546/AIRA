import React from "react";
import { render, screen, waitFor, act } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { MemoryRouter, useLocation } from "react-router-dom";
import App from "../App";
import Landing from "../routes/Landing";
import Terms from "../components/landing/Terms";
import Coverage from "../components/landing/Coverage";
import HowItWorks from "../components/landing/HowItWorks";
import * as client from "../api/client";

vi.mock("../api/client", () => ({
  checkHealth: vi.fn(),
  getMeta: vi.fn(),
}));

describe("Landing Page", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    client.checkHealth.mockResolvedValue(true);
    client.getMeta.mockResolvedValue({
      content_verification: "verified",
      supported_conditions: ["Acute Diarrhea", "Dengue Fever"],
      clinical_review_status: {
        reviewed: false,
      },
    });
  });

  it("renders exactly one h1 and the sections with expected ids in order", async () => {
    const { container } = render(
      <MemoryRouter initialEntries={["/"]}>
        <Landing />
      </MemoryRouter>
    );

    const h1Elements = container.querySelectorAll("h1");
    expect(h1Elements).toHaveLength(1);
    expect(h1Elements[0]).toHaveTextContent(
      "Check what Indian health guidelines say about your symptoms"
    );

    const expectedSectionIds = [
      "what-you-get",
      "who-for",
      "coverage",
      "how-it-works",
      "limits",
      "privacy",
      "terms",
    ];

    const actualSections = Array.from(container.querySelectorAll("section[id]")).map(
      (sec) => sec.id
    );

    expect(actualSections).toEqual(expectedSectionIds);

    // Ensure async coverage resolves cleanly
    await screen.findByTestId("coverage-list");
  });

  it("redirects legacy routes /how-it-works, /privacy, and /terms to matching hash fragments", async () => {
    function LocationWatcher({ onLocation }) {
      const loc = useLocation();
      React.useEffect(() => {
        onLocation(loc);
      }, [loc, onLocation]);
      return null;
    }

    for (const [legacyPath, expectedHash] of [
      ["/how-it-works", "#how-it-works"],
      ["/privacy", "#privacy"],
      ["/terms", "#terms"],
    ]) {
      let currentLoc;
      render(
        <MemoryRouter initialEntries={[legacyPath]}>
          <LocationWatcher onLocation={(loc) => (currentLoc = loc)} />
          <App />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(currentLoc.pathname).toBe("/");
        expect(currentLoc.hash).toBe(expectedHash);
      });
    }
  });

  it("scrolls to element and focuses heading on hash navigation", async () => {
    const scrollIntoViewMock = vi.fn();
    window.HTMLElement.prototype.scrollIntoView = scrollIntoViewMock;

    render(
      <MemoryRouter initialEntries={["/#what-you-get"]}>
        <Landing />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(scrollIntoViewMock).toHaveBeenCalled();
    });

    const targetHeading = screen.getByRole("heading", { name: "What you get" });
    expect(document.activeElement).toBe(targetHeading);

    await screen.findByTestId("coverage-list");
  });

  it("renders wordmark and Sources only in header on /app, without landing links", async () => {
    render(
      <MemoryRouter initialEntries={["/app"]}>
        <App />
      </MemoryRouter>
    );

    const nav = screen.getByRole("navigation", { name: "Main Navigation" });
    expect(nav).toHaveTextContent("Sources");
    expect(screen.queryByText("How it works")).not.toBeInTheDocument();
    expect(screen.queryByText("Privacy")).not.toBeInTheDocument();
    expect(screen.queryByText("Terms")).not.toBeInTheDocument();
    expect(screen.queryByText("Check symptoms")).not.toBeInTheDocument();

    // Verify footer has Privacy and terms link on /app
    const footerLink = screen.getByRole("link", { name: "Privacy and terms" });
    expect(footerLink).toHaveAttribute("href", "/#privacy");
  });

  it("renders single emergency line and review status on landing page footer without privacy link", async () => {
    render(
      <MemoryRouter initialEntries={["/"]}>
        <App />
      </MemoryRouter>
    );

    expect(screen.getByText(/In an emergency call/)).toBeInTheDocument();
    expect(screen.getByTestId("clinical-review-status")).toHaveTextContent(
      "Clinical review: pending"
    );
    expect(screen.queryByRole("link", { name: "Privacy and terms" })).not.toBeInTheDocument();

    await screen.findByTestId("coverage-list");
  });

  it("renders 404 page with link to home on unknown routes", async () => {
    render(
      <MemoryRouter initialEntries={["/random-route-not-found"]}>
        <App />
      </MemoryRouter>
    );

    expect(screen.getByRole("heading", { name: "Page not found" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Return to the home page" })).toHaveAttribute("href", "/");
  });
});

describe("Landing Coverage and Review Status", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("shows fallback text when conditions API times out after 4 seconds", async () => {
    vi.useFakeTimers();
    // Return promise that never resolves
    client.getMeta.mockReturnValue(new Promise(() => {}));

    render(
      <MemoryRouter>
        <Coverage />
      </MemoryRouter>
    );

    expect(screen.getByTestId("coverage-loading")).toHaveTextContent("Loading the list");

    act(() => {
      vi.advanceTimersByTime(4100);
    });

    expect(screen.getByTestId("coverage-fallback")).toHaveTextContent(
      "The full list is on the Sources page."
    );

    vi.useRealTimers();
  });

  it("displays pending review status when API reports unreviewed", async () => {
    client.getMeta.mockResolvedValue({
      clinical_review_status: { reviewed: false },
    });

    render(
      <MemoryRouter>
        <HowItWorks />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByTestId("landing-review-status")).toHaveTextContent(
        "Clinical review: pending."
      );
    });
  });

  it("displays completed review status with reviewer and date when API reports review", async () => {
    client.getMeta.mockResolvedValue({
      clinical_review_status: {
        reviewed: true,
        reviewer: "Dr. A. Sharma",
        date: "2026-08-15",
      },
    });

    render(
      <MemoryRouter>
        <HowItWorks />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByTestId("landing-review-status")).toHaveTextContent(
        "Clinically reviewed: yes, by Dr. A. Sharma on 2026-08-15."
      );
    });
  });
});

describe("Terms Environment Variable Rendering", () => {
  afterEach(() => {
    vi.unstubAllEnvs();
  });

  it("does not render operator or contact info when env vars are not set", () => {
    render(
      <MemoryRouter>
        <Terms />
      </MemoryRouter>
    );

    expect(screen.queryByTestId("terms-operator")).not.toBeInTheDocument();
    expect(screen.queryByTestId("terms-contact")).not.toBeInTheDocument();
  });

  it("renders operator and contact info only when env vars are set", () => {
    vi.stubEnv("VITE_OPERATOR_NAME", "Public Health Research Initiative");
    vi.stubEnv("VITE_CONTACT_EMAIL", "help@aira-health.in");

    render(
      <MemoryRouter>
        <Terms />
      </MemoryRouter>
    );

    expect(screen.getByTestId("terms-operator")).toHaveTextContent(
      "Operated by Public Health Research Initiative."
    );
    expect(screen.getByTestId("terms-contact")).toHaveTextContent(
      "Contact: help@aira-health.in"
    );
  });
});
