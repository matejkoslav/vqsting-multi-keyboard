# Windows test — listener klávesníc (krok za krokom)

Návod pre **Patrika**. Cieľ: overiť, že appka na Windows rozlíši **dve fyzické
klávesnice** a že každá má vlastné stabilné ID. Nič sa neinštaluje, netreba
admin a nemení sa žiadne systémové nastavenie.

Zdrojový kód je `Smatanova/VQSTing/tools/windows_keyboard_listener.py`.
Ak niečo zlyhá, postupuj podľa časti „Ak sa nedarí“ a pošli Matejovi výstup.

## Čo potrebuješ

- Windows 10 alebo 11, dve USB klávesnice.
- Python z <https://www.python.org/downloads/>. Pri inštalácii zaškrtni
  **„Add python.exe to PATH“**. Nič ďalšie neinštaluj.
  (Ak appka vypíše, že chýba Flask, raz spusti
  `pip install -r requirements.txt` v priečinku `Smatanova\VQSTing`.)
- Priečinok s repozitárom (tam, kde je `README.md`).

## Krok 1 — samotný listener bez appky (`--selftest`)

Toto je najmenšia možná kontrola a nepotrebuje ani klávesnice. Otvor
**PowerShell** alebo **Git Bash** a spusti z koreňa repozitára:

```powershell
python Smatanova\VQSTing\tools\windows_keyboard_listener.py --selftest
```

Ak `python` nefunguje, skús `py` namiesto `python` (Python z python.org).

**Čo musíš vidieť** (poradie riadkov nemusí byť presne takéto, ale text áno):

```text
[OK] instančná cesta a stabilné id
[OK] mapovanie VKey na názov klávesy
[OK] stavový JSON zo syntetických eventov
[OK] krúžkový buffer drží posledných 64 eventov
[OK] atomický zápis stavu
selftest OK
```

**Čo poslať späť:** celý tento výstup. Ak je tam `Traceback`, pošli aj ten
(celý, nie len posledný riadok).

## Krok 2 — listener + appka (`run.bat`)

1. Otvor priečinok `Smatanova\VQSTing` v Prieskumníkovi.
2. Dvojklik na **`run.bat`**.

Otvorí sa okno s dvoma vecami:

- **„VQSTing listener“** — minimalizované okno listenera (môžeš ho kedykoľvek
  obnoviť a pozerať, čo vypisuje),
- **Flask appka** — v okne pribudne riadok `Running on http://127.0.0.1:5000`.

Listener sám vypíše:

```text
listener: Windows Raw Input, stav C:\Users\<meno>\AppData\Local\vqsting\keyboards.json
```

## Krok 3 — stránka s klávesnicami

1. V prehliadači otvor <http://127.0.0.1:5000/keyboards>.
2. Prihlás sa ako **admin / admin**.
3. Stlač **raz jednu** klávesu na prvej klávesnici (napr. `1`), potom **raz**
   klávesu na druhej (napr. `2`). Klávesu nedrž — držanie sa počíta ako
   viac stlačení.
4. Tabuľka sa obnovuje raz za sekundu.

**Čo máš vidieť:** dva riadky v tabuľke, každý s iným názvom zariadenia a inou
inštanciou (krátky text typu `7&2f&0&0000`). V stĺpci s klávesou pribudne to, čo
si stlačil, a čas „x s ago“. V okne listenera pribudnú riadky:

```text
[win:7&2f&0&0000] 1  (\\?\HID#VID_046D&PID_C31C#7&2f&0&0000#{...})
[win:5&1a&0&0000] 2  (\\?\HID#VID_...&PID_...#5&1a&0&0000#{...})
```

Dôležité: **dve rôzne hodnoty za `win:`**. Presne tieto ID používa hlasovanie —
klávesnica = testér.

## Krok 4 — vypnutie

1. Zavri okno Flask appky (alebo v ňom stlač **Ctrl+C**).
2. Dvojklik na **`stop.bat`** — vypíše `Listener zastaveny (pid ...)`.
   Listener sa dá vypnúť aj **Ctrl+C** v jeho okne.

## Čo poslať Matejovi späť

1. **Celý výstup** z okna listenera (obnov okno, označ myšou celý text,
   pravý klik → Kopírovať).
2. **Screenshot** stránky `/keyboards` po stlačení klávesy na oboch
   klávesniciach.
3. **Celý výstup** z `--selftest` (Krok 1).
4. Obsah stavového súboru — v PowerShelli:

   ```powershell
   Get-Content "$env:LOCALAPPDATA\vqsting\keyboards.json"
   ```

   (Tento súbor je jediná vec, ktorú listener zapisuje, okrem `listener.pid`.)

5. Ak niečo zlyhalo, aj **celý text chyby** a odpoveď na otázku: „Videl si
   jeden riadok alebo dva?“

## Ak sa nedarí — 3 najčastejšie príčiny

### 1. Klávesnice idú cez USB hub (alebo dokovacia stanica)

Windows vidí hub, nie dve klávesnice, a obe dostanú rovnaké ID.

**Skús:** zapoj každú klávesnicu **priamo** do USB portu na počítači (nie cez
hub, monitor ani dokovaciu stanicu) a spusti `run.bat` znova.

### 2. PS/2 klávesnica (okrúhly konektor alebo prechodka)

PS/2 klávesnica nemá použiteľnú inštančnú cestu, takže sa nedá odlíšiť od
druhej. V tabuľke bude prázdna inštancia alebo rovnaké ID ako pri druhej.

**Skús:** dve USB klávesnice. PS/2 klávesnicu môžeš použiť len ako jednu
(jedinú) — hlasovanie dvoch testérov na nej nepôjde.

### 3. Dve úplne identické klávesnice bez sériového čísla

Ak sú to dva kusy toho istého modelu a výrobca do nich nedal sériové číslo,
Windows im môže dať rovnakú inštanciu. Prejaví sa to tak, že v tabuľke je po
stlačení na oboch klávesniciach **jeden riadok**.

**Skús:** zapojiť ich do rôznych USB portov (iná vetva radiča). Ak to nepomôže,
sú to klávesnice, ktoré sa v tejto appke nedajú rozlíšiť — treba iný model.
Toto je známe obmedzenie, nie chyba listenera.

Ešte dve veci, ktoré sa občas stanú:

- **Iné klávesy** (Shift, šípky, Win) sa tiež zapíšu — v tabuľke vidíš napr.
  `Left Shift` alebo `VKey 0x5B`. Je to správne, hlasovanie používa len
  klávesy `1`–`5`.
- Listener beží, ale v tabuľke je „No keyboard found“ — pozri do okna
  listenera: ak tam nie sú riadky `[win:...]`, klávesy sa k nemu nedostanú
  (zvyčajne príčina 1 alebo 2).

## Bezpečnosť

- Netreba **admin** ani **pkexec**. Nič sa neinštaluje, nič sa nemení
  v nastaveniach systému.
- Listener zapisuje len dva súbory do `%LOCALAPPDATA%\vqsting\`:
  `keyboards.json` a `listener.pid`.
- **Ctrl+C** alebo `stop.bat` ho kedykoľvek ukončí.
