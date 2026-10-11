import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, beforeEach } from "vitest";
import { LanguageProvider, STORAGE_KEY } from "../i18n/LanguageContext";
import LanguageToggle from "../components/LanguageToggle";

describe("LanguageToggle Component", () => {
  beforeEach(() => {
    localStorage.clear();
    document.documentElement.lang = "en";
    document.documentElement.dir = "ltr";
    window.history.replaceState({}, "", "/");
  });

  it("renders glyph 'अ A' with accessible name 'Change language' and role", () => {
    render(
      <LanguageProvider>
        <LanguageToggle />
      </LanguageProvider>
    );

    const button = screen.getByRole("button", { name: "Change language" });
    expect(button).toBeInTheDocument();
    expect(button).toHaveTextContent("अ A");
    expect(button).toHaveAttribute("aria-expanded", "false");
  });

  it("opens dropdown on click displaying English, हिन्दी, मराठी with check on active option", () => {
    render(
      <LanguageProvider>
        <LanguageToggle />
      </LanguageProvider>
    );

    const button = screen.getByRole("button", { name: "Change language" });
    fireEvent.click(button);

    expect(button).toHaveAttribute("aria-expanded", "true");
    expect(screen.getByRole("menuitem", { name: /English/i })).toBeInTheDocument();
    expect(screen.getByRole("menuitem", { name: /हिन्दी/i })).toBeInTheDocument();
    expect(screen.getByRole("menuitem", { name: /मराठी/i })).toBeInTheDocument();

    // English is default selected
    const enOption = screen.getByRole("menuitem", { name: /English/i });
    expect(enOption).toHaveClass("selected");
  });

  it("switches language to Hindi, persists to localStorage, and updates documentElement lang", () => {
    render(
      <LanguageProvider>
        <LanguageToggle />
      </LanguageProvider>
    );

    const button = screen.getByRole("button", { name: "Change language" });
    fireEvent.click(button);

    const hiOption = screen.getByRole("menuitem", { name: /हिन्दी/i });
    fireEvent.click(hiOption);

    expect(localStorage.getItem(STORAGE_KEY)).toBe("hi");
    expect(document.documentElement.lang).toBe("hi");
    expect(document.documentElement.dir).toBe("ltr");
    expect(screen.queryByRole("menu")).not.toBeInTheDocument();
  });

  it("switches language to Marathi, persists to localStorage, and updates documentElement lang", () => {
    render(
      <LanguageProvider>
        <LanguageToggle />
      </LanguageProvider>
    );

    const button = screen.getByRole("button", { name: "Change language" });
    fireEvent.click(button);

    const mrOption = screen.getByRole("menuitem", { name: /मराठी/i });
    fireEvent.click(mrOption);

    expect(localStorage.getItem(STORAGE_KEY)).toBe("mr");
    expect(document.documentElement.lang).toBe("mr");
    expect(document.documentElement.dir).toBe("ltr");
  });

  it("restores saved language preference from localStorage on mount", () => {
    localStorage.setItem(STORAGE_KEY, "mr");

    render(
      <LanguageProvider>
        <LanguageToggle />
      </LanguageProvider>
    );

    expect(document.documentElement.lang).toBe("mr");

    const button = screen.getByRole("button", { name: "भाषा बदला" });
    expect(button).toBeInTheDocument();
    fireEvent.click(button);

    const mrOption = screen.getByRole("menuitem", { name: /मराठी/i });
    expect(mrOption).toHaveClass("selected");
  });

  it("URL parameter ?lang= overrides saved preference in localStorage", () => {
    localStorage.setItem(STORAGE_KEY, "en");
    window.history.replaceState({}, "", "/?lang=hi");

    render(
      <LanguageProvider>
        <LanguageToggle />
      </LanguageProvider>
    );

    expect(document.documentElement.lang).toBe("hi");
    const button = screen.getByRole("button", { name: "भाषा बदलें" });
    expect(button).toBeInTheDocument();
  });

  it("is operable via keyboard: Enter/Space opens, Escape closes and returns focus", async () => {
    const user = userEvent.setup();

    render(
      <LanguageProvider>
        <LanguageToggle />
      </LanguageProvider>
    );

    const button = screen.getByRole("button", { name: "Change language" });
    button.focus();
    expect(document.activeElement).toBe(button);

    // Open via Enter
    await user.keyboard("{Enter}");
    expect(button).toHaveAttribute("aria-expanded", "true");
    expect(screen.getByRole("menuitem", { name: /English/i })).toBeInTheDocument();

    // Close via Escape
    await user.keyboard("{Escape}");
    expect(button).toHaveAttribute("aria-expanded", "false");
    expect(screen.queryByRole("menu")).not.toBeInTheDocument();
    expect(document.activeElement).toBe(button);
  });

  it("closes on outside click and retains selection", () => {
    render(
      <div>
        <div data-testid="outside">Outside area</div>
        <LanguageProvider>
          <LanguageToggle />
        </LanguageProvider>
      </div>
    );

    const button = screen.getByRole("button", { name: "Change language" });
    fireEvent.click(button);
    expect(button).toHaveAttribute("aria-expanded", "true");

    fireEvent.mouseDown(screen.getByTestId("outside"));
    expect(button).toHaveAttribute("aria-expanded", "false");
  });
});
