# Group mode — kontext pre AI agentov

> Posledná aktualizácia: 28.10.2026 · staví na `main` = `3054f6b`
> Tento dokument je **jediný zdroj pravdy** pre prácu na group mode.
> Ak niečo v kóde odporuje tomuto dokumentu, dokument vyhráva — alebo sa ozvi
> rodičovi (parent agentovi), nie si to domýšľaj.

## 1. Cieľ v jednej vete

Na **jednom PC s jedným monitorom** hodnotí **N testérov naraz**, každý na
**svojej fyzickej klávesnici**; klávesnica je identita testéra, netreba žiadne
prihlasovanie ani účty.

## 2. Zamknuté rozhodnutia (nemení sa bez schválenia)

| # | Rozhodnutie |
|---|---|
| D1 | Účastnícke účty (`User` role 1) **sa rušia**. Login ostáva len pre admina (role 10). Každý test je *group run* s N ≥ 1 testermi. |
| D2 | Testér vyplní vek a okuliare **sám na svojej klávesnici**; admin má fallback formulár myšou. |
| D3 | Video prehráva **mpv fullscreen** ako dnes. Split screen je len na hlasovacej obrazovke. |
| D4 | Hlas: **prvý stisk platí** (možno zmeniť do zatvorenia kola), kolo sa zatvára po **9 s** alebo hneď keď hlasovali všetci. **9 s sa nesmie zmeniť.** |
| D5 | Hlasovať sa dá **klávesnicou aj myšou**. Myš nemá identitu: najprv klik na hlavičku stĺpca (arm), potom klik na číslo. |
| D6 | Layout: **N stĺpcov vedľa seba**, max **4** testéri, škála 5→1 zvisle. |
| D7 | Tréning: admin môže prehrať tréningový playlist **raz pre všetkých**, bez kontroly intervalu. |
| D8 | Poradie videí je **jedno spoločné** pre celú skupinu. |
| D9 | Vstup do group módu: tlačidlo **Group test** v tabuľke `My test sessions`. |
| D10 | Nové tabuľky namiesto migrácie starých (`db.create_all()` ich vytvorí). Staré tabuľky v DB ostanú, ale kód ich nepoužíva. |

## 3. Čo sa NESMIE meniť

- **9 sekúnd** na hlasovanie (`test.html` má `9000` ms; v group mode `ROUND_SECONDS = 9`).
- **Škály** a ich popisy: ACR `EXCELLENT / GOOD / FAIR / POOR / BAD`,
  DCR `IMPERCEPTIBLE / PERCEPTIBLE BUT NOT ANNOYING / SLIGHTLY ANNOYING / ANNOYING / VERY ANNOYING`.
- **mpv príkaz** v `platform_compat.play_videos()` (`--fs --ontop --osc=no …`).
- **Generovanie poradia** videí (algoritmus v `website/video.py: start()`) — skopíruj, neprepisuj.
- **Štruktúra CSV**: prvý riadok názov testu, druhý `metóda,display`, tretí prázdny, potom dáta.
- **`grey50.mp4`** medzi referenciou a testovaným videom pri DCR.
- Verejné API `/keyboards` a `/keyboards/state` — group mode ho používa.

## 4. Doménový model

Tri nové tabuľky v `website/models.py`:

```python
class GroupRun(db.Model):
    id              # PK
    id_session      # FK session.id, unique-ish (jeden run na session)
    order           # str, čiarkami oddelené id videí (rovnaký formát ako Order.order)
    current_id      # int, index aktuálneho videa v order
    phase           # "setup" | "running" | "finished"
    round_started   # float, epoch sekundy začiatku hlasovania (NULL pred štartom)
    pairing_seat    # int | NULL, stĺpec, ktorý čaká na stlačenie klávesy
    created         # DateTime default now

class Tester(db.Model):
    id              # PK
    id_group_run    # FK group_run.id
    seat            # int 1..4
    keyboard_id     # str | NULL, stabilné ID zariadenia ("linux:…" / "win:…")
    keyboard_name   # str | NULL, ľudský názov na zobrazenie
    age             # int | NULL
    glasses         # bool | NULL
    gender          # str(1) | NULL
    last_seq        # int, koľký event z listenera už server spracoval

class GroupVote(db.Model):
    id              # PK
    id_group_run    # FK group_run.id
    id_tester       # FK tester.id
    id_video        # FK video.id
    value           # int 1..5
```

Zrušené modely: `Detail`, `Order`, `Valuation`, `Completed`.
`User` ostáva (admin login), `Session`, `Sequence`, `Video`, `Training` ostávajú.

**Prečo nové tabuľky:** `db.create_all()` nevie `ALTER TABLE`. Commitnutá
`instance/database.db` sa tak nemusí migrovať a nič sa nerozbije.

## 5. Kontrakt listenera — JSON

Cesta (rieši `state_paths.py`, importuje listener aj Flask):

- Linux: `/run/vqsting/keyboards.json`
- Windows: `%LOCALAPPDATA%\vqsting\keyboards.json`

```json
{
  "ts": 1760000000.123,
  "platform": "linux",
  "seq": 142,
  "devices": [
    {
      "id": "linux:usb-0000:00:14.0-3/input0",
      "name": "AT Translated Set 2 keyboard",
      "node": "event3",
      "seq": 139,
      "key": "Enter",
      "at": 1759999998.9
    }
  ],
  "events": [
    {"seq": 141, "at": 1759999999.0, "device_id": "linux:…", "key": "2"},
    {"seq": 142, "at": 1759999999.1, "device_id": "linux:…", "key": "3"}
  ]
}
```

Pravidlá (platia pre Linux aj Windows, musia byť **identické**):

1. `seq` je **jeden globálny** čítač pre celý proces, rastie o 1 pri každom
   stlačení (key-down). Nikdy sa neresetuje (okrem reštartu listenera).
2. `events` je **krúžkový buffer posledných 64 eventov** (staršie sa zahadzujú).
   Bez neho sa nedá napísať vek dvoma rýchlymi stlačeniami.
3. `devices[].seq` / `key` / `at` = posledný event daného zariadenia (`null` ak žiadny).
4. `key` je normalizovaný názov: `"1"`…`"0"` pre číslice, `"Enter"`,
   `"Backspace"`, inak ľubovoľný krátky text (`"LEFT SHIFT"`, `"code 42"`).
   **Číslice musia byť presne `"1"`…`"5"`** — na tom stojí hlasovanie.
   Emituj len key-down (na Linuxe `value == 1`, na Windows `Flags & RI_KEY_BREAK == 0`).
5. `id` je **stabilné** ID zariadenia, prefixované platformou:
   - Linux: `"linux:" + (uniq or phys or node)`
   - Windows: `"win:" + instancia z `RIDI_DEVICENAME` (`7&2f&0&0000`)
6. Celý súbor sa zapisuje **atomicky** (`tmp` + `os.replace`).
7. Listener zapisuje aj `listener.pid` vedľa stavu a **zmaže ho pri ukončení**.

## 6. HTTP tok (group mode)

Všetko pod `@login_required @role_required(10)` (admin), blueprint `group`,
`url_prefix='/group'`.

| Metóda | Cesta | Význam |
|---|---|---|
| GET | `/group/<id_session>` | setup: stĺpce testérov, párovanie, vek/okuliare, tlačidlá *Tréning*, *Štart*, *Reset* |
| POST | `/group/<id_session>/tester` | `seat, age, glasses, gender` — upsert testéra |
| POST | `/group/<id_session>/pair` | `seat` — ďalšia nová klávesa sa priradí tomuto stĺpcu |
| POST | `/group/<id_session>/add` | pridá ďalší stĺpec (max 4) |
| POST | `/group/<id_session>/start` | skontroluje párovanie a vek, vygeneruje order, `phase=running`, `current_id=0` |
| GET | `/group/<id_session>/state` | JSON pre frontend (pozri nižšie) |
| POST | `/group/<id_session>/vote` | `seat, value (1..5)` — hlas myšou |
| GET | `/group/<id_session>/play` | zahrá video aktuálneho kola cez mpv (blokuje), nastaví `round_started`, vráti hlasovaciu stránku |
| POST | `/group/<id_session>/next` | zavrie kolo, `current_id += 1`; redirect na `/play` alebo `/results` |
| GET | `/group/<id_session>/results` | tabuľka video × testér + demografia + *Export CSV* + *Reset* |
| GET | `/group/<id_session>/export` | zapíše `csv/<nazov_session>.csv` (rovnaký tvar ako dnes) |
| POST | `/group/<id_session>/training` | prehrá tréningový playlist raz, bez validácie |
| POST | `/group/<id_session>/reset` | zmaže run + hlasy, `phase=setup` |

### `GET /state` — presný tvar

```json
{
  "phase": "running",
  "listener": true,
  "park": {"id": 1, "current": 3, "total": 12, "seconds_left": 6.4, "round_open": true},
  "scale": {"method": "dcr", "labels": ["IMPERCEPTIBLE", "…"]},
  "testers": [
    {"seat": 1, "keyboard_id": "linux:…", "keyboard_name": "AT Translated Set 2",
     "age": 23, "glasses": true, "gender": "m", "vote": 4, "last_seq": 142}
  ],
  "events": [{"seq": 141, "at": 1760000000.0, "device_id": "linux:…", "key": "2"}],
  "pairing_seat": null
}
```

`events` = **len nové** eventy od `?since=<seq>` (default `0`, frontend si drží
kurzor). `testers[].vote` = aktuálny hlas v otvorenom kole (inak posledný).

### Spracovanie eventov (robí server v `GET /state`, nie JS)

Pri každom volaní `/state`:

1. Prečítaj `state_paths.state_file()`. Ak sa nedá prečítať → `listener: false`, zvyšok ako posledný stav.
2. Ak `pairing_seat` nie je NULL: nájdi prvý event s `seq > <max last_seq všetkých testérov>`
   od zariadenia, ktoré ešte nikomu nepatrí → priraď ho testérovi, nastav
   `keyboard_id`, `keyboard_name`, `last_seq = seq`, zruš `pairing_seat`.
3. Ak `phase == "running"` a kolo je otvorené: pre každý event s
   `seq > tester.last_seq`, kde `event.device_id == tester.keyboard_id` a
   `event.key in {"1","2","3","4","5"}` → upsert `GroupVote` (posledná hodnota
   vyhráva). Vždy posuň `tester.last_seq` na `seq` (aj keď klávesa nie je číslica).
4. Nikdy nepočítaj eventy z času **pred** `round_started` (pri štarte kola sa
   `last_seq` všetkých testérov nastaví na aktuálny globálny `seq`).

**Kolo je otvorené**, keď `time.time() < round_started + 9` **a** aspoň jeden
testér ešte nemá hlas. Keď sa zavrie a niekto nehlasoval, **žiadny riadok sa
nezapisuje** — v exporte bude `n/a`.

### Frontend

Jeden `group_vote.html` + `group_setup.html` + `group_results.html`, žiadny
framework, `fetch` + `setInterval` 500 ms, Bootstrap z CDN ako ostatné šablóny.

Hlasovacia stránka:

- hlavička `Video <current+1> / <total>` + odpočet z `seconds_left`
- N stĺpcov: meno `Tester N`, názov klávesnice, vek/okuliare, stav `✓ hlasoval` / `… čaká sa`
- v každom stĺpci 5 riadkov 5→1 s popisom škály (rovnaké texty ako `test.html`)
- klik na hlavičku = arm (modrý rám), klik na číslo = hlas pre ten stĺpec
- klávesa `1`–`5` na klávesnici testéra = hlas pre jeho stĺpec
- keď `round_open == false` → **zastav polling** a o 1 s choď na `POST /next`
- `since` kurzor sa posiela v `?since=`

Setup stránka:

- stĺpce s tlačidlom *Priradiť* (arm) a textom „stlač klávesu na svojej klávesnici“
- po priradení sa v stĺpci zobrazí názov klávesnice
- vek: testér píše číslice na svojej klávesnici (frontend skladá reťazec z `events`),
  `Backspace` maže, `Enter` potvrdí → `POST /tester`
- okuliare: po potvrdení veku `1` = áno, `2` = nie
- admin fallback: v stĺpci sú aj obyčajné `<input>` prvky (vek, okuliare), fungujú myšou
- *Štart* je aktívny, keď majú všetci testéri `keyboard_id` aj `age`

## 7. Export CSV

Rovnaký tvar ako dnes, len stĺpce sú testéri a pribudne hlavička s demografiou:

```csv
ExampleTest
dcr,Samsung U24E590D UHD

,Tester 1,Tester 2,Tester 3
,23,31,22
,ano,nie,ano
Basketball_H264_1M.mp4,2,2,1
Beauty_AV1_1M.mp4,4,5,4
```

Video v riadku, testér v stĺpci, `n/a` = nedostal hlas.

## 8. Čo sa maže (Linux vetva)

- `website/auth.py`: preč `register`, `profile`, `profile_update`; ostáva `login`, `logout`.
- `website/video.py`: preč staré `training*`, `test/start`, `video_play`,
  `valuation_test`, `export`. Poradie generuj v novom module — **skopíruj algoritmus**.
- `website/views.py`: preč `sessions_list` a jinja helpery postavené na
  `Completed`/`Detail`; `statistics` → redirect na group results.
- `website/admin.py`: preč `delete_user`, `delete_valuation`.
- `website/__init__.py`: preč `get_user_completed`, `get_completed_date`,
  `get_all_participants`, `get_age_range`, `get_valuations`.
- šablóny: `register.html`, `profile*.html`, `sessions-list.html`, `test.html`,
  `training.html`, `start.html`, `repeat-test.html`, `finished.html`, `statistics.html`.
- `home.html` a `base.html`: odkazy na zrušené stránky nahraď (Home, Test sessions, Keyboards).

## 9. Git pravidlá pre agentov

- Pracuj **len** vo svojom worktree. Nikdy nespúšťaj `git checkout`/`merge`/`rebase`
  na inej vetve, nikdy nepushuj do `main`.
- Commituj **po malých častiach**, jedna vec = jeden commit, formát
  `<emoji> <typ>: <anglický imperatív>` (napr. `✨ feat: add group voting screen`).
- Pred každým commitom, ktorý sa dotýka kódu: `python tests/smoke_test.py` v `Smatanova/VQSTing`.
- Pushni svoju vetvu na `origin`. **Neotváraj PR, nemerguj.**
- Keď niečo v zadaní chýba alebo si nie si istý, **zastav a spýtaj sa**
  (kontaktuj rodičovský agent) — nedomýšľaj si.

## 10. Známe limity (do elaborátu)

- Dve **identické** klávesnice bez sériového čísla na jednom rozbočovači môžu
  dostať rovnaké `id` → splynú do jedného testéra.
- PS/2 klávesnice na Windows nemajú použiteľnú inštančnú cestu.
- Windows: Raw Input overený len manuálne na reálnom HW (CI runner nemá 2 klávesnice).
- Beží len lokálne (localhost), žiadna autentifikácia testérov.
