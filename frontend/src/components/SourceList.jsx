import React from "react";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faArrowUpRightFromSquare } from "@fortawesome/free-solid-svg-icons";

export default function SourceList({ citations }) {
  if (!citations || citations.length === 0) return null;

  return (
    <section className="sources-section" aria-labelledby="sources-heading">
      <h4 id="sources-heading" className="sources-title">
        Sources
      </h4>
      <ol className="sources-list">
        {citations.map((cite) => {
          const title = cite.title || cite.source_title;
          const publisher = cite.publisher || cite.source_publisher;
          const year = cite.year || cite.source_year;
          const url = cite.url || cite.source_url;
          const pageText = cite.page ? ` (p. ${cite.page})` : "";
          const metaText = `${publisher}, ${year}${pageText}`;

          return (
            <li
              key={cite.id || title}
              id={`source-${cite.id}`}
              className="source-item"
              value={cite.id}
            >
              <span className="source-title">{title}</span>
              <span className="source-meta"> - {metaText}</span>
              {url && (
                <div className="source-link-wrap">
                  <a
                    href={url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="source-link"
                  >
                    <span>View guideline</span>
                    <FontAwesomeIcon
                      icon={faArrowUpRightFromSquare}
                      aria-hidden="true"
                      className="source-ext-icon"
                    />
                  </a>
                </div>
              )}
            </li>
          );
        })}
      </ol>
    </section>
  );
}
