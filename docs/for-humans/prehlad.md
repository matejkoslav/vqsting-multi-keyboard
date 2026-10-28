# VQSTing — krátky prehľad

## Čo to je
Web appka na **subjektívne hodnotenie kvality videa** (Video Quality Subjective Testing).
Nahrádza papierové hlasovanie: pustíš video → každý klikne známku 1–5 → všetko sa uloží do databázy → export do CSV + grafy.

Pôvodná appka je z diplomovky Lenky Smatanovej (ŽU FEIT, 2024).
Beží na **Windows aj Linux**, len lokálne (nie na internet).

## Čo na tom robíme my
Pôvodná appka zvládne **1 človeka na 1 PC**.
Náš cieľ: **viac ľudí na jednom PC naraz** — každý tester má vlastnú klávesnicu a klikne známku na svojej.

## Kto čo robí
- **Ja** — kód.
- **Patrik** — otestuje na Windows, či to funguje. Prípadne na PC u brata.

Viď `plan.md`.

## Ako sa to spustí
1. `cd Smatanova/VQSTing && pip install -r requirements.txt` (raz).
2. Linux: `./run.sh` · Windows: dvojklik na `run.bat`.
3. `http://127.0.0.1:5000` → login `admin` / `admin`.
4. `My test sessions` → pri teste **Group test** → pridať testérov, spárovať
   klávesnice, vyplniť vek a okuliare, `Start`.

Podrobný postup: `docs/for-humans/group-mode.md`.

## Ako to funguje pre testéra
Testér nemá účet ani heslo. Sadne si ku klávesnici, admin ju spáruje („stlač
ľubovoľnú klávesu") a od tej chvíle je jeho identitou. Vek a okuliare napíše
sám na svojej klávesnici. Všetci pozerajú to isté video na jednom monitore
a po ňom každý stlačí 1–5 na svojej klávesnici (alebo klikne myšou).

## Prečo sa to netestuje na VM
- VM ani Docker **nedokážu rozlíšiť viac klávesníc podľa USB portu** — a to je presne funkcia, ktorú pridávame.
- RDP do VM posiela vstup ako jednu klávesnicu. Test musí byť na **reálnom Windows HW**.

## Technicky (detaily v `docs/for-ai/`)
- Python + Flask, SQLite, SQLAlchemy, MPV prehrávač, Bootstrap.
- Pôvodná appka Windows-only: `mpv.exe`, cesty `video\nazov`, otváranie priečinka cez `start` — od 18.10.2026 beží aj na Linuxe (`platform_compat.py`).
