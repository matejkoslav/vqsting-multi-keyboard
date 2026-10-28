# Klávesnica je identita testéra

Pri N ľuďoch na jednom PC a jednom monitore neexistuje prihlasovanie ani
profil: keď niekto stlačí `4`, musíme vedieť, ktorý stĺpec to je. Bežné vstupné
API (prehliadač, `pynput`, `keyboard`) to nepovedia — všetky klávesnice splývajú
do jedného vstupu.

Preto identitu nesie **zariadenie**: Linux listener číta `/dev/input` (evdev),
Windows listener číta Raw Input (`WM_INPUT` → `hDevice` → `RIDI_DEVICENAME`) a
oba zapisujú rovnaký JSON so stabilným `id` zariadenia. Flask nikdy nečíta
zariadenia priamo, len ten JSON.

**Trade-off:** spoliehame sa na to, že OS rozlíši klávesnice. Dve identické
klávesnice bez sériového čísla na jednom rozbočovači môžu splynúť. Vtedy je
fallback myš: klik na hlavičku stĺpca a potom na číslo (myš identitu nemá, a
preto sa musí vybrať stĺpec explicitne).

**Zamietnutá alternatíva:** multi-seat softvér (ASTER, MultiPoint) — jeden PC
ako N nezávislých pracovísk. Rieši to iný problém (každý má vlastný monitor) a
nepotrebuje našu aplikáciu meniť vôbec; zadanie je ale jeden monitor, jedna
projekcia, spoločné video.
