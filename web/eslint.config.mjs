import { defineConfig, globalIgnores } from "eslint/config";
import nextVitals from "eslint-config-next/core-web-vitals";
import nextTs from "eslint-config-next/typescript";

const eslintConfig = defineConfig([
  ...nextVitals,
  ...nextTs,
  // Override default ignores of eslint-config-next.
  globalIgnores([
    // Default ignores of eslint-config-next:
    ".next/**",
    "out/**",
    "build/**",
    "next-env.d.ts",
    // Copied from the release by scripts/prepare-release.mjs at build time.
    "public/release/**",
    "public/search-index.json",
    // Local prebuilt output (`vercel build`) and test artefacts: generated, never source.
    ".vercel/**",
    "test-results/**",
    "playwright-report/**",
  ]),
]);

export default eslintConfig;
