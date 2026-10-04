import { useEffect } from "react";
import { useLocation } from "react-router-dom";

export function useHashScroll() {
  const location = useLocation();

  useEffect(() => {
    if (!location.hash) {
      return;
    }
    const targetId = location.hash.replace("#", "");
    if (!targetId) {
      return;
    }

    const scrollToAndFocus = () => {
      const element = document.getElementById(targetId);
      if (!element) {
        return false;
      }
      if (typeof element.scrollIntoView === "function") {
        element.scrollIntoView();
      }
      const heading = element.tagName.match(/^H[1-6]$/i)
        ? element
        : element.querySelector("h1, h2, h3, h4, h5, h6");
      const target = heading || element;
      target.setAttribute("tabindex", "-1");
      if (typeof target.focus === "function") {
        target.focus({ preventScroll: true });
      }
      return true;
    };

    if (!scrollToAndFocus()) {
      const timer = setTimeout(scrollToAndFocus, 50);
      return () => clearTimeout(timer);
    }
  }, [location.hash, location.pathname]);
}

export default useHashScroll;
