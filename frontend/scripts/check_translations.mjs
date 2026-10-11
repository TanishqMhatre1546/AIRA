import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const i18nDir = path.resolve(__dirname, "../src/i18n");
const enPath = path.join(i18nDir, "en.json");
const hiPath = path.join(i18nDir, "hi.json");
const mrPath = path.join(i18nDir, "mr.json");

function readJson(file) {
  return JSON.parse(fs.readFileSync(file, "utf8"));
}

function getPlaceholders(str) {
  const matches = str.match(/\{[a-zA-Z0-9_]+\}/g);
  return matches ? matches.sort() : [];
}

function flattenKeys(obj, prefix = "") {
  let result = {};
  for (const [key, value] of Object.entries(obj)) {
    const nextKey = prefix ? `${prefix}.${key}` : key;
    if (value !== null && typeof value === "object" && !Array.isArray(value)) {
      Object.assign(result, flattenKeys(value, nextKey));
    } else {
      result[nextKey] = value;
    }
  }
  return result;
}

const en = readJson(enPath);
const hi = readJson(hiPath);
const mr = readJson(mrPath);

const enFlat = flattenKeys(en);
const hiFlat = flattenKeys(hi);
const mrFlat = flattenKeys(mr);

let errors = [];

function checkLanguage(langCode, targetFlat) {
  for (const [key, enValue] of Object.entries(enFlat)) {
    if (!(key in targetFlat)) {
      errors.push(`[${langCode}] Missing key: ${key}`);
      continue;
    }
    const val = targetFlat[key];
    if (typeof val === "string" && val.trim() === "") {
      errors.push(`[${langCode}] Empty value for key: ${key}`);
      continue;
    }
    if (typeof enValue === "string" && typeof val === "string") {
      const enPlaceholders = getPlaceholders(enValue);
      const targetPlaceholders = getPlaceholders(val);
      if (enPlaceholders.join(",") !== targetPlaceholders.join(",")) {
        errors.push(
          `[${langCode}] Placeholder mismatch for key ${key}: expected [${enPlaceholders.join(", ")}], got [${targetPlaceholders.join(", ")}]`
        );
      }
    }
  }

  for (const key of Object.keys(targetFlat)) {
    if (!(key in enFlat)) {
      errors.push(`[${langCode}] Extra key not in en.json: ${key}`);
    }
  }
}

checkLanguage("hi", hiFlat);
checkLanguage("mr", mrFlat);

if (errors.length > 0) {
  console.error("Translation check failed with errors:");
  for (const err of errors) {
    console.error(`  - ${err}`);
  }
  process.exit(1);
} else {
  console.log(`Translation check passed: ${Object.keys(enFlat).length} keys verified across en, hi, mr.`);
}
