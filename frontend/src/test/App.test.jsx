import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { MemoryRouter } from "react-router-dom";
import App from "../App";
import * as client from "../api/client";

vi.mock("../api/client", () => ({
  checkHealth: vi.fn(),
  getMeta: vi.fn(),
}));

describe("App Prototype Banner", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    client.checkHealth.mockResolvedValue(true);
  });

  it("shows prototype banner when content_verification is unverified", async () => {
    client.getMeta.mockResolvedValue({
      content_verification: "unverified",
    });

    render(
      <MemoryRouter>
        <App />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(
        screen.getByText(
          "Prototype. The guideline content has not been checked against the source documents yet."
        )
      ).toBeInTheDocument();
    });
  });

  it("does not show prototype banner when content_verification is verified", async () => {
    client.getMeta.mockResolvedValue({
      content_verification: "verified",
    });

    render(
      <MemoryRouter>
        <App />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(
        screen.queryByText(
          "Prototype. The guideline content has not been checked against the source documents yet."
        )
      ).not.toBeInTheDocument();
    });
  });
});
