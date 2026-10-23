import React from "react";
import { render, screen, fireEvent, act } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { MemoryRouter } from "react-router-dom";
import SymptomForm from "../components/SymptomForm";
import ResultCard from "../components/ResultCard";
import EmergencyBanner from "../components/EmergencyBanner";
import CrisisBanner from "../components/CrisisBanner";
import RefusalNotice from "../components/RefusalNotice";
import { LanguageProvider, STORAGE_KEY } from "../i18n/LanguageContext";
import { splitIntoSentences, cleanTextForSpeech, findVoiceForLocale } from "../hooks/useSpeechSynthesis";

describe("Voice Features: Web Speech API Integration", () => {
  let originalSpeechRecognition;
  let originalWebkitSpeechRecognition;
  let originalSpeechSynthesis;
  let originalSpeechSynthesisUtterance;

  beforeEach(() => {
    localStorage.clear();
    originalSpeechRecognition = window.SpeechRecognition;
    originalWebkitSpeechRecognition = window.webkitSpeechRecognition;
    originalSpeechSynthesis = window.speechSynthesis;
    originalSpeechSynthesisUtterance = window.SpeechSynthesisUtterance;
  });

  afterEach(() => {
    localStorage.clear();
    window.SpeechRecognition = originalSpeechRecognition;
    window.webkitSpeechRecognition = originalWebkitSpeechRecognition;
    window.speechSynthesis = originalSpeechSynthesis;
    window.SpeechSynthesisUtterance = originalSpeechSynthesisUtterance;
    vi.restoreAllMocks();
  });

  describe("Sentence chunking & Text cleaning utilities", () => {
    it("strips citation markers and cleans extra whitespace", () => {
      const text = "Drink fluids [1] and take rest [2]. Persistent fever [10] is a red flag.";
      const cleaned = cleanTextForSpeech(text);
      expect(cleaned).toBe("Drink fluids and take rest. Persistent fever is a red flag.");
    });

    it("splits Devanagari and Latin text into sentences on danda and punctuation", () => {
      const text = "सीने में दर्द है। सांस लेने में परेशानी हो रही है॥ तुरंत डॉक्टर को दिखाएं.";
      const sentences = splitIntoSentences(text);
      expect(sentences).toHaveLength(3);
      expect(sentences[0]).toBe("सीने में दर्द है।");
      expect(sentences[1]).toBe("सांस लेने में परेशानी हो रही है॥");
      expect(sentences[2]).toBe("तुरंत डॉक्टर को दिखाएं.");
    });

    it("matches voices correctly by exact locale and language prefix", () => {
      const voices = [
        { name: "Google US English", lang: "en-US" },
        { name: "Google Hindi", lang: "hi-IN" },
        { name: "Google UK English", lang: "en-GB" },
      ];

      expect(findVoiceForLocale(voices, "hi-IN")?.name).toBe("Google Hindi");
      expect(findVoiceForLocale(voices, "en-IN")?.name).toBe("Google US English"); // fallback en-*
      expect(findVoiceForLocale(voices, "mr-IN")).toBeNull(); // No Marathi voice
    });
  });

  describe("Voice Input (SpeechRecognition in SymptomForm)", () => {
    function setupMockSpeechRecognition() {
      let instance = null;
      const MockRecognition = vi.fn().mockImplementation(function () {
        this.continuous = false;
        this.interimResults = false;
        this.lang = "en-IN";
        this.onstart = null;
        this.onresult = null;
        this.onerror = null;
        this.onend = null;
        this.start = vi.fn().mockImplementation(() => {
          if (this.onstart) this.onstart();
        });
        this.stop = vi.fn().mockImplementation(() => {
          if (this.onend) this.onend();
        });
        this.abort = vi.fn().mockImplementation(() => {
          if (this.onend) this.onend();
        });
        instance = this;
      });

      window.SpeechRecognition = MockRecognition;
      return {
        MockRecognition,
        getInstance: () => instance,
      };
    }

    it("shows fallback note when SpeechRecognition is not supported", () => {
      delete window.SpeechRecognition;
      delete window.webkitSpeechRecognition;

      render(
        <LanguageProvider>
          <SymptomForm message="" setMessage={() => {}} onSubmit={() => {}} loading={false} />
        </LanguageProvider>
      );

      expect(screen.queryByTestId("voice-input-button")).not.toBeInTheDocument();
      expect(screen.getByTestId("voice-unsupported-note")).toHaveTextContent(
        "Voice input works in Chrome and Edge."
      );
    });

    it("renders microphone button and initiates recognition in English (en-IN)", () => {
      const { getInstance } = setupMockSpeechRecognition();
      const setMessage = vi.fn();

      render(
        <LanguageProvider>
          <SymptomForm message="" setMessage={setMessage} onSubmit={() => {}} loading={false} />
        </LanguageProvider>
      );

      const micButton = screen.getByTestId("voice-input-button");
      expect(micButton).toHaveAttribute("aria-label", "Speak");
      expect(micButton).toHaveTextContent("Speak");

      fireEvent.click(micButton);
      const instance = getInstance();
      expect(instance).toBeDefined();
      expect(instance.lang).toBe("en-IN");
      expect(screen.getByTestId("voice-status-feedback")).toHaveTextContent("Listening");
    });

    it("sets correct locale for Hindi (hi-IN) and Marathi (mr-IN)", () => {
      const { getInstance } = setupMockSpeechRecognition();

      // Hindi
      localStorage.setItem(STORAGE_KEY, "hi");
      const { unmount } = render(
        <LanguageProvider>
          <SymptomForm message="" setMessage={() => {}} onSubmit={() => {}} loading={false} />
        </LanguageProvider>
      );
      fireEvent.click(screen.getByTestId("voice-input-button"));
      expect(getInstance().lang).toBe("hi-IN");
      unmount();

      // Marathi
      localStorage.setItem(STORAGE_KEY, "mr");
      render(
        <LanguageProvider>
          <SymptomForm message="" setMessage={() => {}} onSubmit={() => {}} loading={false} />
        </LanguageProvider>
      );
      fireEvent.click(screen.getByTestId("voice-input-button"));
      expect(getInstance().lang).toBe("mr-IN");
    });

    it("updates text area with interim and final transcript without submitting", () => {
      const { getInstance } = setupMockSpeechRecognition();
      let currentMsg = "";
      const setMessage = vi.fn((newMsg) => {
        currentMsg = newMsg;
      });

      render(
        <LanguageProvider>
          <SymptomForm
            message={currentMsg}
            setMessage={setMessage}
            onSubmit={vi.fn()}
            loading={false}
          />
        </LanguageProvider>
      );

      fireEvent.click(screen.getByTestId("voice-input-button"));
      const instance = getInstance();

      act(() => {
        instance.onresult({
          results: [
            [{ transcript: "I have a cough and cold" }],
          ],
        });
      });

      expect(setMessage).toHaveBeenCalledWith("I have a cough and cold");

      act(() => {
        instance.onend();
      });

      expect(screen.getByTestId("voice-status-feedback")).toHaveTextContent(
        "Check the text, then press Check guidelines"
      );
    });

    it("enforces the 500-character cap on speech input", () => {
      const { getInstance } = setupMockSpeechRecognition();
      const setMessage = vi.fn();

      render(
        <LanguageProvider>
          <SymptomForm message="" setMessage={setMessage} onSubmit={vi.fn()} loading={false} />
        </LanguageProvider>
      );

      fireEvent.click(screen.getByTestId("voice-input-button"));
      const instance = getInstance();

      const veryLongString = "a".repeat(600);
      act(() => {
        instance.onresult({
          results: [[{ transcript: veryLongString }]],
        });
      });

      expect(setMessage).toHaveBeenCalledWith("a".repeat(500));
    });

    it("displays blocked message when microphone permission is denied", () => {
      const { getInstance } = setupMockSpeechRecognition();

      render(
        <LanguageProvider>
          <SymptomForm message="" setMessage={vi.fn()} onSubmit={vi.fn()} loading={false} />
        </LanguageProvider>
      );

      fireEvent.click(screen.getByTestId("voice-input-button"));
      const instance = getInstance();

      act(() => {
        instance.onerror({ error: "not-allowed" });
      });

      expect(screen.getByTestId("voice-status-feedback")).toHaveTextContent(
        "Allow the microphone in your browser settings"
      );
    });

    it("displays no speech message when no speech is detected", () => {
      const { getInstance } = setupMockSpeechRecognition();

      render(
        <LanguageProvider>
          <SymptomForm message="" setMessage={vi.fn()} onSubmit={vi.fn()} loading={false} />
        </LanguageProvider>
      );

      fireEvent.click(screen.getByTestId("voice-input-button"));
      const instance = getInstance();

      act(() => {
        instance.onerror({ error: "no-speech" });
        instance.onend();
      });

      expect(screen.getByTestId("voice-status-feedback")).toHaveTextContent(
        "No speech heard"
      );
    });

    it("stops listening when Escape key is pressed", () => {
      const { getInstance } = setupMockSpeechRecognition();

      render(
        <LanguageProvider>
          <SymptomForm message="" setMessage={vi.fn()} onSubmit={vi.fn()} loading={false} />
        </LanguageProvider>
      );

      fireEvent.click(screen.getByTestId("voice-input-button"));
      const instance = getInstance();
      expect(instance.stop).not.toHaveBeenCalled();

      fireEvent.keyDown(window, { key: "Escape" });
      expect(instance.stop).toHaveBeenCalled();
    });
  });

  describe("Read Aloud (SpeechSynthesis)", () => {
    let mockVoices = [];
    let speakSpy;
    let cancelSpy;

    function setupMockSpeechSynthesis(customVoices = null) {
      mockVoices = customVoices || [
        { name: "English Voice", lang: "en-IN" },
        { name: "Hindi Voice", lang: "hi-IN" },
        { name: "Marathi Voice", lang: "mr-IN" },
      ];

      speakSpy = vi.fn();
      cancelSpy = vi.fn();

      window.speechSynthesis = {
        getVoices: vi.fn().mockReturnValue(mockVoices),
        speak: speakSpy,
        cancel: cancelSpy,
        onvoiceschanged: null,
      };

      window.SpeechSynthesisUtterance = vi.fn().mockImplementation(function (text) {
        this.text = text;
        this.lang = "";
        this.voice = null;
        this.onend = null;
        this.onerror = null;
      });
    }

    it("renders Listen button on ResultCard when voice exists and speaks on click", () => {
      setupMockSpeechSynthesis();

      const sampleResult = {
        response_type: "ANSWER",
        triage_level: "SELF_CARE",
        sections: [
          {
            heading: "What guidelines say",
            content: "Rest and oral hydration [1].",
            items: [],
          },
        ],
        citations: [],
      };

      render(
        <MemoryRouter>
          <LanguageProvider>
            <ResultCard result={sampleResult} onReset={() => {}} onRetry={() => {}} />
          </LanguageProvider>
        </MemoryRouter>
      );

      const listenBtn = screen.getByTestId("result-listen-button");
      expect(listenBtn).toHaveTextContent("Listen");

      fireEvent.click(listenBtn);
      expect(speakSpy).toHaveBeenCalled();
      expect(listenBtn).toHaveTextContent("Stop");

      // Clicking stop halts speech
      fireEvent.click(listenBtn);
      expect(cancelSpy).toHaveBeenCalled();
      expect(listenBtn).toHaveTextContent("Listen");
    });

    it("hides button and shows 'No voice' notice if device has no voice for language", () => {
      // Only English voice installed on client, switch language to Marathi
      localStorage.setItem(STORAGE_KEY, "mr");
      setupMockSpeechSynthesis([{ name: "English Voice", lang: "en-US" }]);

      render(
        <MemoryRouter>
          <LanguageProvider>
            <EmergencyBanner message="छातीत तीव्र वेदना होत आहेत" helplines={[]} />
          </LanguageProvider>
        </MemoryRouter>
      );

      expect(screen.queryByTestId("emergency-listen-button")).not.toBeInTheDocument();
      expect(screen.getByTestId("no-voice-note")).toHaveTextContent(
        "या डिव्हाइसवर या भाषेसाठी कोणताही आवाज उपलब्ध नाही."
      );
    });

    it("renders Listen button and speaks on EmergencyBanner, CrisisBanner, and RefusalNotice", () => {
      setupMockSpeechSynthesis();

      // EmergencyBanner
      const { unmount: unmountEmergency } = render(
        <LanguageProvider>
          <EmergencyBanner message="Severe chest pain radiating to arm" helplines={[]} />
        </LanguageProvider>
      );
      const emergBtn = screen.getByTestId("emergency-listen-button");
      fireEvent.click(emergBtn);
      expect(speakSpy).toHaveBeenCalled();
      unmountEmergency();

      // CrisisBanner
      localStorage.setItem(STORAGE_KEY, "hi");
      const { unmount: unmountCrisis } = render(
        <LanguageProvider>
          <CrisisBanner message="सहायता उपलब्ध है" helplines={[]} />
        </LanguageProvider>
      );
      const crisisBtn = screen.getByTestId("crisis-listen-button");
      fireEvent.click(crisisBtn);
      expect(speakSpy).toHaveBeenCalled();
      unmountCrisis();

      // RefusalNotice
      localStorage.setItem(STORAGE_KEY, "en");
      render(
        <LanguageProvider>
          <RefusalNotice message="AIRA does not give medicine dosages." />
        </LanguageProvider>
      );
      const refusalBtn = screen.getByTestId("refusal-listen-button");
      fireEvent.click(refusalBtn);
      expect(speakSpy).toHaveBeenCalled();
    });

    it("stops speech when Escape key is pressed", () => {
      setupMockSpeechSynthesis();

      const sampleResult = {
        response_type: "ANSWER",
        triage_level: "SELF_CARE",
        sections: [{ heading: "Notice", content: "Stay hydrated.", items: [] }],
      };

      render(
        <MemoryRouter>
          <LanguageProvider>
            <ResultCard result={sampleResult} onReset={() => {}} onRetry={() => {}} />
          </LanguageProvider>
        </MemoryRouter>
      );

      const listenBtn = screen.getByTestId("result-listen-button");
      fireEvent.click(listenBtn);
      expect(listenBtn).toHaveTextContent("Stop");

      fireEvent.keyDown(window, { key: "Escape" });
      expect(cancelSpy).toHaveBeenCalled();
      expect(listenBtn).toHaveTextContent("Listen");
    });
  });
});
