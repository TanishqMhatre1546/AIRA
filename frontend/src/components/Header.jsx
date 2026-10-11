import React from "react";
import { Link, NavLink, useLocation } from "react-router-dom";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faHeartPulse } from "@fortawesome/free-solid-svg-icons";
import { useT } from "../i18n/useT";
import LanguageToggle from "./LanguageToggle";

export function Header() {
  const { t } = useT();
  const location = useLocation();
  const isLanding = location.pathname === "/";

  return (
    <>
      <a href="#main-content" className="skip-link">
        {t("header.skipLink")}
      </a>
      <header className="site-header" role="banner">
        <div className="header-container">
          <div className="brand-group">
            <Link to="/" className="brand-wordmark" aria-label="AIRA Home">
              <FontAwesomeIcon icon={faHeartPulse} className="brand-icon" aria-hidden="true" />
              <span className="brand-name">{t("header.brandName")}</span>
            </Link>
            <span className="brand-tagline">{t("header.brandTagline")}</span>
          </div>

          <div className="header-right">
            <nav className="site-nav" aria-label="Main Navigation">
              {isLanding ? (
                <>
                  <a href="#how-it-works" className="nav-link">
                    {t("header.navHowItWorks")}
                  </a>
                  <a href="#privacy" className="nav-link">
                    {t("header.navPrivacy")}
                  </a>
                  <a href="#terms" className="nav-link">
                    {t("header.navTerms")}
                  </a>
                  <NavLink
                    to="/sources"
                    className={({ isActive }) => `nav-link ${isActive ? "active" : ""}`}
                  >
                    {t("header.navSources")}
                  </NavLink>
                  <Link to="/app" className="header-cta-button">
                    {t("header.checkSymptoms")}
                  </Link>
                </>
              ) : (
                <NavLink
                  to="/sources"
                  className={({ isActive }) => `nav-link ${isActive ? "active" : ""}`}
                >
                  {t("header.navSources")}
                </NavLink>
              )}
            </nav>
            <LanguageToggle />
          </div>
        </div>
      </header>
    </>
  );
}

export default Header;
