import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getMeta } from "../../api/client";
import { landingContent } from "../../content/landing";

export function Coverage() {
  const { coverage } = landingContent;
  const [conditions, setConditions] = useState([]);
  const [status, setStatus] = useState("loading");

  useEffect(() => {
    let active = true;
    const controller = new AbortController();

    const timeoutId = setTimeout(() => {
      if (active) {
        setStatus((prev) => (prev === "loading" ? "fallback" : prev));
      }
    }, 4000);

    getMeta(controller.signal)
      .then((data) => {
        if (!active) return;
        clearTimeout(timeoutId);
        const list = data?.supported_conditions || [];
        if (list.length > 0) {
          setConditions(list);
          setStatus("loaded");
        } else {
          setStatus("fallback");
        }
      })
      .catch(() => {
        if (!active) return;
        clearTimeout(timeoutId);
        setStatus("fallback");
      });

    return () => {
      active = false;
      clearTimeout(timeoutId);
      controller.abort();
    };
  }, []);

  return (
    <section id="coverage" className="landing-section">
      <h2 className="landing-section-title">{coverage.heading}</h2>

      {status === "loading" && (
        <p className="landing-text landing-status-text" data-testid="coverage-loading">
          {coverage.loadingText}
        </p>
      )}

      {status === "loaded" && (
        <ul className="landing-condition-list" data-testid="coverage-list">
          {conditions.map((condition, index) => (
            <li key={index} className="landing-condition-item">
              <Link to="/sources" className="landing-link">
                {condition}
              </Link>
            </li>
          ))}
        </ul>
      )}

      {status === "fallback" && (
        <p className="landing-text" data-testid="coverage-fallback">
          The full list is on the{" "}
          <Link to="/sources" className="landing-link">
            {coverage.sourcesLinkText}
          </Link>
          .
        </p>
      )}
    </section>
  );
}

export default Coverage;
