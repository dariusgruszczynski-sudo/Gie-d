import { describe, expect, it } from "vitest";
import { withShare } from "./client";

// Uwaga: shareToken czytany jest z window.location przy imporcie modułu; w
// środowisku `node` window nie istnieje, więc token jest "" i withShare zwraca
// ścieżkę bez zmian. To dokładnie zachowanie "brak trybu podglądu".
describe("withShare (bez tokenu podglądu)", () => {
  it("zwraca ścieżkę bez zmian, gdy nie ma tokenu", () => {
    expect(withShare("/api/status")).toBe("/api/status");
    expect(withShare("/api/portfolio?limit=600")).toBe("/api/portfolio?limit=600");
  });
});
