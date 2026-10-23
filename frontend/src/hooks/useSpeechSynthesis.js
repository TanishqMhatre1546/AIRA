import { useCallback, useEffect, useRef, useState } from "react";

const LANG_LOCALE_MAP = {
  en: "en-IN",
  hi: "hi-IN",
  mr: "mr-IN",
};

export function cleanTextForSpeech(text) {
  if (!text) return "";
  // Strip citations like [1], [2], [10] and normalize spaces around punctuation
  return text
    .replace(/\s*\[\d+\]/g, "")
    .replace(/\s+([.,!?:;।॥])/g, "$1")
    .replace(/\s+/g, " ")
    .trim();
}

export function splitIntoSentences(text) {
  if (!text) return [];
  const cleaned = cleanTextForSpeech(text);
  if (!cleaned) return [];
  // Split on '.', '!', '?', Devanagari danda '।', double danda '॥', or line breaks
  const matches = cleaned.match(/[^.!?।॥\n\r]+[.!?।॥\n\r]*/g);
  if (!matches) {
    return [cleaned];
  }
  return matches.map((s) => s.trim()).filter((s) => s.length > 0);
}

export function findVoiceForLocale(voices, locale) {
  if (!voices || voices.length === 0) return null;
  const target = locale.toLowerCase().replace("_", "-");
  const prefix = target.split("-")[0];

  // 1. Exact match (e.g. en-in)
  let matched = voices.find(
    (v) => v.lang && v.lang.toLowerCase().replace("_", "-") === target
  );
  if (matched) return matched;

  // 2. Exact language match (e.g. 'hi' for 'hi-IN')
  matched = voices.find(
    (v) => v.lang && v.lang.toLowerCase() === prefix
  );
  if (matched) return matched;

  // 3. Fallback to any regional variant of the exact same language
  // (e.g. en-US / en-GB for en-IN, or mr-* for mr-IN)
  matched = voices.find((v) => {
    if (!v.lang) return false;
    const vPrefix = v.lang.toLowerCase().replace("_", "-").split("-")[0];
    return vPrefix === prefix;
  });

  return matched || null;
}

export function useSpeechSynthesis({ language }) {
  const isSupported = typeof window !== "undefined" && Boolean(window.speechSynthesis);
  const [voices, setVoices] = useState([]);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const queueRef = useRef([]);
  const activeUtteranceRef = useRef(null);
  const isCancelledRef = useRef(false);

  const locale = LANG_LOCALE_MAP[language] || "en-IN";

  // Load voices and listen to voiceschanged event
  useEffect(() => {
    if (!isSupported) return;

    const updateVoices = () => {
      const v = window.speechSynthesis.getVoices();
      if (v && v.length > 0) {
        setVoices(v);
      }
    };

    updateVoices();
    if (window.speechSynthesis && "onvoiceschanged" in window.speechSynthesis) {
      window.speechSynthesis.onvoiceschanged = updateVoices;
    }

    return () => {
      if (
        typeof window !== "undefined" &&
        window.speechSynthesis &&
        "onvoiceschanged" in window.speechSynthesis
      ) {
        window.speechSynthesis.onvoiceschanged = null;
      }
    };
  }, [isSupported]);

  const matchedVoice = findVoiceForLocale(voices, locale);
  const hasVoiceForLanguage = Boolean(matchedVoice);

  const stop = useCallback(() => {
    isCancelledRef.current = true;
    queueRef.current = [];
    if (isSupported) {
      try {
        window.speechSynthesis.cancel();
      } catch {
        // Ignore
      }
    }
    setIsSpeaking(false);
    activeUtteranceRef.current = null;
  }, [isSupported]);

  const speak = useCallback(
    (text) => {
      if (!isSupported || !text) return;
      stop();

      const sentences = splitIntoSentences(text);
      if (sentences.length === 0) return;

      isCancelledRef.current = false;
      queueRef.current = [...sentences];
      setIsSpeaking(true);

      const playNextSentence = () => {
        if (isCancelledRef.current || queueRef.current.length === 0) {
          setIsSpeaking(false);
          activeUtteranceRef.current = null;
          return;
        }

        const sentence = queueRef.current.shift();
        const utterance = new SpeechSynthesisUtterance(sentence);
        utterance.lang = locale;
        if (matchedVoice) {
          utterance.voice = matchedVoice;
        }

        utterance.onend = () => {
          if (!isCancelledRef.current) {
            playNextSentence();
          }
        };

        utterance.onerror = (e) => {
          if (e.error !== "canceled" && e.error !== "interrupted") {
            // Unhandled error
          }
          if (!isCancelledRef.current && queueRef.current.length > 0) {
            playNextSentence();
          } else {
            setIsSpeaking(false);
            activeUtteranceRef.current = null;
          }
        };

        activeUtteranceRef.current = utterance;
        try {
          window.speechSynthesis.speak(utterance);
        } catch {
          setIsSpeaking(false);
        }
      };

      playNextSentence();
    },
    [isSupported, locale, matchedVoice, stop]
  );

  // Stop on Escape key
  useEffect(() => {
    if (!isSpeaking) return;

    const handleKeyDown = (e) => {
      if (e.key === "Escape") {
        e.preventDefault();
        stop();
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => {
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [isSpeaking, stop]);

  // Stop on language change or component unmount (leaving page)
  useEffect(() => {
    return () => {
      stop();
    };
  }, [language, stop]);

  return {
    isSupported,
    hasVoiceForLanguage,
    isSpeaking,
    speak,
    stop,
    matchedVoice,
  };
}
