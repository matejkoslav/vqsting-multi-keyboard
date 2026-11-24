# Group mode — ako spustiť skupinový test

> N = 1 až 4 testéri sedia pri jednom PC, pozerajú
> to isté video na jednom monitore a každý hlasuje na svojej klávesnici.
> Hodnotenie je **slepé**: nikto nevidí, ako hodnotili ostatní. Testéri nemajú
> účty ani heslá — identitou je fyzická klávesnica, ktorú im priradíš pri párovaní.

## Čo na to treba

- Linux alebo Windows s touto verziou appky (listener klávesníc je súčasťou
  balíka: `./run.sh` na Linuxe, `run.bat` na Windows).
- Appku spúšťaj cez `./run.sh` — spustí aj Flask, aj listener klávesníc.
  Listener si na Linuxe vypýta `pkexec` (prístup k `/dev/input`), ten potvrď.
- Jedna obrazovka, jedna myš a 1–4 fyzické klávesnice.
- Vytvorenú session s videami (`Create new test session`, videá v
  `video/<nazov_session>/…`).
- Prihlásenie len pre admina: v demo databáze `admin` / `admin`. Nové účty sa
  cez web už nezakladajú — admin je jeden a to stačí.

## Krok za krokom

1. Prihlás sa ako admin a otvor **My test sessions**.
2. Pri session klikni na zelené tlačidlo **Group test**.
   Otvorí sa setup stránka s prázdnym priestorom pre stĺpce testérov.
3. Klikni **Add tester**. Pribudne stĺpec *Tester 1*. Postup zopakuj pre
   ďalších testérov (max 4).
4. **Párovanie klávesnice:** v stĺpci klikni **Pair keyboard**, potom testér
   stlačí ľubovoľnú klávesu na svojej klávesnici. Stĺpec zobrazí názov
   klávesnice (`AT Translated Set 2 keyboard`, …) a prestane čakať.
   Párovanie je **povinné**: hlasuje sa len na vlastnej klávesnici (myšou nie,
   aby ostatní nevideli, čo testér vybral). Bez spárovanej klávesnice sa *Start*
   neodomkne.
5. **Meno, vek a okuliare na klávesnici testéra:** polia idú v pevnom poradí
   a aktívne pole je zvýraznené modrým rámom:
   - meno a priezvisko písmenami (`Space` = medzera), potom `Enter`.
     Klávesnica testéra posiela len A–Z bez diakritiky a appka meno sama
     upraví na tvar „Jan Novak“;
   - vek číslicami, potom `Enter`;
   - okuliare: `1` = nosí, `2` = nenosí.
   `Backspace` maže v aktívnom poli. Klávesy idú **len** do aktívneho poľa, takže
   číslice sa nikdy nedostanú do mena a 1/2 pri okuliaroch nezmenia vek. Keď je
   všetko uložené, ďalšie klávesy sa ignorujú a opravu urobí operátor cez ✎.
   Políčka sú zamknuté. Windows posiela stlačenia zo všetkých klávesníc aj do
   políčka, na ktoré niekto klikol, a preto sa kedysi vek jedného testéra
   zapisoval aj do políčka iného testéra.
6. **Úprava operátorom:** tlačidlo ✎ pri políčku ho odomkne a operátor môže na
   svojej klávesnici opraviť meno (aj s diakritikou) alebo vek. `Enter` uloží,
   `Esc` zruší. Kým operátor upravuje, klávesnice testérov sú pozastavené, takže
   sa nič nezapíše inam. Okuliare sa dajú kliknúť aj myšou (*Yes/No*).
   **✕ Remove** odstráni testéra. Ostatní si nechajú svoje údaje aj rozpísaný
   text a len sa prečíslujú. Uvoľnené miesto sa dá znova obsadiť cez
   **Add tester**. Počas bežiaceho testu sa odstrániť nedá.
7. **Tréning (nepovinné):** tlačidlo **Training** prehrá tréningový playlist
   raz pre všetkých, bez kontroly intervalu. Po dohraní si testéri môžu
   sadnúť a ide sa na ostro.
8. **Start** je aktívny, keď má každý testér vyplnené meno a vek a spárovanú klávesnicu. Pred spustením
   skontroluje, či sú v priečinku `video` všetky súbory session. Ak niečo chýba,
   ostane na setup stránke s chybovou hláškou a test sa nezasekne v stave „running“. Appka vygeneruje spoločné poradie videí a prehrá prvé.
9. **Hlasovanie (slepé):** po každom videu sa zobrazí obrazovka s časovačom,
   legendou stupnice 5→1 hore (rovnaké texty ako v klasickom teste) a N stĺpcami.
   Stĺpec ukazuje meno, „Tester X“, „…“ a „waiting for rating…“.
   - každý testér stlačí `1`–`5` na svojej klávesnici — rámik jeho stĺpca
     **zozelenie** a text sa zmení na „*meno* has rated this sequence“. Hodnota sa
     **nikde nezobrazí** (ani sa neposiela do prehliadača), aby neovplyvnila ostatných;
   - platí **len prvé stlačenie** — ďalšie klávesy v tom kole sa ignorujú;
   - myšou sa hlasovať nedá;
   - kolo sa zavrie po **9 sekundách** alebo hneď, keď hlasovali všetci.
10. Po poslednom videu sa zobrazí **Results** — tabuľka video × testér
    s demografiou. Je určená pre admina (testéri ju už nemusia vidieť).
    Odtiaľ sa robí export, reset aj nový beh.

## Opakované spustenie session (viac behov)

Jednu session môžeš spustiť **koľkokrát chceš**, zakaždým s inými testérmi:

- Keď beh dobehne a znova klikneš **Group test** (alebo **New run** na Results),
  začne sa **nový beh** (*Run 2, Run 3, …*) s voľnými miestami. Testéri
  z predchádzajúcich behov sa **nestratia** — ostanú vo výsledkoch aj exporte
  a noví sa k nim pridajú vedľa.
- Results a export ukazujú všetkých testérov zo všetkých dokončených behov vedľa
  seba, s riadkami **Run** (číslo behu) a **Run date** (kedy bol beh spustený).
- **Reset** zmaže len **aktuálny** beh (jeho testérov a hlasy). Staršie behy ostanú.
- **Delete all results** (na stránke Results) po potvrdení zmaže **všetky** behy
  session so všetkými testérmi a hlasmi — napr. po skúšobných testoch.
- Beh, ktorý sa nedokončil (stav *running*), sa sám neukončí — dokonči ho alebo
  daj **Reset**.

## Ako čítať výsledky a CSV

Tabuľka na Results má riadky videá, stĺpce testérov, v hlavičke vek
a okuliare. `n/a` znamená, že testér v tom kole nehlasoval (kolo sa zavrelo
po 9 s bez neho).

Tlačidlo **Export CSV + Excel** zapíše do priečinka `csv/` dva súbory
(podčiarkniky namiesto medzier) a otvorí priečinok:

- Hore je dátum **vytvorenia session** (*Created*). Pri sessions vytvorených
  pred 21.11.2026 sa to nevedelo, preto sa použije dátum prvého skupinového testu.
- `<nazov_session>.xlsx`: naformátovaná tabuľka vo farbách appky. Obsahuje
  hlavičku s menami testérov, vek a okuliare, farebne odlíšené hodnotenia
  (5 = zelená … 1 = červená) a legendu stupnice.
- `<nazov_session>.csv`: rovnaké údaje na ďalšie spracovanie (Excel, MATLAB).
  Oddeľovač je `;`, aby sa v slovenskom Exceli každá hodnota zobrazila vo
  vlastnom stĺpci. Kódovanie je UTF-8 s BOM, aby sa správne zobrazila diakritika.

```csv
Session;ExampleTest
Method;DCR
Display;Samsung U24E590D UHD
Created;18.10.2026

Name;Ann;Bob;Cid
Run;1;2;2
Run date;07.11.2026 18:05;21.11.2026 19:40;21.11.2026 19:40
Tester;Tester 1;Tester 1;Tester 2
Age;21;22;23
Glasses;ano;nie;nie

Video;Ann;Bob;Cid
Basketball_H264_1M.mp4;4;2;5
Beauty_AV1_1M.mp4;3;n/a;1
```

Hodnoty sú 1–5, alebo `n/a`, ak testér v danom kole nehlasoval. Ak je súbor
otvorený v Exceli, export naň nevie zapisovať a appka ťa upozorní, aby si ho
zavrel. Na Excel export treba knižnicu `openpyxl`, ktorú nainštaluje
`pip install -r requirements.txt`.

**Reset** (na setup stránke) zmaže testérov a hlasy **aktuálneho behu**
a vráti ho do stavu *setup*; staršie behy, session a videá ostávajú.
**Delete all results** zmaže po potvrdení všetky behy session.

## Keď klávesnica nefunguje

| Príznak | Čo robiť |
|---|---|
| Červený pruh „Keyboard listener is not running“ | Appka nevidí listener. Ukonči appku a spusti znova `./run.sh`, potvrď `pkexec` dialóg. Skontroluj stránku **Keyboards** v menu — musí tam byť aspoň jeden riadok a posledná stlačená klávesa sa má meniť. |
| Pair keyboard nič nezobrazí | Testér stlačil klávesu na zlom zariadení, alebo je to myš. Skús inú klávesnicu. |
| Vek sa na klávesnici „nezachytí“ | Pozri, či stĺpec ukazuje názov klávesnice. Ak nie, nie je spárovaný — spáruj ho, prípadne vyplň vek cez ✎. |
| Stlačenie sa ukáže až po ďalšej klávese | Opravené 21.11.2026 (listener na Windowse opakuje zápis, keď appka práve číta `keyboards.json`). Ak sa to deje, over, že máš aktuálnu verziu a appku si spustil cez `run.bat`. |
| Hlasovanie klávesou nefunguje | Over párovanie a stránku **Keyboards**. Myšou sa hlasovať nedá (slepé hodnotenie) — oprav klávesnicu a kolo zopakuj cez *Reset*. |
| Dve rovnaké klávesnice sa „zlepia“ | Dve identické klávesnice bez sériového čísla na jednom rozbočovači môžu dostať rovnaké ID. Vtedy hlasujú ako jeden testér; použi inú klávesnicu. |

Meno, vek a okuliare sa dajú vždy vyplniť aj bez klávesnice testéra (✎, *Yes/No*),
ale **hlasovanie vyžaduje spárovanú klávesnicu** pre každého testéra a bežiaci listener.

## Známe obmedzenia

- Max 4 testéri (layout N stĺpcov vedľa seba).
- Beží len lokálne (`http://127.0.0.1:5000`), žiadne prihlasovanie testérov.
- Staré tabuľky (`detail`, `order`, `valuation`, `completed`) ostávajú
  v `instance/database.db`, ale kód ich už nepoužíva — `db.create_all()`
  pridá len nové tabuľky (`group_run`, `tester`, `group_vote`).
- Staré stránky účastníka (Register, Profile, Sessions list, Training/Test
  cez účet) už neexistujú; všetko ide cez Group test.
