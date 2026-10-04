import { useState, useRef, useCallback, useEffect } from "react";
import { triageSymptoms } from "../api/client.js";

export function useTriage() {
  const [state, setState] = useState("idle"); // idle | loading | follow_up | success | error
  const [result, setResult] = useState(null);
  const [followUp, setFollowUp] = useState(null);
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
    setFollowUp(null);
    setError(null);
    setIsSlow(false);
  }, [clearTimers]);

  const executeTriage = useCallback(
    async (payload) => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
      clearTimers();

      const controller = new AbortController();
      abortControllerRef.current = controller;

      setState("loading");
      setError(null);
      setIsSlow(false);

      // After 4 seconds, mark as slow to notify user about cold start
      slowTimerRef.current = setTimeout(() => {
        setIsSlow(true);
      }, 4000);

      try {
        const data = await triageSymptoms(payload, controller.signal);
        clearTimers();
        setIsSlow(false);

        if (data.response_type === "FOLLOW_UP") {
          setFollowUp(data);
          setState("follow_up");
        } else {
          setFollowUp(null);
          setResult(data);
          setState("success");
        }
      } catch (err) {
        if (err.name === "AbortError" || (err.message && err.message.includes("abort"))) {
          return;
        }
        clearTimers();
        setError(err.message || "Could not reach AIRA. If this is an emergency call 112.");
        setState("error");
        setIsSlow(false);
      }
    },
    [clearTimers]
  );

  const checkGuidelines = useCallback(
    async (message) => {
      if (!message || !message.trim()) return;
      setLastQuery(message);
      setResult(null);
      setFollowUp(null);
      await executeTriage({ message });
    },
    [executeTriage]
  );

  const submitIntake = useCallback(
    async (answers, extraText) => {
      if (!lastQuery) return;
      await executeTriage({
        message: lastQuery,
        intake: {
          answers: answers || [],
          extra_text: extraText || null,
        },
      });
    },
    [lastQuery, executeTriage]
  );

  const skipIntake = useCallback(async () => {
    if (!lastQuery) return;
    await executeTriage({
      message: lastQuery,
      skip_intake: true,
    });
  }, [lastQuery, executeTriage]);

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
    followUp,
    error,
    isSlow,
    lastQuery,
    checkGuidelines,
    submitQuery: checkGuidelines,
    submitIntake,
    skipIntake,
    retry,
    reset,
  };
}
