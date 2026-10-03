import { useState, useRef, useCallback, useEffect } from "react";
import { triageSymptoms } from "../api/client.js";

export function useTriage() {
  const [state, setState] = useState("idle"); // idle | loading | success | error
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [isSlow, setIsSlow] = useState(false);
  const [lastQuery, setLastQuery] = useState("");

  const abortControllerRef = useRef(null);
  const slowTimerRef = useRef(null);

  const clearTimers = useCallback(() => {
    if (slowTimerRef.current) {
      clearTimeout(slowTimerRef.current);
      slowTimerRef.current = null;
    }
  }, []);

  const reset = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    clearTimers();
    setState("idle");
    setResult(null);
    setError(null);
    setIsSlow(false);
  }, [clearTimers]);

  const checkGuidelines = useCallback(async (message) => {
    if (!message || !message.trim()) return;

    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    clearTimers();

    const controller = new AbortController();
    abortControllerRef.current = controller;

    setLastQuery(message);
    setState("loading");
    setResult(null);
    setError(null);
    setIsSlow(false);

    // After 4 seconds, mark as slow to notify user about cold start
    slowTimerRef.current = setTimeout(() => {
      setIsSlow(true);
    }, 4000);

    try {
      const data = await triageSymptoms(message, controller.signal);
      clearTimers();
      setResult(data);
      setState("success");
      setIsSlow(false);
    } catch (err) {
      if (err.name === "AbortError" || (err.message && err.message.includes("abort"))) {
        return;
      }
      clearTimers();
      setError(err.message || "Could not reach AIRA. If this is an emergency call 112.");
      setState("error");
      setIsSlow(false);
    }
  }, [clearTimers]);

  const retry = useCallback(() => {
    if (lastQuery) {
      checkGuidelines(lastQuery);
    }
  }, [lastQuery, checkGuidelines]);

  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
      clearTimers();
    };
  }, [clearTimers]);

  return {
    state,
    status: state,
    result,
    error,
    isSlow,
    lastQuery,
    checkGuidelines,
    submitQuery: checkGuidelines,
    retry,
    reset,
  };
}
