import { useCallback, useEffect, useRef, useState } from "react";

const LANG_LOCALE_MAP = {
  en: "en-IN",
  hi: "hi-IN",
  mr: "mr-IN",
};

export function useSpeechRecognition({ language, message, setMessage, maxLength = 500 }) {
  const isSupported =
    typeof window !== "undefined" &&
    Boolean(window.SpeechRecognition || window.webkitSpeechRecognition);

  const [state, setState] = useState(() => (isSupported ? "ready" : "not_supported"));
  const recognitionRef = useRef(null);
  const baseTextRef = useRef("");
  const hasRecognizedSpeechRef = useRef(false);
  const currentLang = LANG_LOCALE_MAP[language] || "en-IN";

  // Stop listening cleanly
  const stopListening = useCallback(() => {
    if (recognitionRef.current) {
      try {
        recognitionRef.current.stop();
      } catch {
        // Ignore already stopped/aborted
      }
    }
  }, []);

  const startListening = useCallback(() => {
    if (!isSupported) {
      setState("not_supported");
      return;
    }

    // Abort existing instance if any
    if (recognitionRef.current) {
      try {
        recognitionRef.current.abort();
      } catch {
        // Ignore
      }
    }

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const recognition = new SpeechRecognition();

    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = currentLang;

    baseTextRef.current = message || "";
    hasRecognizedSpeechRef.current = false;

    recognition.onstart = () => {
      setState("listening");
    };

    recognition.onresult = (event) => {
      let sessionTranscript = "";
      for (let i = 0; i < event.results.length; i++) {
        sessionTranscript += event.results[i][0].transcript;
      }

      if (sessionTranscript.trim().length > 0) {
        hasRecognizedSpeechRef.current = true;
      }

      const base = baseTextRef.current;
      const combined = base
        ? `${base.trim()} ${sessionTranscript}`.trim()
        : sessionTranscript;

      const clamped = combined.slice(0, maxLength);
      setMessage(clamped);
    };

    recognition.onerror = (event) => {
      if (event.error === "not-allowed" || event.error === "service-not-allowed") {
        setState("blocked");
      } else if (event.error === "no-speech") {
        setState("no_speech");
      } else if (event.error !== "aborted") {
        setState("ready");
      }
    };

    recognition.onend = () => {
      setState((prev) => {
        if (prev === "blocked") return "blocked";
        if (hasRecognizedSpeechRef.current) return "got_it";
        return "no_speech";
      });
      recognitionRef.current = null;
    };

    recognitionRef.current = recognition;

    try {
      recognition.start();
      setState("listening");
    } catch {
      setState("ready");
    }
  }, [isSupported, currentLang, message, maxLength, setMessage]);

  const toggleListening = useCallback(() => {
    if (state === "listening") {
      stopListening();
    } else {
      startListening();
    }
  }, [state, stopListening, startListening]);

  // Handle Escape key to cancel listening
  useEffect(() => {
    if (state !== "listening") return;

    const handleKeyDown = (e) => {
      if (e.key === "Escape") {
        e.preventDefault();
        stopListening();
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => {
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [state, stopListening]);

  // Cancel listening on unmount (leaving page) or language toggle
  useEffect(() => {
    return () => {
      if (recognitionRef.current) {
        try {
          recognitionRef.current.abort();
        } catch {
          // Ignore
        }
        recognitionRef.current = null;
      }
    };
  }, [language]);

  return {
    isSupported,
    state,
    isListening: state === "listening",
    startListening,
    stopListening,
    toggleListening,
    setState,
  };
}
