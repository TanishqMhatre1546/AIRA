import React, { useEffect, useState } from "react";
import { getSources } from "../../api/client";

export function SourceStrip() {
  const [publishers, setPublishers] = useState([]);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    let active = true;
    getSources()
      .then((data) => {
        if (!active) return;
        if (data && Array.isArray(data.sources) && data.sources.length > 0) {
          const names = Array.from(
            new Set(data.sources.map((s) => s.publisher).filter(Boolean))
          );
          if (names.length > 0) {
            setPublishers(names);
            setVisible(true);
          }
        }
      })
      .catch(() => {
        if (active) {
          setVisible(false);
        }
      });

    return () => {
      active = false;
    };
  }, []);

  if (!visible || publishers.length === 0) {
    return null;
  }

  return (
    <div className="source-strip" data-testid="source-strip">
      <div className="source-strip-container">
        <span className="source-strip-label">Based on documents from:</span>{" "}
        <span className="source-strip-names">{publishers.join(", ")}</span>
      </div>
    </div>
  );
}

export default SourceStrip;
