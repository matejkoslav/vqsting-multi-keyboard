# Windows checklist — cross-platform patch

Vetva `feature/cross-platform`. Cieľ: overiť, že sa na Windows nič nerozbilo.

## Spustenie

1. `git fetch origin`
2. `git checkout feature/cross-platform`
3. `cd Smatanova/VQSTing`
4. `pip install -r requirements.txt`
5. `python main.py` → <http://127.0.0.1:5000>

Potrebuješ lokálne `mpv.exe` a `video/` (od Mateja).

## Skontroluj

| # | Krok | Očakávam |
|---|---|---|
| 1 | `admin` / `admin` → My test sessions → ExampleTest → Details | stránka sa načíta |
| 2 | Register → profil → Sessions list → heslo `eXamp1e` | prejde na training |
| 3 | Training: video sa spustí fullscreen v mpv | prehrá sa, po zavretí otázka |
| 4 | Test: video + hodnotenie 1–5 | prejde celý test |
| 5 | Ako admin → Export | otvorí sa `csv/`, súbor má dáta |
| 6 | Statistics | grafy sa načítajú |

## Výsledok

- Napíš do PR komentu **OK** alebo čo zlyhalo (+ screenshot).
- CI beží automaticky: zelená fajka = appka sa spustí na Linuxe aj Windows.
