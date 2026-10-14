# VQSTing — krátky prehľad

## Čo to je
Web appka na **subjektívne hodnotenie kvality videa** (Video Quality Subjective Testing).
Nahrádza papierové hlasovanie: pustíš video → každý klikne známku 1–5 → všetko sa uloží do databázy → export do CSV + grafy.

Pôvodná appka je z diplomovky Lenky Smatanovej (ŽU FEIT, 2024).
Je **len na Windows** a len na lokálny počítač (nie na internet).

## Čo na tom robíme my
Pôvodná appka zvládne **1 človeka na 1 PC**.
Náš cieľ: **viac ľudí na jednom PC naraz** — každý tester má vlastnú klávesnicu a klikne známku na svojej.

## Kto čo robí
- **Ja** — kód.
- **Patrik** — otestuje na Windows, či to funguje. Prípadne na PC u brata.

Viď `plan.md`.

## Ako sa to spustí (na Windows)
1. Dvojklik na `VQSTing.bat` (prvé spustenie je pomalé — inštaluje knižnice).
2. Otvorí sa `http://127.0.0.1:5000`.
3. Login `admin / admin` → `My test sessions` → `ExampleTest`.
4. Nový účastník: `Register` → vyplní profil → vyberie test → zadá heslo od admina.

## Prečo sa to netestuje na VM
- VM ani Docker **nedokážu rozlíšiť viac klávesníc podľa USB portu** — a to je presne funkcia, ktorú pridávame.
- RDP do VM posiela vstup ako jednu klávesnicu. Test musí byť na **reálnom Windows HW**.

## Technicky (detaily v `docs/for-ai/`)
- Python + Flask, SQLite, SQLAlchemy, MPV prehrávač, Bootstrap.
- Windows-only: `mpv.exe`, cesty `video\nazov`, otváranie priečinka cez `start`.
