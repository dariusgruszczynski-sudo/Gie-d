# Widget na ekran główny iPhone (żywy podgląd konta)

## ⭐ Wersja v3 (zalecana) — `gieldarek-widget-v3.js`

Jeden skrypt obsługuje **wiele rozmiarów i miejsc**:

- **Ekran główny:**
  - **mały** — jedna wielka liczba (metryka wybrana w apce) + konto/dzień,
  - **średni** — liczba + sparkline + ostatni ruch bota,
  - **duży** — liczba + wykres + skuteczność/edge + lista pozycji.
- **Ekran blokady (iOS 16+):** kołowy / prostokątny / liniowy — zysk dnia i konto
  na jedno spojrzenie, bez odblokowywania (przytrzymaj Lock Screen → Dostosuj →
  dodaj widżet → Scriptable → wybierz „GielDarek v3”).
- **Motyw:** u góry skryptu `THEME` = `"auto"` / `"dark"` / `"light"` / `"cyber"`.
- **Główna liczba** (Zysk automatu / dnia / konto / pozycje): wybierasz **w apce**
  (Sterowanie → „📲 Widżet — co pokazuje”); skrypt czyta ją z serwera.
- Adres i token są już wpisane; stopka pokazuje czas ostatniej aktualizacji.

**Uczciwie o granicach iOS:** kafel na ekranie głównym się nie animuje (iOS sam
odświeża co kilka minut). **Apple Watch:** Scriptable nie robi komplikacji tarczy
— najbliżej „na nadgarstku” jest widżet na ekranie **blokady** iPhone’a.
**Live Activity** (pasek tuż po transakcji) nie jest możliwa z wklejanego skryptu
— zamiast tego działają **powiadomienia push** per-transakcja (włącz w apce).

Instalacja jak niżej, tylko wklej `gieldarek-widget-v3.js`.

---

# (starsze wersje poniżej)
# Widget v1/v2 — `gieldarek-widget.js` / `gieldarek-widget-v2.js`

iOS nie pozwala zrobić natywnego widgetu z PWA, ale darmowa apka **Scriptable**
uruchamia JavaScript jako pełnoprawny widget na ekranie głównym. Skrypt
`gieldarek-widget.js` ciąga dane z Twojego **linku tylko do odczytu**
(`GET /api/status?share=…`) i pokazuje: łączny stan konta, dzienny %, wynik
netto, stan obu silników i „temperaturę" rynku — w kolorach apki.

Widget nie może nic kliknąć ani handlować (to samo ograniczenie co link
read-only). iOS odświeża widgety własnym harmonogramem (zwykle co ~5–15 min) —
to nie jest sekundowy stream, ale sam się aktualizuje w tle; tapnięcie otwiera
pełny podgląd na żywo.

## Warunek wstępny
Musisz mieć włączony **link tylko do odczytu** na serwerze (patrz Centrum
sterowania → „Link tylko do odczytu"): w `~/gie-d/.env` ustawiony `SHARE_TOKEN`.
Bez tego widget nie ma z czego czytać.

## Instalacja (raz)
1. Zainstaluj **Scriptable** z App Store (darmowe).
2. Otwórz Scriptable → **+** → wklej całą zawartość `deploy/gieldarek-widget.js`
   → nazwij np. „GielDarek".
3. Na górze pliku wpisz `BASE_URL` (np. `https://46.225.229.113.sslip.io`) i
   `SHARE_TOKEN` — **albo** zostaw puste i podaj je w kroku 5.
4. Ekran główny → przytrzymaj → **+** → **Scriptable** → wybierz rozmiar
   (**średni** pokazuje najwięcej) → Dodaj widget.
5. Przytrzymaj widget → **Edytuj widget**:
   - **Script:** GielDarek
   - **When Interacting:** Run Script (albo Open URL, żeby otwierał dashboard)
   - **Parameter:** `https://46.225.229.113.sslip.io|TWOJ_SHARE_TOKEN`
     (adres i token oddzielone `|`). To nadpisuje wartości z kodu, więc token
     nie musi siedzieć w samym skrypcie.

## Co pokazuje
- **Mały** widget: łączny stan konta + dzienny % + wynik netto + luźna gotówka.
- **Średni** widget: dodatkowo mini-wykres skuteczności (krzywa wartości konta)
  i lista trzymanych pozycji (ticker/moneta + wartość + P&L, kropka koloru
  silnika: niebieski = Akcje US, złoty = Krypto).
- **Duży** widget: to samo, ale więcej pozycji na liście.

## Nie pokazuje danych? (diagnostyka)
Widget czyta jeden endpoint: `GET /api/widget?share=<token>`. Jeśli nic nie widać:
- **„Brak SHARE_TOKEN"** na widgecie → nie wpisałeś tokenu (w skrypcie lub w polu
  Parameter jako `adres|token`).
- **„Błąd połączenia: 401"** → serwer nie ma `SHARE_TOKEN` w `.env` (albo token
  się nie zgadza). Ustaw go i zrestartuj apkę:
  ```bash
  cd ~/gie-d
  grep -q '^SHARE_TOKEN=' .env || python3 -c "import secrets; print('SHARE_TOKEN='+secrets.token_urlsafe(24))" >> .env
  docker compose up -d --force-recreate app
  grep '^SHARE_TOKEN=' .env    # skopiuj wartość do pola Parameter widgetu
  ```
- **„Błąd połączenia"** (inny) → sprawdź adres BASE_URL i czy `https://…` otwiera
  się w Safari.
- iOS odświeża widgety własnym rytmem (~5–15 min) — żeby wymusić od razu:
  przytrzymaj widget → Edytuj → wyjdź, albo dodaj go ponownie.

## Uwagi
- Token wpisany w „Parameter" jest bezpieczniejszy niż w kodzie skryptu.
- Żeby unieważnić dostęp widgetu: zmień `SHARE_TOKEN` w `.env` i zrestartuj apkę.
- Certyfikat jest zaufany (Let's Encrypt przez sslip.io), więc Scriptable łączy
  się bez ostrzeżeń.
