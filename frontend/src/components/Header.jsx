import React from "react";
import { Link, NavLink, useLocation } from "react-router-dom";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faHeartPulse } from "@fortawesome/free-solid-svg-icons";

export function Header() {
  const location = useLocation();
  const isLanding = location.pathname === "/";

  return (
    <>
      <a href="#main-content" className="skip-link">
        Skip to main content
      </a>
      <header className="site-header" role="banner">
        <div className="header-container">
          <div className="brand-group">
            <Link to="/" className="brand-wordmark" aria-label="AIRA Home">
              <FontAwesomeIcon icon={faHeartPulse} className="brand-icon" aria-hidden="true" />
              <span className="brand-name">AIRA</span>
            </Link>
            <span className="brand-tagline">Clinical guidelines assistant</span>
          </div>

          <nav className="site-nav" aria-label="Main Navigation">
            {isLanding ? (
              <>
                <a href="#how-it-works" className="nav-link">
                  How it works
                </a>
                <a href="#privacy" className="nav-link">
                  Privacy
                </a>
                <a href="#terms" className="nav-link">
                  Terms
                </a>
                <NavLink
                  to="/sources"
                  className={({ isActive }) => `nav-link ${isActive ? "active" : ""}`}
                >
                  Sources
                </NavLink>
                <Link to="/app" className="header-cta-button">
                  Check symptoms
                </Link>
              </>
            ) : (
              <NavLink
                to="/sources"
                className={({ isActive }) => `nav-link ${isActive ? "active" : ""}`}
              >
                Sources
              </NavLink>
            )}
          </nav>
        </div>
      </header>
    </>
  );
}

export default Header;
