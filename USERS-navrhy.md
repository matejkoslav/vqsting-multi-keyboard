# Users — ako spustiť test s viacerými klávesnicami (návrhy na vybranie)

Cieľ: viac ľudí na jednom PC hodnotí naraz, každý svojou klávesnicou.
Reálne nás zaujíma len dáta: **okuliare, vek** (prípadne pohlavie). Meno asi netreba.

Toto je na rozmyslenie, vyberieme neskôr. Nižšie tri návrhy.

## Čo už appka vie

- admin zakladá session, nahráva videá, exportuje CSV a pozerá štatistiky
- testér má účet (meno + heslo) a profil (pohlavie, vek, okuliare)
- video hrá mpv na monitore PC; prehliadač je len ovládač
- klávesnice sa dajú rozlíšiť (Linux PoC, stránka `/keyboards`)

## Návrh A — Sloty (odporúčam)

**Pred testom (admin, ~1 min):**
1. Admin otvorí session a klikne „Skupinový test“.
2. Nastaví 3 sloty: Tester 1, 2, 3. Pri každom vek, okuliare (a pohlavie).
3. Appka vyzve: „Stlač Enter na klávesnici Testera 1“, to isté pre 2 a 3.
   Tabuľka ukáže zelenú fajku pri každom.

**Počas testu:**
4. Testéri si sadnú. Admin klikne „Štart“.
5. Na monitore beží video. Všetci pozerajú to isté.
6. Po videu sa zobrazí veľká škála. Každý stlačí 1–5 na svojej klávesnici.
7. Obrazovka ukáže, kto už hlasoval. Keď majú všetci, ide ďalšie video.
8. Na konci admin exportuje CSV. Stĺpce = testeri, hlavička = demografia.

- **Plus:** testéri sa neprihlasujú, nemajú heslá ani účty. Rýchly štart.
- **Mínus:** demografiu vypĺňa admin; testér nemá trvalý účet.

## Návrh B — Účty + párovanie

- Testeri majú účty a profily ako dnes.
- Pred testom sa každý raz prihlási a stlačí klávesu na svojej klávesnici.
  Appka účet spáruje so zariadením a odhlási ho.
- Potom test prebieha ako A.

- **Plus:** história, meno, štatistiky po osobách.
- **Mínus:** heslá, viac krokov, viac kódu.

## Návrh C — Zero setup

- Admin len spustí test. Appka sama nájde klávesnice a vytvorí sloty „Zariadenie 1..N“.
- Po teste admin priradí mená a demografiu, alebo nie.

- **Plus:** najrýchlejší štart, najmenej kódu.
- **Mínus:** riziko zámeny slotov; demografia až po teste.

## Spoločný priebeh hlasovania (všetky návrhy)

```text
┌────────────────────────────────────────────────┐
│  Video 3 / 12                    Hlasujte 1 – 5│
│                                                │
│   Tester 1  ✓                                  │
│   Tester 2  ✓                                  │
│   Tester 3  … čaká sa                          │
│                                                │
│  1 EXCELLENT   2 GOOD   3 FAIR   4 POOR   5 BAD│
└────────────────────────────────────────────────┘
```

- každý stlačí číslo na svojej klávesnici
- obrazovka ukáže fajky, nie hodnoty — hlas ostatných neovplyvní
- keď majú všetci, kolo sa zatvorí → ďalšie video
- chýbajúci hlas: po 30 s sa kolo uzavrie a do CSV ide „n/a“

## Otázky na rozhodnutie

1. Meno: reálne, alebo len „Tester 1“?
2. Demografia: vek + okuliare (+ pohlavie)? Kto vypĺňa?
3. Všetci pozerajú to isté video na jednom monitore?
4. Nechať aj single-tester režim?
5. Max počet testerov?

## Čo z toho vyplýva (technicky) — len pre neskôr

- tester = slot bez hesla; nová tabuľka `Subject` + väzba na zariadenie klávesnice
- `Valuation` dostane `id_subject` (`id_user` zostane pre starý režim)
- group run: jeden order pre všetkých, index aktuálneho videa, stav
- listener: event log (zariadenie, klávesa, čas) → Flask
