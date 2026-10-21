# NÁVOD — ako si stiahnuť a rozbehnúť projekt

Krátky návod pre kolegov. Cieľ: **stiahnuť → spustiť → funguje to.**

## Ako začať (rýchlo)

1. Pošli **Matejovi** svoj **GitHub username** → príde ti pozvánka do repa → **prijmi ju**.
2. `git clone …` (bod 2 nižšie).
3. Spusť appku (bod 3), rob zmeny, potom **vetva → push → Pull Request** (bod 5).

Čo je a čo NIE je v repe → bod 6. 👇

---

## 1. Čo potrebuješ (raz nainštalovať)

- **Windows + Linux** (od 18.10.2026).
- **Python 3** — <https://www.python.org/downloads/> → pri inštalácii zaškrtni **„Add python.exe to PATH“**.
- **Git** — [Git for Windows](https://git-scm.com/download/win) (nainštaluj vrátane *Git Bash*).
- **`mpv.exe` a videá nie sú v repe** (sú veľké) → vyžiadaj si ich od Mateja (USB/disk).

## 2. Stiahnutie projektu

```bash
git clone https://github.com/matejkoslav/vqsting-multi-keyboard.git
cd vqsting-multi-keyboard
```

Na Windows to spustíš v **Git Bash** (odporúčané) alebo v **PowerShell** (príkazy sú rovnaké).

Alternatíva bez Gitu: na GitHube **Code → Download ZIP**. Pozor: so ZIPom nebudeš dostávať nové zmeny
(`git pull`) ani vedieť posielať vlastné — preto odporúčam clone.

## 3. Spustenie appky

```bash
cd Smatanova/VQSTing
pip install flask flask_sqlalchemy flask_login plotly
python main.py
```

Potom otvor <http://127.0.0.1:5000>.

- Prvé spustenie je pomalé (inštalujú sa knižnice).
- Terminál musí bežať celý čas. Vypnutie: `Ctrl+C`.

**Na plný test** (prehrávanie videí) treba mať na týchto cestách:
- `Smatanova/VQSTing/mpv.exe` — prehrávač,
- `Smatanova/VQSTing/video/` — testovacie videá (vrátane `grey50.mp4`).

Toto v repe nie je → skopíruj od Mateja na tie isté cesty.

## 4. Prihlásenie a rýchly test

1. <http://127.0.0.1:5000> → login **`admin` / `admin`**.
2. `My test sessions` → `ExampleTest` → `Details / Statistics / Export`.
3. Nový účastník: odhlás sa → `Register` → vyplň profil → `Test sessions list` → zadaj heslo testu.

## 5. Ako prispieť kódom (push)

Repo je **public** — klonovať môže ktokoľvek, ale **pushovať priamo nie, kým nemáš práva**. Dve možnosti:

**A — Collaborator (odporúčané, pushuješ priamo):**

1. Pošli Matejovi svoj **GitHub username**.
2. Matej ťa pridá: *repo → Settings → Collaborators → Add people*.
3. Prijmi pozvánku → máš push práva.

**B — Fork + Pull Request (bez práv):**

1. Na GitHube hore vpravo klikni **Fork**.
2. Klonuj si **svoj fork** a pracuj v ňom.
3. Pushni do forku → na GitHube **Contribute → Open pull request**.

**Bežný postup (platí pre obe možnosti):**

```bash
git pull                                  # VŽDY pred prácou
git checkout -b feature/kratky-nazov      # vlastná vetva na prácu
# ... robíš zmeny, ukladáš ...
git add -A
git commit -m "Stručný popis zmeny"
git push -u origin feature/kratky-nazov
```

Potom na GitHube otvor **Pull Request** do `main` a napíš, čo si zmenil.

## 6. Čo je v repe a čo NIE

**V repe (commitnuté):**

- kód appky — `Smatanova/VQSTing/` (Python, šablóny, štýly, obrázky),
- demo databáza — `Smatanova/VQSTing/instance/database.db` (`admin/admin` + `ExampleTest`),
- export — `Smatanova/VQSTing/csv/ExampleTest.csv`,
- dokumentácia — `docs/` + tento návod.

**NIE je v repe (zámerne, cez `.gitignore`):**

- `Smatanova/VQSTing/video/` — testovacie videá (**581 MB**) → od Mateja,
- `Smatanova/VQSTing/mpv.exe` — prehrávač (**104 MB**, GitHub blokuje súbory >100 MB) → od Mateja,
- `*.pdf` — zdrojová diplomovka a manuál → necommitovať,
- `__pycache__/`, `*.pyc` — generuje Python.

## 7. Poznámky pre Windows tím

- Drž sa **presných názvov** — v tíme sú aj Linux stroje, kde na veľkosti písmen záleží.
- `main` = stabilná verzia. Nerobiť do nej priame commity.
- Ak appku spustíš, `database.db` sa zmení — **necommituj tú zmenu**, ak si nič nemenil v DB.
