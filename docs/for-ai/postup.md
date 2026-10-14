odpoved od ai, ešte sa spýtať čo spolupárca

Krátko a k veci — najprv pár faktov, potom odporúčaný postup.
1. Prostredie: VM alebo reálny Windows?
- Na overenie, že appka funguje (spustí sa, prihlásenie, test, export CSV) → VM stačí. Na Omarchy je najlepšie QEMU/KVM + virt-manager s Windows 10/11 guestom.
- Na reálne subjektívne meranie kvality videa VM NEPOUŽÍVAJ — virtualizovaný grafický výstup, škálovanie a audio skresľujú to, čo ľudia vidia/počujú. To by znehodnotilo celý test. Na to potrebuješ reálny PC / dual-boot.
- Odporúčam: dual-boot alebo reálny Windows PC v labe na ostré testy, VM len na vývoj/overenie. USB klávesnice vieš do VM prepasovať (virt-manager → Add Hardware → USB Host Device podľa portu), ale je to otrava a pri meraní to aj tak nepoužiješ.
2. Najprv potvrdenie funkčnosti (úloha „potvrdiť, že funguje")
1. Windows + Python z python.org (zaškrtni „Add to PATH").
2. Dvojklik VQSTing.bat → otvorí http://127.0.0.1:5000.
3. Login admin / admin, pozri My test sessions → ExampleTest.
4. Registruj účastníka, vyplň profil, zadaj heslo testu, sprav tréning + test, daj Export a skontroluj csv/.
3. Kľúčový technický fakt k viacerým klávesniciam
Bežné Windows API (WM_KEYDOWN, Python keyboard, pynput) nevedia rozlíšiť, z ktorej klávesnice stlačenie prišlo — všetky sa zlejú do jedného vstupu. Preto sa to „podľa USB portov" robí cez Windows Raw Input API:
- RegisterRawInputDevices (usage page 1, usage 6 = klávesnica, flag RIDEV_INPUTSINK, cieľ = skryté okno),
- pri každej stlačenej klávese príde WM_INPUT, z neho GetRawInputData → hDevice,
- GetRawInputDeviceInfo(RIDI_DEVICENAME) → reťazec ako \\?\HID#VID_046D&PID_C31C#7&2f...&0&0000#{...}. To „7&2f...&0&0000" je inštančná cesta, ktorá pri rovnakých klávesniciach bez sériového čísla kóduje USB port → presne to rozlíšenie, ktoré chceš.
V Pythone: buď pip install rawinput, alebo ručne cez ctypes/pywin32. (pynput/keyboard sú nepoužiteľné.) Pozor: PS/2 klávesnice rozlíšiť nevieš, a Bluetooth/hub môže dať iné cesty — treba testovať.
Dôležité: prehliadač toto nezvládne (vstup je viazaný na fokus okna, nie na zariadenie). Takže Raw Input musí bežať v natívnom pomocnom procese (Python), ktorý sa pripojí k Flask appke.
4. Dve možné architektúry (vyber podľa zadania)
A) Group mód (jeden PC, jedna obrazovka, N klávesníc) — najbližšie k tomu, čo opisuješ:
- všetci pozerajú to isté video naraz (jeden MPV, jeden zvuk — vyrieši to aj problém s audiaom),
- po skončení sa zobrazí N panelov, každý tester stlačí 1–5 na svojej klávesnici,
- natívny Raw Input proces namapuje hDevice → slot testera a pošle hlas na Flask endpoint (/vote?tester=1),
- server zapíše do Valuation s identitou slotu.
- Realizácia: nový skript keyboard_listener.py + úpravy v video.py (nový endpoint) + test.html (N panelov).
B) Multi-seat (jeden PC = N nezávislých PC) — žiadny Raw Input, žiadne prepisovanie appky:
- softvér ako ASTER / Windows MultiPoint spraví z jedného PC N samostatných pracovísk, každé s vlastnou klávesnicou, myšou, monitorom a zvukom,
- appku pustíš ako N inštancií (rôzne porty) alebo N prehliadačov → každý tester je normálne samostatný „user" ako dnes.
- Toto je výrazne jednoduchšie a menej riskantné, ak testovatelia nemusia vidieť to isté video.
5. Odporúčaný postup
1. Over appku na Windows (bod 2) — bez tohto ďalej nemá zmysel.
2. Vyjasni so zadávateľom: pozerajú testeri to isté video spoločne (→ A), alebo každý sám (→ B)? Jeden monitor alebo viac? Koľko testerov? — toto rozhodne o celej architektúre.
3. Zderiskuj jadro problému vopred: napíš malý Windows skript, ktorý vypíše RIDI_DEVICENAME pri stlačení klávesy na každej z dvoch klávesníc a over, že dáva 2 rôzne ID (a či sedí s USB portom). Ak áno, A je priechodné; ak nie, B je istota.
4. Až potom implementuj integráciu a testuj s 2 klávesnicami: stlač na každej a over v DB, že hlas patrí správnemu testerovi.
Zhrnutie: na funkčnosť stačí VM, na meranie reálny PC; multi-seat (B) je najbezpečnejšia cesta, Raw Input (A) je to, čo po tebe zrejme chcú, ale najprv si to nechaj potvrdiť a sprav prototyp rozlíšenia klávesníc.