# Testéri nemajú účty, len stĺpce

Pôvodná aplikácia vyžadovala od každého účastníka registráciu, heslo a profil
(pohlavie, vek, okuliare). Pri skupinovom teste na jednom PC je to zbytočná
prekážka: nikto sa neprihlasuje, nikto nemá históriu a jediné, čo z účastníka
naozaj potrebujeme, sú demografické údaje pre export.

Rozhodli sme sa **zrušiť účastnícke účty** (`User` role 1) a nahradiť ich
stĺpcami viazanými na konkrétny beh testu. Prihlásenie ostáva len pre admina.
Dôsledok: `Valuation`, `Order`, `Completed` a `Detail` sa prestali používať a
nahradili ich `GroupRun`, `Tester` a `GroupVote`.

**Zamietnutá alternatíva:** nechať starý flow bežať popri novom. Znamenalo by to
dva svety, dva exporty a dva spôsoby štatistík pri jednej obrazovke.
