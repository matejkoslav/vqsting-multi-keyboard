# Progress — living list

Aktualizované: 21.10.2026 · branch `feature/keyboard-identity`

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

## ⏭️ Next actionable steps
1. **Patrik:** prejsť Windows checklist na reálnom Windows (overiť pôvodnú appku)
2. **Merge:** `feature/cross-platform` → `main` (2 commity čakajú)
3. **Windows tracking:** Raw Input (`hDevice` → `RIDI_DEVICENAME`) v
   `tools/keyboard_listener.py` — Flask/stránka ostávajú rovnaké, bez roota
4. **Users rework:** tester-sloty bez hesla (potrebuje rozhodnutia: login áno/nie,
   kto zakladá testerov) — predpoklad pre napojenie klávesníc na testerov
5. Napojiť identitu klávesnice na slot testera + hlasovanie 1–5

## 🚀 Ako spustiť (Linux, tracking)

```bash
cd Smatanova/VQSTing
./run.sh     # listener (1× pkexec dialóg) + appka → http://127.0.0.1:5000/keyboards
Ctrl+C       # alebo ./stop.sh — vypne oboje, prístup k /dev/input zaniká
```

- stránka `/keyboards` = len admin (`admin`/`admin`), refresh 1 s
- stav beží v `/run/vqsting/keyboards.json` (RAM, zmizne rebootom)

## 🧠 Rozhodnutia (21.10.2026)
- Architektúra **B**: samostatný listener proces + IPC cez JSON — rovnaký tvar
  ako Windows verzia (tam len Raw Input namiesto evdev, bez `pkexec`)
- Prístup k `/dev/input` **len cez dočasné fds** root openera — žiadny ACL/udev rule
- Stránka `/keyboards` len pre admina (role 10)
- Čítač: stdlib `struct`, žiadna nová závislosť (`requirements.txt` ostáva cross-platform)

## 🧹 Poznámky
- `csv/ExampleTest.csv` a `instance/database.db` mení smoke test / beh appky → necommitovať
