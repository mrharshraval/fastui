import { defineConfig, globalIgnores } from "eslint/config";
import nextVitals from "eslint-config-next/core-web-vitals";

const eslintConfig = defineConfig([
  ...nextVitals,
  globalIgnores([
    ".next/**",
    "out/**",
    "build/**",
    "next-env.d.ts",
    "src/core/api/generated/schema.d.ts",
  ]),
  {
    // Rule for core/: core cannot import from features/ or app/
    files: ["src/core/**/*.ts", "src/core/**/*.tsx"],
    rules: {
      "no-restricted-imports": [
        "error",
        {
          patterns: [
            {
              group: ["@/features/**", "../features/**", "../../features/**", "@/app/**"],
              message: "Architecture Violation: core/ cannot import from features/ or app/.",
            },
          ],
        },
      ],
    },
  },
  {
    // Rule for shared/: shared cannot import from features/, core/, or app/
    files: ["src/shared/**/*.ts", "src/shared/**/*.tsx"],
    rules: {
      "no-restricted-imports": [
        "error",
        {
          patterns: [
            {
              group: ["@/features/**", "@/core/**", "@/app/**"],
              message: "Architecture Violation: shared/ must remain strictly domain-agnostic and cannot import from features/, core/, or app/.",
            },
          ],
        },
      ],
    },
  },
  {
    // General rule: prevent uncanonical HTTP transport libraries
    files: ["src/**/*.ts", "src/**/*.tsx"],
    rules: {
      "no-restricted-imports": [
        "error",
        {
          patterns: [
            {
              group: ["axios", "node-fetch"],
              message: "Use canonical transport in @/core/api/client.",
            },
          ],
        },
      ],
      "react-hooks/set-state-in-effect": "off",
      "react-hooks/refs": "off",
      "@next/next/no-location-assign-relative-destination": "warn",
    },
  },
]);

export default eslintConfig;
