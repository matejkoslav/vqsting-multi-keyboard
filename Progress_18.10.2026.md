📋 Recap
Cieľ: rozbehnúť VQSTing na Linuxe + pripraviť Windows overenie.
✅ Hotové
1. Cross-platform patch na branchi feature/cross-platform
- nový website/platform_compat.py (mpv, cesty, otváranie priečinka)
- upravené video.py + views.py — Windows správanie bez zmeny
2. Smoke test tests/smoke_test.py — celý flow (register → training → 12× test → hodnotenie)
3. CI .github/workflows/ci.yml — matica Ubuntu + Windows → obe zelené ✅
4. Checklist pre kamaráta: docs/for-humans/windows-checklist.md
5. Venv mimo syncu: ~/.venvs/vqsting (nesynchronizuje sa)
✅ Overené
- Linux desktop: celý flow funguje (mpv fullscreen, hodnotenie, export)
- Notebook: test prešiel, user matej + 12 hodnotení + CSV stĺpec dorazili cez Syncthing
- Windows: CI boot + importy OK (prehrávanie overí kamarát manuálne)
📌 Zostáva
- Kamarát: prejsť checklist na Windows
- Potom: multi-keyboard feature (Linux evdev + Windows Raw Input)
- Necommitovať database.db a csv/ExampleTest.csv