import { Link, NavLink } from "react-router-dom";

export function Header() {
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
          <NavLink
            to="/how-it-works"
            className={({ isActive }) => `nav-link ${isActive ? "active" : ""}`}
          >
            How it works
          </NavLink>
          <NavLink
            to="/sources"
            className={({ isActive }) => `nav-link ${isActive ? "active" : ""}`}
          >
            Sources
          </NavLink>
        </nav>
      </div>
    </header>
  );
}

export default Header;
