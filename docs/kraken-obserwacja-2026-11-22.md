# Raport z obserwacji — noga krypto na Kraken (paper)

**Data:** 2026-11-22, ~01:00 UTC
**Stan:** Kraken podłączony (klucz przez panel), tryb PAPER/dry-run, `crypto_kraken_live=False`.

---

## 1. Co DZIAŁA (zielone)

| Element | Stan | Dowód |
|---|---|---|
| Połączenie z Krakenem | ✅ | `key_present=true`, źródło `panel`; saldo odczytane **€119.81** |
| Skaner uniwersum (EUR) | ✅ | `BTC/EUR, ETH/EUR, SOL/EUR, LINK/EUR, AVAX/EUR, DOGE/EUR, LTC/EUR` |
| Cykl krypto | ✅ | `reason: ok`, `last_error: None`, odświeżany co 15 min |
| Tryb paper | ✅ | `live_trading=false` — zero wydanych środków |
| Konto (realne) | ✅ | gotówka €119.81, pozycje 0, total €119.81 |

**Wniosek techniczny:** migracja Alpaca → Kraken **zadziałała**. Noga krypto realnie
łączy się z Krakenem, skanuje pary EUR, mieli cykle bez błędów.

---

## 2. Co NIE DZIAŁA — i to jest pilne (czerwone)

**Noga paper jest ZABLOKOWANA fałszywym HALTem z ery Alpaca.**

- `is_halted = true`
- `halted_reason = "Dzienny limit strat przekroczony: -100.0% (limit 30.0%)"`

To **artefakt**, nie realna strata: licznik dnia bazuje na starym szczycie konta
Alpaca (**€840 454**), a realne konto to €119.81 → pozorne **-100%** → auto-HALT.

**Konsekwencja:** dopóki HALT trzyma, noga paper tylko mieli **HOLD** (12/12 ostatnich
decyzji = HOLD, zero wejść). Czyli *obserwacji realnie nie ma* — bot nie może wejść
nawet papierowo, bo globalny HALT blokuje nowe pozycje. **To trzeba zdjąć, żeby paper
w ogóle ruszył.**

---

## 3. Trupy z ery Alpaca zaśmiecające pulpit

Wszystkie poniższe to zaszłości, które nie mają nic wspólnego z kontem Kraken €120:

| Pole na pulpicie | Pokazuje | Prawda (Kraken) |
|---|---|---|
| Wynik netto | **-€378 118** | €0 (świeży start) |
| Zrealizowany P&L | **-€378 118** | €0 |
| Szczyt konta | **€840 455** | €119.81 |
| P&L dzień / tydzień | **-99.98% / -99.98%** | ~0% |
| Pozycje krypto (rozjazd) | **ETH 7.69 + UNI 291.9 = €14 447** | 0 (Kraken ma 0) |
| Rekoncyliacja | **reconciled: false** (czerwony baner) | powinno być zielone |
| Benchmark | **BTC/USD** | BTC/EUR |
| Uniwersum (kafel) | **…/USD** | …/EUR |
| Waluta (główny kafel) | **USD** | EUR dla krypto |
| Tryb | **testnet** | paper na Kraken |
| Epoka pomiaru | **2026-08-10** (Alpaca) | dziś (start Kraken) |

**To są „historyczne liczby", o których mówiłeś.** Nie są błędem w handlu — to lustro
starego konta, które po migracji wprowadza w błąd i straszy.

---

## 4. Rekomendacja

Jeden ruch rozwiązuje punkty 2 i 3 naraz: **czysty start pod Kraken** (re-bazowanie
do €119.81, zdjęcie HALTu, skasowanie fantomowych pozycji, epoka = dziś, benchmark
BTC/EUR, uniwersum EUR). Lekcje (nauka bota) **zostają**.

Po tym: pulpit pokazuje czystą rzeczywistość Kraken €120, HALT znika, a noga paper
może realnie wchodzić (dry-run) — i dopiero WTEDY obserwacja zaczyna mieć sens
(zbieramy dowód: skan → decyzja → egzekucja dry-run → wynik).

**Brutalnie, w procentach:** realnej obserwacji paper mamy teraz **~0%** — bo HALT
blokuje wejścia. Po czystym starcie: ~100% gotowości do obserwacji. Czas do pierwszego
sensownego wejścia paper: kilka–kilkanaście cykli (15 min każdy), zależnie od sygnałów.
