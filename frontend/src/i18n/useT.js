import { useContext } from "react";
import { LanguageContext } from "./LanguageContext";

export function useT() {
  const context = useContext(LanguageContext);
  if (!context) {
    throw new Error("useT must be used within a LanguageProvider");
  }
  return context;
}

export default useT;
