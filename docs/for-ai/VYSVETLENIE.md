# VQSTing – jednoduché vysvetlenie projektu

> Zdroj: `Smatanova_DP.pdf` (diplomovka, 59 strán, 2024) + `Smatanova_DP2.pdf` (5-stranový manuál / DP2) + kód v `Smatanova/VQSTing/`

## 1. Čo to je v jednej vete

**VQSTing = Video Quality Subjective Testing** – webová aplikácia, ktorá nahrádza papierové hlasovanie pri subjektívnom hodnotení kvality videa.

Autorka: **Lenka Smatanová, Bc., ŽU Žilina, FEIT, 2024**, vedúci: Ing. Miroslav Uhrina, PhD.

Namiesto: pustím video → napíšem známku na papier → niekto to prepisuje do Excelu (pomaly + chyby),
je to: pustím video → kliknem 1–5 vo webe → všetko sa samo uloží do databázy → export do CSV + grafy.

Určené **len na lokálny počítač v laboratóriu** (nie na internet), lebo videá sú veľké a slabý internet by zhoršil prehrávanie.

## 2. Prečo to vzniklo (teória v skratke)

Kvalita videa sa dá merať dvoma spôsobmi:

1. **Objektívne** – matematika (napr. odstup signálu od šumu). Rýchle, ale nezhoduje sa s tým, čo vidí človek.
2. **Subjektívne** – reálni ľudia pozerajú videá a dávajú známky 1–5. Pomalé, ale najspoľahlivejšie.

Normy na to: **ITU-R BT.500** (televízia) a **ITU-T P.910** (multimédiá – táto aplikácia sa riadi práve ňou).

Aplikácia podporuje 3 metódy z P.910:

| Metóda | Ako prebieha | Škála 1–5 |
|---|---|---|
| **ACR** – Absolute Category Rating | Prehrá sa 1 video → hneď hodnotíš kvalitu | 1 Zlá, 2 Slabá, 3 Prijateľná, 4 Dobrá, 5 Výborná |
| **ACR-HR** – ACR with Hidden Reference | Ako ACR, ale medzi videami je tajne schovaná aj originálna referencia. Potom sa známky prepočítajú vzorcom `DV = V(PVS) - V(REF) + 5`, aby sa odfiltroval vkus na obsah. | rovnaká ako ACR |
| **DCR** – Degradation Category Rating | Prehrá sa pár: originál → 3s šedá → pokazené video → hodnotíš, ako moc je pokazené | 1 Veľmi nepríjemné, 2 Nepríjemné, 3 Mierne nepríjemné, 4 Postrehnuteľné ale nerušiace, 5 Nepostrehnuteľné |

Pravidlá, ktoré appka dodržuje automaticky:
- pred testom je **tréning** (ukážka najlepšej / najhoršej kvality),
- každý účastník má **náhodné poradie** videí,
- **nikdy nejdú 2 videá s rovnakým záberom po sebe**,
- na oficiálny test treba aspoň **4 rôzne scény**, ideálne 24+ ľudí.

V diplomovke sú porovnané aj staré appky – AVRateNG, VQone, WEST, Tally. Všetky mali problém: buď už nefungujú (starý kód), alebo sa testy museli ručne písať do `config.txt`, alebo vedeli len 1 test naraz. VQSTing to rieši klikacím rozhraním.

## 3. Ako sa to spúšťa

Potrebuješ: **Windows + Python + cesty v PATH** (`python.exe` + `pip.exe`).

```
skupinovy_projekt/Smatanova/VQSTing/
  main.py          <- spustí Flask (3 riadky)
  VQSTing.bat      <- na toto 2x klikneš
  mpv.exe          <- prehrávač videí (netreba inštalovať)
  video/           <- sem sa dávajú videá + grey50.mp4 (nemazať!)
  csv/             <- sem padajú exporty (napr. ExampleTest.csv)
  instance/database.db <- SQLite databáza
  website/         <- celá webka (Flask)
```

`VQSTing.bat` robí:
1. `pip install flask flask_sqlalchemy flask_login plotly`
2. otvorí `http://127.0.0.1:5000`
3. spustí `python main.py`

Prvé spustenie je pomalé (inštaluje knižnice). Vypína sa `Ctrl+C` → `y`. Okno terminálu musí bežať celý čas.

Technológie:
- **Python + Flask** – web server,
- **SQLite + SQLAlchemy (ORM)** – databáza, nemusíš písať SQL,
- **Flask-Login** – prihlasovanie, `role 1 = účastník`, `role 10 = admin`,
- **Plotly** – koláčové / stĺpcové grafy v štatistikách,
- **MPV** – prehráva videá cez príkaz `mpv.exe --cursor-autohide=0 --osc=no --no-input-default-bindings --ontop --fs video1 video2`, čiže fullscreen, bez kurzora, bez ovládania, bez pauzy,
- **Bootstrap** – dizajn stránok.

## 4. Ako funguje program – dve role

```
ADMIN (role 10)                         ÚČASTNÍK (role 1)
registrácia na /admin                    registrácia cez "Register"
  |                                        |
vytvorí "test session"                   vyplní profil: pohlavie, vek (15+), okuliare
  |                                      (bez toho nemôže testovať)
nahádže videá do priečinkov              vyberie test zo zoznamu, zadá heslo
  |                                        |
nastaví tréningové limity                tréning -> ak netrafí interval, opakuje
  |                                        |
sleduje Details/Statistics/Export        oficiálny test -> ohodnotí všetko -> hotovo
```

### 4.1 Admin – vytvorenie testu

1. Registrácia admina: ručne dopíšeš `/admin` za URL, napr. `http://127.0.0.1:5000/admin`. Bežný user sa registruje cez menu.
2. `Create new test session`: zadáš **názov, metódu (acr / acr-hr / dcr), display, prostredie, heslo pre účastníkov** (min. 5 znakov).
3. Appka vytvorí priečinok `video/Tvoj_nazov/{test_seq, training, + ref_seq pre dcr/acr-hr}` a automaticky ho otvorí.
4. Nakopíruješ videá:
   - `training/` – 3–5 videí, názov ľubovoľný, iné zábery ako v teste. Pri DCR tam musí byť 1 referencia, ktorá sa pustí ku každému tréningovému videu.
   - `ref_seq/` – originály, 1 záber = 1 video, napr. `Basketball.avi`
   - `test_seq/` – pokazené verzie, 1 záber = viac videí, napr. `Basketball_H264_1M.mp4, Basketball_H264_3M.mp4`
   - **Bez medzier a divných znakov v názvoch!**
5. Zadáš **počet úvodných znakov na rozlíšenie sekvencií** (default 5). Príklad z práce:
   - `Basketball`, `Balance`, `Balloon` → treba 7 znakov, inak sa ti pri 6 znakoch zleje `Basket...` a pri 2 znakoch (`Ba`) všetko do jednej kopy.
   - Kód to robí v `views.py: insert_sequences()` – vezme `file[0:letters]` a hľadá `Video.name LIKE 'pattern%'`.
6. `set-training`: ku každému tréningovému videu zadáš `min` a `max` (čo musí účastník trafiť) + pri DCR vyberieš, ktoré je referencia.
7. Hotovo. V `My test sessions` vidíš test + počet dokončených hodnotení. Tlačidlá:
   - **Details** – zoznam videí po sekvenciách + tréningové limity (dajú sa editovať),
   - **Statistics** – počet ľudí, vek min/max/priemer, grafy pohlavie / okuliare / vek,
   - **Export** – vyrobí `csv/Tvoj_nazov.csv`,
   - **Delete** – zmaže test + hodnotenia z DB (priečinok s videami ostane). Edit videí po vytvorení **nie je možný** – zámerne, aby sa nepomiešali hodnotenia.

### 4.2 Účastník – priebeh testu

1. `Register` → `Profile` → vyplní pohlavie, vek, okuliare.
2. `Test sessions list` → nájde test podľa názvu + autora → zadá heslo.
3. **Tréning** (`video.py: training_play()`): video sa pustí v MPV na celú obrazovku. Po skončení web ukáže 5 tlačidiel (dá sa aj klávesami 1–5, hodí sa bezdrôtová numerická klávesnica pri sedení ďaleko od monitora). Máš 10 sekúnd, potom to samo skočí ďalej. Ak nedáš nič, uloží sa `0` (= `n/a` v CSV). Ak netrafíš adminom zadaný interval, ideš na `repeat-test.html` a opakuješ od začiatku.
4. **Oficiálny test** (`video.py: start()` + `video_play()`):
   - appka vygeneruje náhodné poradie: urobí pole `[1,1,1,2,2,2...]` (ID záberu × počet videí), zamieša, prehádže tak, aby neboli rovnaké vedľa seba, potom zamieša videá vnútri sekvencií a pospája do finálneho `order = [1,9,5,8,...]` (ID videí).
   - poradie + `current_id` (kde si skončil) sa uloží do tabuľky `Order`, takže po výpadku pokračuješ tam, kde si prestal.
   - pri ACR: pustí 1 video. Pri DCR: pustí `referencia + grey50.mp4 + testované` ako jeden playlist.
   - po každom videu hodnotenie 1–5, hneď zápis do `Valuation`.
   - po poslednom: zápis do `Completed` + stránka `finished.html`. Test už druhýkrát nespustíš.
5. Šedá obrazovka medzi videami je súbor `video/grey50.mp4` (3s pri DCR, 10s výzva na hodnotenie pri ACR).

## 5. Databáza (9 tabuliek, SQLite)

Zjednodušene (`website/models.py`, schéma obr. 3.12 v DP):

- `User(id, username, password_hash, role)` – 1 = účastník, 10 = admin
- `Detail(id_user, gender, age, glasses)` – profil účastníka 1:1
- `Session(id, name, test_method, display, surrounding, password, id_user, ok)` – jedna testovacia relácia, `ok=False` = zle naplnená (červená v zozname)
- `Sequence(id, id_session)` – jeden záber (napr. všetko čo začína na `Basketb...`)
- `Video(id, id_sequence, name, reference)` – konkrétny súbor, `reference True/False`
- `Training(id_session, name, min, max, ref)` – tréningové videá + očakávaný interval
- `Order(id_session, id_user, order="1,9,5,...", current_id)` – náhodné poradie pre daného človeka
- `Valuation(id_user, id_video, value)` – jedna známka (0 = nezadané)
- `Completed(id_user, id_session, date)` – kto dokončil, blokuje opakovaný vstup

V demo DB je `admin/admin`, test `ExampleTest (dcr)` a 9 userov `exampleUser1..9`. Export vyzerá takto (`csv/ExampleTest.csv`):

```
ExampleTest
dcr,Samsung U24E590D UHD

Basketball_H264_1M.mp4,1,2,1,1,2,1,1,1,1
Beauty_H264_5M.mp4,4,4,4,4,5,4,4,4,4
...
```

Riadok = video, stĺpce = známky jednotlivých ľudí, `n/a` = nestihol ohodnotiť.

## 6. Štruktúra kódu (kde čo hľadať)

- `website/__init__.py` – `create_app()`, registrácia 4 blueprintov, `role_required()`, helpery pre šablóny (`get_age_range`, `get_valuations`...)
- `website/auth.py` – `login, register, profile, profile-update, logout` (hash `pbkdf2`)
- `website/admin.py` – `register_admin (/admin), delete-session, delete-user, delete-valuation`
- `website/views.py` – `create-test, add-videos, insert-sequences, set-training, details, statistics (Plotly pie+bar), sessions-list`
- `website/video.py` – `training, training_play (mpv), valuation_training, test/start (generovanie poradia), video_play (mpv), valuation, export (csv.writer)`
- `website/templates/*.html` – `test.html` (5 tlačidiel + JS 10s timer + klávesy 1–5), `training.html, start.html, repeat-test.html, statistics.html, session-details.html...`
- `website/static/style.css, img/Logo.png`

## 7. Obmedzenia / na čo si dať pozor

1. **Len Windows** – cesty sú `video\\nazov\\...`, otváranie priečinka cez `subprocess.call(["start", ...])`, prehrávač `mpv.exe`.
2. **Len 1 tester naraz na 1 PC** – v diplomovke je to priznané ako hlavná nevýhoda do budúcna (papierovo vie pozerať skupina).
3. Test po vytvorení **nevieš editovať**, len zmazať a vytvoriť znova.
4. Názvy videí musia mať dosť dlhý spoločný prefix, inak sa sekvencie zlejú – vždy skontroluj v Details.
5. Heslá admina aj testov sú v DB, user heslá hashované, testovacie heslá v plaintexte.
6. `SECRET_KEY` a `REMEMBER_COOKIE_DURATION` sú natvrdo v kóde – OK na lab, nie na internet.

## 8. Najrýchlejší postup na vyskúšanie

1. Dvojklik `VQSTing.bat` → počkaj na `http://127.0.0.1:5000`.
2. Prihlás sa `admin / admin` → `My test sessions` → `Details / Statistics / Export` pri `ExampleTest`.
3. Odhlás sa → registruj nového usera → vyplň profil → `Test sessions list` → heslo ti povie admin → skús tréning + test.
4. Pozri `csv/` a `instance/database.db` (otvoríš napr. cez DB Browser for SQLite).

---
*Vygenerované z DP + DP2 + kódu 13.10.2026. Ak chceš, viem to skrátiť na 1-stranový ťahák alebo preložiť do angličtiny.*
