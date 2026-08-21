// ESLint (flat config) dla panelu. Zestaw skupiony na REALNYCH błędach React/TS,
// nie na czystym stylu (formatowanie zostawiamy edytorowi). Odpalane w CI i
// lokalnie: `npm run lint`.
import js from "@eslint/js";
import tseslint from "typescript-eslint";
import reactHooks from "eslint-plugin-react-hooks";
import reactRefresh from "eslint-plugin-react-refresh";

export default tseslint.config(
  { ignores: ["dist", "node_modules", "../backend/static"] },
  {
    files: ["src/**/*.{ts,tsx}"],
    extends: [js.configs.recommended, ...tseslint.configs.recommended],
    plugins: {
      "react-hooks": reactHooks,
      "react-refresh": reactRefresh,
    },
    rules: {
      // Tylko dwie klasyczne, wartościowe reguły hooków. Świadomie NIE włączamy
      // pełnego recommended v7 (React Compiler: purity/set-state-in-effect) —
      // sypie fałszywymi trafieniami na normalnych wzorcach (np. Date.now()
      // w renderze dla „teraz"), co zaszumia CI bez realnej wartości.
      "react-hooks/rules-of-hooks": "error",   // wywołanie hooka poza topem = realny bug
      "react-hooks/exhaustive-deps": "warn",   // nieaktualne domknięcia w zależnościach
      "react-refresh/only-export-components": ["warn", { allowConstantExport: true }],
      "@typescript-eslint/no-unused-vars": ["warn", { argsIgnorePattern: "^_", varsIgnorePattern: "^_" }],
    },
  },
  // Pliki testowe: luźniej (mocki, any bywają potrzebne).
  {
    files: ["src/**/*.test.{ts,tsx}"],
    rules: { "@typescript-eslint/no-explicit-any": "off" },
  },
);
