# TODO — Matej

Stav: 24.10.2026 · `main` = `0321b4d` · CI na `main` zelené

## 0. Windows — hneď (Patrik, ~20 min)
Cieľ: zistiť, či Windows rozlíši dve klávesnice.

- [ ] `git checkout feature/windows-raw-input-probe`
- [ ] `python Smatanova/VQSTing/tools/windows_keyboard_probe.py`
- [ ] stlačiť 1 klávesu na prvej, 1 na druhej, potom Ctrl+C
- [ ] poslať celý výstup Matejovi
- Done: dva rôzne `id=`, alebo jasné „len jedno zariadenie"

Potom appka:
- [ ] `git checkout main`
- [ ] prejsť `docs/for-humans/windows-checklist.md` (riadok s vetvou je starý → `main`)

## 1. Linux identity — dokončiť (~15 min)
- [ ] manuálny test 2 klávesníc na `main` (interná + KILO BT) → `/keyboards` 2 riadky
- [ ] po potvrdení zmergovať `feature/windows-raw-input-probe` do `main`
- [x] CI na `main` zelené (24.10.)

## 2. Users — premyslieť ešte (blokuje kód)
👉 Návrhy s postupom: **[USERS-navrhy.md](USERS-navrhy.md)**

Reálne nás zaujíma až na dáta: **okuliare, vek** (prípadne pohlavie). Meno asi netreba.

- [ ] vybrať návrh A / B / C
- [ ] meno: reálne, alebo len „Tester 1"
- [ ] demografia: vek + okuliare (+ pohlavie)? Kto vypĺňa?
- [ ] všetci pozerajú to isté video na jednom monitore?
- [ ] single-tester režim nechať, alebo nahradiť?
- [ ] max počet testerov

## 3. Group mode — jadro (~2–3 dni, po rozhodnutí)
- [ ] model: slot testera + väzba na zariadenie klávesnice
- [ ] jeden order pre všetkých, kolo: video → hlasy → ďalšie
- [ ] admin: vytvorenie slotov + demografia
- [ ] párovanie: „stlač klávesu" → uložiť zariadenie
- [ ] listener: event log (zariadenie, klávesa, čas) — Linux
- [ ] Flask: event → slot → hlas 1–5
- [ ] obrazovka hlasovania: veľká, kto už hlasoval, zmena hlasu, timeout
- [ ] automaticky ďalšie video, keď majú všetci
- [ ] export CSV: riadok = video, stĺpce = testeri + demografia
- [ ] smoke test group módu + CI

## 4. Windows group mode (~1–2 dni, po probe)
- [ ] Raw Input listener s rovnakým IPC
- [ ] test 2 klávesníc na Windows
- [ ] fallback, ak Windows zlúči zariadenia

## 5. Odovzdanie
- [ ] aktualizovať `progress.md`, `prehlad.md`, `NAVOD.md`
- [ ] elaborát 5–7 strán (ideálne do Vianoc)
- [ ] prezentácia 5–7 min
- [ ] pondelok 14:00 Uhrín: potvrdiť group mode + rozsah

## 6. Hygiena
- [ ] `info od uhrinu.md` — commitnúť alebo presunúť do `docs/`
- [ ] `vm_start.md` — commitnúť alebo zmazať
- [ ] zavrieť registráciu admina (`role=10`)
- [ ] zmazať zmergované vetvy
