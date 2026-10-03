import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const srcDir = path.resolve(__dirname, "../src");

const ALLOWED_HEX = new Set([
  "#ffffff",
  "#f6f7f9",
  "#d5d9e0",
  "#1a1a2e",
  "#4a4f5c",
  "#b3261e",
  "#1d6a8a",
  "#1e8449",
  "#8a5a00",
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
  { name: "IntersectionObserver", regex: /IntersectionObserver/ },
  { name: "Mousemove listener", regex: /mousemove/i },
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
    { fg: "#1a1a2e", bg: "#ffffff", label: "Text on Background" },
    { fg: "#1a1a2e", bg: "#f6f7f9", label: "Text on Surface" },
    { fg: "#4a4f5c", bg: "#ffffff", label: "Muted text on Background" },
    { fg: "#4a4f5c", bg: "#f6f7f9", label: "Muted text on Surface" },
    { fg: "#ffffff", bg: "#b3261e", label: "White on Emergency" },
    { fg: "#ffffff", bg: "#1d6a8a", label: "White on Information" },
    { fg: "#ffffff", bg: "#1e8449", label: "White on Self-Care" },
    { fg: "#ffffff", bg: "#8a5a00", label: "White on Caution" },
    { fg: "#b3261e", bg: "#ffffff", label: "Emergency on Background" },
    { fg: "#1d6a8a", bg: "#ffffff", label: "Information on Background" },
    { fg: "#1e8449", bg: "#ffffff", label: "Self-Care on Background" },
    { fg: "#8a5a00", bg: "#ffffff", label: "Caution on Background" },
  ];

  console.log("Validating WCAG AA Contrast (>= 4.5:1 for normal text):");
  for (const pair of pairings) {
    const ratio = contrastRatio(pair.fg, pair.bg);
    const pass = ratio >= 4.5;
    console.log(`  ${pair.label} (${pair.fg} on ${pair.bg}): ${ratio.toFixed(2)}:1 [${pass ? "PASS" : "FAIL"}]`);
    if (!pass) {
      console.error(`  Contrast violation for ${pair.label}!`);
      errorCount++;
    }
  }
  console.log("");

  // 2. Scan all files in src/
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
        // Allow 3-digit shorthand expansion if needed
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
