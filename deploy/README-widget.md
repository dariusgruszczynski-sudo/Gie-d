# Widget na ekran główny iPhone (żywy podgląd konta)

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
- **Mały** widget: łączny stan konta + dzienny % + wynik netto.
- **Średni** widget: dodatkowo wiersze obu silników (Akcje US / Krypto) ze
  stanem (aktywny / wstrzymany / STOP) i temperaturą rynku (hossa/bessa).

## Uwagi
- Token wpisany w „Parameter" jest bezpieczniejszy niż w kodzie skryptu.
- Żeby unieważnić dostęp widgetu: zmień `SHARE_TOKEN` w `.env` i zrestartuj apkę.
- Certyfikat jest zaufany (Let's Encrypt przez sslip.io), więc Scriptable łączy
  się bez ostrzeżeń.
