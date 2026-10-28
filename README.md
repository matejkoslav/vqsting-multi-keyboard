# VQSTing — multi-keyboard

Školský skupinový projekt. Rozširujeme appku **VQSTing** (subjektívne hodnotenie kvality videa; Python + Flask)
o novú funkciu: **viac testerov na jednom PC, každý s vlastnou klávesnicou**.

- Pôvodná appka: Lenka Smatanová, ŽU FEIT (2024)
- Náš cieľ: 1 PC + N klávesníc → každý tester hodnotí na svojej

> Appka beží na **Windows aj Linux**. Viac testerov na jednom PC funguje na oboch:
> Linux číta `/dev/input`, Windows Raw Input, zvyšok appky je spoločný.
>
> Ako spustiť skupinový test: **[docs/for-humans/group-mode.md](docs/for-humans/group-mode.md)**.

## 👉 Začni tu

- **[NAVOD.md](NAVOD.md)** — ako si projekt stiahnuť, spustiť a ako prispievať kódom.
- **[docs/](docs/)** — prehľad projektu, plán a technické detaily.

## Čo nie je v repe

Testovacie videá (~581 MB) a prehrávač `mpv.exe` (~104 MB) zámerne nie sú v gite — treba si ich vyžiadať
zvlášť. Detaily v [NAVOD.md](NAVOD.md), bod 6.
