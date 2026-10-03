import React from "react";

export default function SourceList({ citations }) {
  if (!citations || citations.length === 0) return null;

  return (
    <section className="sources-section" aria-labelledby="sources-heading">
      <h4 id="sources-heading" className="sources-title">
        Sources
      </h4>
      <ol className="sources-list">
        {citations.map((cite) => {
          const pageText = cite.page ? ` (p. ${cite.page})` : "";
          const metaText = `${cite.publisher}, ${cite.year}${pageText}`;

          return (
            <li key={cite.id || cite.title} className="source-item" value={cite.id}>
              <span className="source-title">{cite.title}</span>
              <span className="source-meta"> - {metaText}</span>
              {cite.url && (
                <div>
                  <a
                    href={cite.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="source-link"
                  >
                    View guideline
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
