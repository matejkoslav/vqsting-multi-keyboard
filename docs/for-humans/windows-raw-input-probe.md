# Windows probe — rozlíšenie klávesníc (Raw Input)

Krátky návod pre **Patrika**. Cieľ: overiť, či Windows vidí dve fyzické klávesnice ako
dve samostatné zariadenia. Probe je len diagnostika — appku ani systém nemení.

## Čo potrebuješ

- Windows 10/11.
- Python z <https://www.python.org/downloads/>. Pri inštalácii zaškrtni
  **„Add python.exe to PATH“**. Nič ďalšie neinštaluj.

## Spustenie

1. Otvor **Git Bash** alebo **PowerShell** v koreni repa (tam, kde je `README.md`).
2. Spusti:

   ```bash
   python Smatanova/VQSTing/tools/windows_keyboard_probe.py
   ```

3. Stlač **raz** klávesu na prvej klávesnici, potom na druhej. Klávesu nedrž —
   opakovanie sa počíta ako ďalšie stlačenie.
4. Ukonči cez **Ctrl+C**. Probe vypíše súhrn.
5. **Skopíruj celý výstup** a pošli ho Matejovi.

Ak príkaz `python` nefunguje, skús `py` namiesto `python` (Python z python.org).

## Ako vyzerá úspech

- Po stlačení na dvoch klávesniciach vidíš **dve rôzne čísla zariadenia** `[1]`, `[2]`.
- Každé má iný **plný názov** zariadenia.
- `id=` je krátka časť názvu. Pri dvoch rovnakých klávesniciach bez sériového čísla
  práve táto časť rozlišuje USB port.

Príklad (skrátené):

```text
[1] id=7&2f...&0&0000 VKey=0x41  \\?\HID#VID_046D&PID_C31C#7&2f...&0&0000#{...}
[2] id=5&1a...&0&0000 VKey=0x41  \\?\HID#VID_...&PID_...&5&1a...&0&0000#{...}
```

## Ak vidíš len jedno zariadenie

Po **5 stlačeniach** probe vypíše varovanie. Možné príčiny:

- **PS/2** klávesnica — nemá samostatný USB port,
- obe klávesnice idú cez **USB hub**,
- **Bluetooth** klávesnica — Windows ju môže zlúčiť,
- **RDP** alebo virtuálny stroj — vstup sa zlučuje,
- ovládač zlúčil zariadenia.

Skús každú klávesnicu zapojiť priamo do USB portu, vypni Bluetooth a spusti probe znova.

## Bezpečnosť

- Netreba **admin**, nič sa neinštaluje a nič sa neukladá.
- Probe nemení appku, databázu ani súbory.
- **Ctrl+C** ho kedykoľvek ukončí.
