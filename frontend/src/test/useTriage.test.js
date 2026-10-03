import { renderHook, act } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { useTriage } from "../hooks/useTriage";
import * as client from "../api/client";

describe("useTriage", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.restoreAllMocks();
    vi.useRealTimers();
  });

  it("triggers 4s slow-server timer during long requests", async () => {
    let resolvePromise;
    const pendingPromise = new Promise((res) => {
      resolvePromise = res;
    });

    vi.spyOn(client, "triageSymptoms").mockImplementation(() => pendingPromise);

    const { result } = renderHook(() => useTriage());

    expect(result.current.state).toBe("idle");
    expect(result.current.isSlow).toBe(false);

    act(() => {
      result.current.submitQuery("I have had high fever and chills for 3 days");
    });

    expect(result.current.state).toBe("loading");
    expect(result.current.isSlow).toBe(false);

    // Fast-forward 3.9 seconds -> still not slow
    act(() => {
      vi.advanceTimersByTime(3900);
    });
    expect(result.current.isSlow).toBe(false);

    // Fast-forward another 200ms (total > 4.0s) -> should be marked slow
    act(() => {
      vi.advanceTimersByTime(200);
    });
    expect(result.current.isSlow).toBe(true);

    // Resolve the request
    await act(async () => {
      resolvePromise({
        response_type: "ANSWER",
        triage_level: "SEE_DOCTOR",
        sections: {},
      });
    });

    expect(result.current.state).toBe("success");
    expect(result.current.isSlow).toBe(false);
    expect(result.current.result).toBeDefined();
  });

  it("handles request failure gracefully", async () => {
    vi.spyOn(client, "triageSymptoms").mockRejectedValue(new Error("Server error"));

    const { result } = renderHook(() => useTriage());

    await act(async () => {
      await result.current.submitQuery("My symptoms");
    });

    expect(result.current.state).toBe("error");
    expect(result.current.error).toBe("Server error");
    expect(result.current.isSlow).toBe(false);
  });

  it("resets state properly", async () => {
    const { result } = renderHook(() => useTriage());

    act(() => {
      result.current.reset();
    });

    expect(result.current.state).toBe("idle");
    expect(result.current.result).toBeNull();
    expect(result.current.error).toBeNull();
  });
});
