import { describe, expect, it } from "vitest";
import { ago, money, money0, pct } from "./kit";

describe("money", () => {
  it("formatuje dodatnie z dwoma miejscami i znakiem dolara", () => {
    expect(money(1234.5)).toBe("$1234,50");
  });
  it("używa znaku minus (−) dla ujemnych", () => {
    expect(money(-42)).toBe("−$42,00");
  });
  it("zwraca — dla null/undefined/NaN", () => {
    expect(money(null)).toBe("—");
    expect(money(undefined)).toBe("—");
    expect(money(NaN)).toBe("—");
  });
  it("respektuje liczbę miejsc po przecinku", () => {
    expect(money(1, 0)).toBe("$1");
  });
});

describe("money0", () => {
  it("zaokrągla do pełnych dolarów", () => {
    expect(money0(1234.7)).toBe("$1235");
  });
  it("zwraca — dla braku wartości", () => {
    expect(money0(null)).toBe("—");
  });
});

describe("pct", () => {
  it("dodaje + dla nieujemnych i dwa miejsca", () => {
    expect(pct(3.5)).toBe("+3.50%");
    expect(pct(0)).toBe("+0.00%");
  });
  it("zostawia − dla ujemnych", () => {
    expect(pct(-1.2)).toBe("-1.20%");
  });
  it("zwraca — dla braku wartości", () => {
    expect(pct(undefined)).toBe("—");
  });
});

describe("ago", () => {
  it("mówi 'przed chwilą' dla świeżej chwili", () => {
    expect(ago(new Date().toISOString())).toBe("przed chwilą");
  });
  it("liczy minuty", () => {
    const twoMinAgo = new Date(Date.now() - 2 * 60 * 1000).toISOString();
    expect(ago(twoMinAgo)).toBe("2 min temu");
  });
  it("pusty string dla niepoprawnej daty", () => {
    expect(ago("nie-data")).toBe("");
  });
});
