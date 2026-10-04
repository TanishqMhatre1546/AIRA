import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const srcDir = path.resolve(__dirname, "../src");
const indexHtmlPath = path.resolve(__dirname, "../index.html");

const ALLOWED_HEX = new Set([
  "#f4f9f9",
  "#ffffff",
  "#e1f1f1",
  "#cfe0e0",
  "#5f8a8a",
  "#12303a",
  "#475b63",
  "#0b6e72",
  "#084f52",
  "#b3261e",
  "#fdecea",
  "#8c1d18",
  "#1b7a4b",
  "#e4f4eb",
  "#8a5a00",
  "#fff4db",
  "#3f6670",
  "#eaf1f3",
]);

// WCAG Contrast Calculation
function hexToRgb(hex) {
  const cleanHex = hex.replace("#", "");
  const num = parseInt(cleanHex, 16);
  return {
    r: (num >> 16) & 255,
    g: (num >> 8) & 255,
    b: num & 255,
  };
}

function relativeLuminance(rgb) {
  const srgb = [rgb.r / 255, rgb.g / 255, rgb.b / 255].map((val) => {
    return val <= 0.03928 ? val / 12.92 : Math.pow((val + 0.055) / 1.055, 2.4);
  });
  return 0.2126 * srgb[0] + 0.7152 * srgb[1] + 0.0722 * srgb[2];
}

function contrastRatio(hex1, hex2) {
  const lum1 = relativeLuminance(hexToRgb(hex1));
  const lum2 = relativeLuminance(hexToRgb(hex2));
  const brightest = Math.max(lum1, lum2);
  const darkest = Math.min(lum1, lum2);
  return (brightest + 0.05) / (darkest + 0.05);
}

const FORBIDDEN_PATTERNS = [
  { name: "Em dash (U+2014)", regex: /\u2014/ },
  { name: "En dash (U+2013)", regex: /\u2013/ },
  { name: "Gradient", regex: /gradient\(/i },
  { name: "Keyframes / Animation", regex: /@keyframes|animation:|animation-name:/i },
  { name: "Scroll behavior", regex: /scroll-behavior:/i },
  { name: "Prefers color scheme", regex: /prefers-color-scheme/i },
  { name: "IntersectionObserver", regex: /IntersectionObserver/ },
  { name: "Mousemove listener", regex: /mousemove/i },
  { name: "External font or style URL", regex: /https?:\/\/[a-zA-Z0-9.-]+\/(?:css|font|webfont)/i },
  { name: "Emoji characters", regex: /[\u{1F300}-\u{1F9FF}\u{2600}-\u{26FF}\u{2700}-\u{27BF}]/u },
  { name: "Purple keywords", regex: /\b(purple|rebeccapurple|magenta|violet)\b/i },
];

function scanDirectory(dir, fileList = []) {
  const files = fs.readdirSync(dir);
  for (const file of files) {
    const fullPath = path.join(dir, file);
    const stat = fs.statSync(fullPath);
    if (stat.isDirectory()) {
      scanDirectory(fullPath, fileList);
    } else {
      fileList.push(fullPath);
    }
  }
  return fileList;
}

function runLint() {
  console.log("Running AIRA frontend design lint...\n");
  let errorCount = 0;

  // 1. Check WCAG contrast pairings
  const pairings = [
    { fg: "#12303a", bg: "#f4f9f9", min: 4.5, label: "Text on Page" },
    { fg: "#12303a", bg: "#ffffff", min: 4.5, label: "Text on Surface" },
    { fg: "#12303a", bg: "#e1f1f1", min: 4.5, label: "Text on Tint" },
    { fg: "#475b63", bg: "#f4f9f9", min: 4.5, label: "Muted text on Page" },
    { fg: "#475b63", bg: "#ffffff", min: 4.5, label: "Muted text on Surface" },
    { fg: "#475b63", bg: "#e1f1f1", min: 4.5, label: "Muted text on Tint" },
    { fg: "#0b6e72", bg: "#ffffff", min: 4.5, label: "Primary on Surface" },
    { fg: "#0b6e72", bg: "#f4f9f9", min: 4.5, label: "Primary on Page" },
    { fg: "#084f52", bg: "#e1f1f1", min: 4.5, label: "Primary-dark on Tint" },
    { fg: "#ffffff", bg: "#0b6e72", min: 4.5, label: "White on Primary" },
    { fg: "#ffffff", bg: "#b3261e", min: 4.5, label: "White on Emergency" },
    { fg: "#8c1d18", bg: "#fdecea", min: 4.5, label: "Emergency-dark on Emergency-tint" },
    { fg: "#b3261e", bg: "#ffffff", min: 4.5, label: "Emergency on Surface" },
    { fg: "#1b7a4b", bg: "#e4f4eb", min: 4.5, label: "Self-Care on Tint" },
    { fg: "#1b7a4b", bg: "#ffffff", min: 4.5, label: "Self-Care on Surface" },
    { fg: "#8a5a00", bg: "#fff4db", min: 4.5, label: "See-Doctor on Tint" },
    { fg: "#8a5a00", bg: "#ffffff", min: 4.5, label: "See-Doctor on Surface" },
    { fg: "#3f6670", bg: "#eaf1f3", min: 4.5, label: "Unknown on Tint" },
    { fg: "#3f6670", bg: "#ffffff", min: 4.5, label: "Unknown on Surface" },
    { fg: "#5f8a8a", bg: "#ffffff", min: 3.0, label: "Input border on Surface" },
  ];

  console.log("Validating WCAG AA Contrast (>= 4.5:1 text, >= 3.0:1 controls):");
  for (const pair of pairings) {
    const ratio = contrastRatio(pair.fg, pair.bg);
    const pass = ratio >= pair.min;
    console.log(`  ${pair.label} (${pair.fg} on ${pair.bg}): ${ratio.toFixed(2)}:1 [${pass ? "PASS" : "FAIL"}]`);
    if (!pass) {
      console.error(`  Contrast violation for ${pair.label}!`);
      errorCount++;
    }
  }
  console.log("");

  // 2. Check HTML color-scheme
  if (fs.existsSync(indexHtmlPath)) {
    const indexHtml = fs.readFileSync(indexHtmlPath, "utf-8");
    if (!indexHtml.includes('<meta name="color-scheme" content="light"')) {
      console.error("[FAIL] Missing <meta name=\"color-scheme\" content=\"light\"> in index.html");
      errorCount++;
    }
  }

  // 3. Scan all files in src/
  const allFiles = scanDirectory(srcDir);

  for (const filePath of allFiles) {
    const relPath = path.relative(srcDir, filePath);
    const content = fs.readFileSync(filePath, "utf-8");
    const isCss = filePath.endsWith(".css");

    // Check forbidden regex patterns
    for (const pattern of FORBIDDEN_PATTERNS) {
      if (pattern.regex.test(content)) {
        console.error(`[FAIL] ${pattern.name} found in src/${relPath}`);
        errorCount++;
      }
    }

    // Check CSS specific rules
    if (isCss) {
      // Check hex colors
      const hexMatches = content.match(/#[0-9a-fA-F]{3,8}\b/g) || [];
      for (const hex of hexMatches) {
        const lowerHex = hex.toLowerCase();
        const normHex =
          lowerHex.length === 4
            ? `#${lowerHex[1]}${lowerHex[1]}${lowerHex[2]}${lowerHex[2]}${lowerHex[3]}${lowerHex[3]}`
            : lowerHex;

        if (!ALLOWED_HEX.has(normHex)) {
          console.error(`[FAIL] Unapproved color '${hex}' in src/${relPath}. Only approved design tokens are allowed.`);
          errorCount++;
        }
      }

      // Check border radius > 8px
      const radiusMatches = content.match(/border-radius:\s*([0-9]+)px/g) || [];
      for (const match of radiusMatches) {
        const pxVal = parseInt(match.replace(/[^0-9]/g, ""), 10);
        if (pxVal > 8) {
          console.error(`[FAIL] Disallowed border-radius '${match}' in src/${relPath} (> 8px).`);
          errorCount++;
        }
      }

      // Check box-shadow
      const shadowMatches = content.match(/box-shadow:\s*([^;]+);/g) || [];
      for (const shadow of shadowMatches) {
        const shadowVal = shadow.replace(/box-shadow:\s*/, "").replace(";", "").trim();
        const isAllowed =
          shadowVal === "none" ||
          shadowVal === "none !important" ||
          shadowVal === "var(--shadow-card)" ||
          shadowVal === "0 1px 2px rgba(18, 48, 58, 0.08)";
        if (!isAllowed) {
          console.error(`[FAIL] Unapproved box-shadow '${shadowVal}' in src/${relPath}.`);
          errorCount++;
        }
      }
    }
  }

  if (errorCount > 0) {
    console.error(`\nDesign lint failed with ${errorCount} error(s).`);
    process.exit(1);
  } else {
    console.log("\nAll design lint checks passed successfully! (0 errors)\n");
  }
}

runLint();
