import React, { useEffect, useRef, useState } from "react";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faCheck } from "@fortawesome/free-solid-svg-icons";
import { useT } from "../i18n/useT";

const OPTIONS = [
  { code: "en", label: "English" },
  { code: "hi", label: "हिन्दी" },
  { code: "mr", label: "मराठी" },
];

export function LanguageToggle() {
  const { language, setLanguage, t } = useT();
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef(null);
  const buttonRef = useRef(null);

  const toggleDropdown = () => {
    setIsOpen((prev) => !prev);
  };

  const handleSelect = (code) => {
    setLanguage(code);
    setIsOpen(false);
    if (buttonRef.current) {
      buttonRef.current.focus();
    }
  };

  useEffect(() => {
    if (!isOpen) return;

    const handleKeyDown = (e) => {
      if (e.key === "Escape") {
        setIsOpen(false);
        if (buttonRef.current) {
          buttonRef.current.focus();
        }
      }
    };

    const handleClickOutside = (e) => {
      if (containerRef.current && !containerRef.current.contains(e.target)) {
        setIsOpen(false);
      }
    };

    document.addEventListener("keydown", handleKeyDown);
    document.addEventListener("mousedown", handleClickOutside);

    return () => {
      document.removeEventListener("keydown", handleKeyDown);
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [isOpen]);

  return (
    <div className="language-toggle-container" ref={containerRef}>
      <button
        ref={buttonRef}
        type="button"
        className="language-toggle-button"
        onClick={toggleDropdown}
        aria-haspopup="true"
        aria-expanded={isOpen}
        aria-label={t("header.changeLanguage")}
      >
        अ A
      </button>

      {isOpen && (
        <div className="language-dropdown-panel" role="menu">
          {OPTIONS.map((opt) => {
            const isSelected = language === opt.code;
            return (
              <button
                key={opt.code}
                type="button"
                className={`language-option-button ${isSelected ? "selected" : ""}`}
                role="menuitem"
                onClick={() => handleSelect(opt.code)}
              >
                <span className="language-option-label">{opt.label}</span>
                {isSelected && (
                  <FontAwesomeIcon
                    icon={faCheck}
                    className="language-option-check"
                    aria-hidden="true"
                  />
                )}
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}

export default LanguageToggle;
