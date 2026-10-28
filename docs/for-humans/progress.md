# Progress — living list

Aktualizované: 28.10.2026 · `main` = `71bc32d` · group mode aj Windows listener zmergované

## ✅ Hotové (28.10.2026): group mode — N testérov na jednom PC
- [x] účastnícke účty zrušené: testér = stĺpec v behu testu, nie `User`
- [x] nové tabuľky `GroupRun`, `Tester`, `GroupVote` (bez migrácie starých)
- [x] párovanie klávesníc („stlač klávesu"), demografia na vlastnej klávesnici
- [x] hlasovanie: klávesa 1–5 alebo jeden klik myšou, 9 s okno, hlas z aktuálneho kola
- [x] spoločné poradie videí, results tabuľka, export CSV s demografiou
- [x] Linux listener posiela `seq` + 64-eventový buffer + stabilné `id` zariadenia
- [x] **Windows listener (Raw Input)** — overený na reálnom HW: rozlíši dve klávesnice
- [x] pid lifecycle: mazanie pri ukončení, `stop.sh` overí proces, guard proti druhému listeneru
- [x] smoke test je izolovaný (nezráža ho rozrobený beh v `database.db`)
- [x] CI zelené na Ubuntu aj Windows
- [x] dokumentácia: `group-mode.md`, `windows-test.md`, `CONTEXT-group-mode.md`, `GLOSSARY.md`, 2 ADR

Aktualizované: 22.10.2026 · branch `feature/keyboard-identity` — pushnuté, čaká CI

## ✅ Hotové (18.10.2026)
- Cross-platform patch (`platform_compat.py`) → appka beží na Linuxe aj Windows
- Smoke test `tests/smoke_test.py` + CI (Ubuntu + Windows) zelené
- Windows checklist pre Patrika

## ✅ Hotové (21.10.2026): rozlíšenie klávesníc — Linux proof of concept
Appka vie, **z ktorej fyzickej klávesnice** prišlo stlačenie, a zobrazuje to naživo.

- [x] `tools/keyboard_listener.py` — samostatný proces; root "opener" posielá len
      file deskriptory, čítanie beží ako prihlásený user (žiadne trvalé práva,
      žiadny ACL — prístup zaniká so skončením procesu)
- [x] `website/keyboards.py` — Flask číta len `/run/vqsting/keyboards.json`
- [x] stránka `/keyboards` (len admin) — tabuľka klávesníc + posledná klávesa, refresh 1 s
- [x] `run.sh` / `stop.sh` — spustí/vypne listener + appku spolu
- [x] otestované s 2 klávesnicami: `AT Translated Set 2` (event3) vs `KILO V2 BT1` (event18)
- [x] reconnect BT klávesnice sa sám zachytí (~5 s rescan)
- [x] myš (Logitech G305) sa správne odfiltruje — `REL_X/REL_Y` kontrola
- [x] Windows CI ostáva zelené (listener je Linux-only, Flask k `/dev/input` nepristupuje)

**Funkcionalita appky nezmenená** — len pridané súbory + 2 routes + 1 link v menu.

## ✅ Hotové (22.10.2026): hardening + Windows guard
- [x] `keyboards.state()` sa na ne-Linuxe vráti hneď — na Windows sa už nečíta
      `/run` a nevolá `os.kill(pid, 0)` (to by proces zabilo, nie skontrolovalo)
- [x] `_drop_privileges()` v listeneri: `chown` reconnect socketu na usera +
      `setgroups([])` pred `setgid/setuid` — dieťa po `pkexec` už nedrží group `root`
- [x] smoke test: chýbajúci/poškodený JSON, živý listener, simulovaný Windows,
      poradie `setgroups → setgid → setuid` a vlastníctvo socketu
- [x] red-green overené: bez fixu testy padnú, s fixom `exit=0`
- [x] `run.sh` posiela pkexecu absolútnu cestu — pkexec mení CWD na `/root`,
      relatívna cesta `tools/keyboard_listener.py` preto nefungovala
- [x] listener sa po fixe spustil a otvoril `event3` cez `open.sock` — hardening OK
- [ ] **manuálny test:** doplniť druhú (KILO BT) klávesnicu a overiť 2 riadky

## ⏭️ Next actionable steps
Všetko z pôvodného zoznamu je hotové (28.10.2026):
druhá klávesnica overená, Windows checklist prejdený, `feature/keyboard-identity`
aj `feature/windows-raw-input-probe` zmergované, Raw Input hotový, users rework
spravený, identita klávesnice napojená na stĺpec testéra.

Ostáva už len škola: elaborát, prezentácia a pondelkový meeting s Uhrínom
(viď `TODO-matej.md`).

## 🚀 Ako spustiť (Linux, tracking)

```bash
cd Smatanova/VQSTing
./run.sh     # listener (1× pkexec dialóg) + appka → http://127.0.0.1:5000/keyboards
Ctrl+C       # alebo ./stop.sh — vypne oboje, prístup k /dev/input zaniká
```

- stránka `/keyboards` = len admin (`admin`/`admin`), refresh 1 s
- stav beží v `/run/vqsting/keyboards.json` (RAM, zmizne rebootom)

## 🧠 Rozhodnutia (21.–22.10.2026)
- Architektúra **B**: samostatný listener proces + IPC cez JSON — rovnaký tvar
  ako Windows verzia (tam len Raw Input namiesto evdev, bez `pkexec`)
- Prístup k `/dev/input` **len cez dočasné fds** root openera — žiadny ACL/udev rule
- Po `pkexec` listener **zhodí supplementary groups**; `open.sock` je vlastnený
  userom, nie rootom (22.10.)
- Stránka `/keyboards` len pre admina (role 10)
- Čítač: stdlib `struct`, žiadna nová závislosť (`requirements.txt` ostáva cross-platform)

## 🧹 Poznámky
- `csv/ExampleTest.csv` a `instance/database.db` mení smoke test / beh appky → necommitovať
