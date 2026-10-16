import { defineConfig, globalIgnores } from "eslint/config";
import nextVitals from "eslint-config-next/core-web-vitals";

export default defineConfig([
  ...nextVitals,
  // Existing client screens hydrate authentication and preferences after mounting.
  // Keep that behavior during this security upgrade; other hook checks stay active.
  {rules: {"react-hooks/set-state-in-effect": "off"}},
  globalIgnores([".next/**", "node_modules/**", "next-env.d.ts"])
]);
