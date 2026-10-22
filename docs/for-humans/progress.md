# Progress — living list

Aktualizované: 22.10.2026 · branch `feature/keyboard-identity` (6 commitov pred `main`, 0 lokálnych — pushnuté)

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
1. **Doplniť druhú klávesnicu:** zapnúť KILO BT, `./run.sh`, overiť 2 riadky na `/keyboards`
2. **Patrik:** prejsť Windows checklist na reálnom Windows (overiť pôvodnú appku)
3. **Merge:** `feature/keyboard-identity` → `main` (6 commitov, pushnuté; čaká CI + BT test)
4. **Windows tracking:** Raw Input (`hDevice` → `RIDI_DEVICENAME`) v
   `tools/keyboard_listener.py` — Flask/stránka ostávajú rovnaké, bez roota
5. **Users rework:** tester-sloty bez hesla (potrebuje rozhodnutia: login áno/nie,
   kto zakladá testerov) — predpoklad pre napojenie klávesníc na testerov
6. Napojiť identitu klávesnice na slot testera + hlasovanie 1–5

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
