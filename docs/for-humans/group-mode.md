# Group mode — ako spustiť skupinový test

> Vetva `feature/group-mode`. N = 1 až 4 testéri sedia pri jednom PC, pozerajú
> to isté video na jednom monitore a každý hlasuje na svojej klávesnici
> (alebo myšou). Testéri nemajú účty ani heslá — identitou je fyzická
> klávesnica, ktorú im priradíš pri párovaní.

## Čo na to treba

- Linux s touto verziou appky (listener klávesníc je súčasťou balíka).
- Appku spúšťaj cez `./run.sh` — spustí aj Flask, aj listener klávesníc.
  Listener si vypýta `pkexec` dialóg (prístup k `/dev/input`), ten potvrď.
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
   Párovanie je odporúčané, nie povinné — testér bez klávesnice môže hlasovať
   myšou (krok 6).
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
8. **Start** je aktívny, keď má každý testér vyplnené meno a vek. Pred spustením
   skontroluje, či sú v priečinku `video` všetky súbory session. Ak niečo chýba,
   ostane na setup stránke s chybovou hláškou a test sa nezasekne v stave „running“. Appka vygeneruje spoločné poradie videí a prehrá prvé.
9. **Hlasovanie:** po každom videu sa zobrazí obrazovka s N stĺpcami vedľa
   seba a školou 5→1 (rovnaké texty ako v klasickom teste).
   - každý testér stlačí `1`–`5` na svojej klávesnici — jeho stĺpec sa označí
     `✓ hlasoval`;
   - myšou: klikni na hlavičku stĺpca (modrý rám = stĺpec je „arm“), potom
     klikni na číslo v tom stĺpci;
   - hlas sa dá zmeniť do zatvorenia kola;
   - kolo sa zavrie po **9 sekundách** alebo hneď, keď hlasovali všetci.
10. Po poslednom videu sa zobrazí **Results** — tabuľka video × testér
    s demografiou. Odtiaľ sa robí export aj reset.

## Ako čítať výsledky a CSV

Tabuľka na Results má riadky videá, stĺpce testérov, v hlavičke vek
a okuliare. `n/a` znamená, že testér v tom kole nehlasoval (kolo sa zavrelo
po 9 s bez neho).

Tlačidlo **Export CSV + Excel** zapíše do priečinka `csv/` dva súbory
(podčiarkniky namiesto medzier) a otvorí priečinok:

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
Exported;07.11.2026 19:31

Tester;Tester 1;Tester 2
Name;Ján Nový;Eva Malá
Age;23;31
Glasses;ano;nie

Video;Ján Nový;Eva Malá
Basketball_H264_1M.mp4;2;n/a
Beauty_AV1_1M.mp4;4;5
```

Hodnoty sú 1–5, alebo `n/a`, ak testér v danom kole nehlasoval. Ak je súbor
otvorený v Exceli, export naň nevie zapisovať a appka ťa upozorní, aby si ho
zavrel. Na Excel export treba knižnicu `openpyxl`, ktorú nainštaluje
`pip install -r requirements.txt`.

**Reset** (na setup aj results stránke) zmaže testérov, hlasy aj poradie
a vráti run do stavu *setup*; session a videá ostávajú.

## Keď klávesnica nefunguje

| Príznak | Čo robiť |
|---|---|
| Červený pruh „Keyboard listener is not running“ | Appka nevidí listener. Ukonči appku a spusti znova `./run.sh`, potvrď `pkexec` dialóg. Skontroluj stránku **Keyboards** v menu — musí tam byť aspoň jeden riadok a posledná stlačená klávesa sa má meniť. |
| Pair keyboard nič nezobrazí | Testér stlačil klávesu na zlom zariadení, alebo je to myš. Skús inú klávesnicu, prípadne použi fallback myšou. |
| Vek sa na klávesnici „nezachytí“ | Pozri, či stĺpec ukazuje názov klávesnice. Ak nie, nie je spárovaný — vyplň vek myšou. |
| Hlasovanie klávesou nefunguje | Over párovanie a stránku **Keyboards**; do zatvorenia kola môžeš hlasovať myšou (hlavička → číslo). |
| Dve rovnaké klávesnice sa „zlepia“ | Dve identické klávesnice bez sériového čísla na jednom rozbočovači môžu dostať rovnaké ID. Vtedy hlasujú ako jeden testér; použi myš alebo inú klávesnicu. |

Vždy platí: **bez klávesnice sa dá celý test odohrať myšou** — nastav vek
a okuliare inputmi, hlasuj kliknutím na hlavičku a číslo. Admin tak vie
dokončiť test aj vtedy, keď listener nebeží.

## Známe obmedzenia

- Max 4 testéri (layout N stĺpcov vedľa seba).
- Beží len lokálne (`http://127.0.0.1:5000`), žiadne prihlasovanie testérov.
- Staré tabuľky (`detail`, `order`, `valuation`, `completed`) ostávajú
  v `instance/database.db`, ale kód ich už nepoužíva — `db.create_all()`
  pridá len nové tabuľky (`group_run`, `tester`, `group_vote`).
- Staré stránky účastníka (Register, Profile, Sessions list, Training/Test
  cez účet) už neexistujú; všetko ide cez Group test.
