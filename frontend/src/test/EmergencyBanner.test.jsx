import React from "react";
import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import EmergencyBanner from "../components/EmergencyBanner";

describe("EmergencyBanner", () => {
  it("renders with role='alert' and moves focus to banner", () => {
    render(
      <EmergencyBanner
        message="Crushing chest pain is an emergency. Call 112 immediately."
        helplines={[{ label: "National Emergency", number: "112" }]}
      />
    );

    const banner = screen.getByRole("alert");
    expect(banner).toBeInTheDocument();
    expect(banner).toHaveFocus();
    expect(screen.getByText(/Crushing chest pain is an emergency/i)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Call National Emergency at 112/i })).toHaveAttribute(
      "href",
      "tel:112"
    );
  });
});
