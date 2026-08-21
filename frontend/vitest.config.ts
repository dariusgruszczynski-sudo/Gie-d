import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

// Testy jednostkowe czystych funkcji panelu (formatowanie kwot, link share,
// etykiety). Środowisko `node` wystarcza — nie renderujemy DOM, więc bez jsdom.
export default defineConfig({
  plugins: [react()],
  test: {
    environment: "node",
    include: ["src/**/*.test.{ts,tsx}"],
  },
});
