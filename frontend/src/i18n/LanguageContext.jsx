import React, { createContext, useCallback, useEffect, useMemo, useState } from "react";
import en from "./en.json";
import hi from "./hi.json";
import mr from "./mr.json";

export const SUPPORTED_LANGUAGES = ["en", "hi", "mr"];
export const DEFAULT_LANGUAGE = "en";
export const STORAGE_KEY = "aira_lang";

const translations = { en, hi, mr };

function translateKey(lang, key, params = {}) {
  const keys = key.split(".");
  let val = translations[lang] || translations[DEFAULT_LANGUAGE];
  for (const k of keys) {
    if (val && typeof val === "object" && k in val) {
      val = val[k];
    } else {
      val = undefined;
      break;
    }
  }

  if (val === undefined) {
    val = translations[DEFAULT_LANGUAGE];
    for (const k of keys) {
      if (val && typeof val === "object" && k in val) {
        val = val[k];
      } else {
        val = undefined;
        break;
      }
    }
  }

  if (val === undefined || typeof val !== "string") {
    return key;
  }

  let result = val;
  for (const [paramKey, paramVal] of Object.entries(params)) {
    result = result.replace(new RegExp(`\\{${paramKey}\\}`, "g"), String(paramVal));
  }
  return result;
}

export const LanguageContext = createContext({
  language: DEFAULT_LANGUAGE,
  setLanguage: () => {},
  t: (key, params) => translateKey(DEFAULT_LANGUAGE, key, params),
});

function getInitialLanguage() {
  if (typeof window === "undefined") {
    return DEFAULT_LANGUAGE;
  }
  const params = new URLSearchParams(window.location.search);
  const langQuery = params.get("lang");
  if (langQuery && SUPPORTED_LANGUAGES.includes(langQuery)) {
    return langQuery;
  }
  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved && SUPPORTED_LANGUAGES.includes(saved)) {
      return saved;
    }
  } catch (_e) {
    // localStorage unavailable or restricted
  }
  return DEFAULT_LANGUAGE;
}

export function LanguageProvider({ children }) {
  const [language, setLanguageState] = useState(getInitialLanguage);

  const setLanguage = useCallback((newLang) => {
    if (!SUPPORTED_LANGUAGES.includes(newLang)) return;
    setLanguageState(newLang);
    try {
      localStorage.setItem(STORAGE_KEY, newLang);
    } catch (_e) {
      // Ignore localStorage write error
    }
  }, []);

  useEffect(() => {
    document.documentElement.lang = language;
    document.documentElement.dir = "ltr";

    if (language === "hi" || language === "mr") {
      import("../styles/devanagari.css").catch((err) => {
        if (process.env.NODE_ENV === "development") {
          console.warn("Failed to load Devanagari font styles:", err);
        }
      });
    }
  }, [language]);

  const t = useCallback(
    (key, params = {}) => {
      const keys = key.split(".");
      let val = translations[language];
      for (const k of keys) {
        if (val && typeof val === "object" && k in val) {
          val = val[k];
        } else {
          val = undefined;
          break;
        }
      }

      if (val === undefined) {
        if (process.env.NODE_ENV === "development") {
          console.warn(`[i18n] Missing translation key "${key}" for language "${language}"`);
        }
        val = translations[DEFAULT_LANGUAGE];
        for (const k of keys) {
          if (val && typeof val === "object" && k in val) {
            val = val[k];
          } else {
            val = undefined;
            break;
          }
        }
      }

      if (val === undefined || typeof val !== "string") {
        return key;
      }

      let result = val;
      for (const [paramKey, paramVal] of Object.entries(params)) {
        result = result.replace(new RegExp(`\\{${paramKey}\\}`, "g"), String(paramVal));
      }
      return result;
    },
    [language]
  );

  const value = useMemo(
    () => ({
      language,
      setLanguage,
      t,
    }),
    [language, setLanguage, t]
  );

  return (
    <LanguageContext.Provider value={value}>
      {children}
    </LanguageContext.Provider>
  );
}
