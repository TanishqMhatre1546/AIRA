import React from "react";
import { Link } from "react-router-dom";
import { useT } from "../i18n/useT";

export function NotFound() {
  const { t } = useT();

  return (
    <div className="landing-container">
      <section className="landing-section" style={{ borderTop: "none" }}>
        <h1 className="landing-section-title">{t("notFound.title")}</h1>
        <p className="landing-text">
          {t("notFound.message")}
        </p>
        <p className="landing-text">
          <Link to="/" className="landing-link">
            {t("notFound.homeLink")}
          </Link>
          .
        </p>
      </section>
    </div>
  );
}

export default NotFound;
