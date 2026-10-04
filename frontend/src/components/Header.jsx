import React from "react";
import { Link, NavLink, useLocation } from "react-router-dom";

export function Header() {
  const location = useLocation();
  const isLanding = location.pathname === "/";

  return (
    <header className="site-header" role="banner">
      <div className="header-container">
        <div className="brand-group">
          <Link to="/" className="brand-wordmark" aria-label="AIRA Home">
            AIRA
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
  );
}

export default Header;
