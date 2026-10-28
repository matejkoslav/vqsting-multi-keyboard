# VQSTing — slovník

Subjektívne hodnotenie kvality videa na jednom PC, kde každý testér sedí pri
vlastnej klávesnici. Slovník drží jednu vec: aby „kto“ a „čo“ znamenali vždy
to isté, v kóde, v dokumentácii aj v rozhovore.

## Jazyk

**Testér** (Tester):
Človek, ktorý sedí pri PC a hodnotí videá. Nemá účet ani heslo.
_Avoid_: user, účastník, používateľ, participant

**Admin**:
Človek, ktorý sa prihlási (role 10), zakladá testy a pozerá výsledky.
_Avoid_: user, obsluha

**Stĺpec** (Seat):
Miesto testéra v jednom behu testu — má poradie 1–4, priradenú klávesnicu a demografiu.
_Avoid_: slot, okno, panel, user

**Párovanie** (Pairing):
Priradenie fyzickej klávesnice k stĺpcu tak, že testér stlačí ľubovoľnú klávesu.
_Avoid_: registrácia, prihlásenie, bind

**Group run**:
Jeden beh testu pre celú skupinu naraz — spoločné poradie videí, spoločný
monitor, N stĺpcov. N = 1 je tiež group run.
_Avoid_: skupinový test (v kóde), session (to je niečo iné)

**Session** (test session):
Konfigurácia testu, ktorú zakladá admin: názov, metóda (acr / acr-hr / dcr),
display, prostredie, videá. Existuje raz, môže mať viac behov.
_Avoid_: test (nejednoznačné)

**Kolo** (Round):
Jedno video v group rune: prehratie → hlasovanie → zatvorenie.
_Avoid_: iterácia, cyklus, step

**Hlas** (Vote):
Číslo 1–5, ktoré testér zadá v kole. Po zatvorení kola sa už nedá zmeniť.
_Avoid_: hodnotenie, známka, rating

**Keyboard ID**:
Stabilný reťazec identifikujúci fyzickú klávesnicu naprieč reconnectom
(`linux:…` / `win:…`). Je to identita testéra počas behu testu.
_Avoid_: port, device, zariadenie (to je širší pojem)

**Tréning**:
Prehratie tréningových videí pred ostrým testom. V group móde raz pre všetkých,
bez kontroly intervalu.
_Avoid_: cvičenie, warmup

## Vzťahy

- **Session** má 0 alebo 1 **Group run**; **Group run** má 1–4 **Stĺpce**.
- **Stĺpec** má najviac jedno **Keyboard ID** a ľubovoľne veľa **Hlasov**
  (jeden na **Kolo**).
- **Kolo** patrí **Group runu**, nie stĺpcu — všetci vidia to isté video.
