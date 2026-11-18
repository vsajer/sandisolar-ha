# Počet stažení v HACS

HACS používá počítadlo stažení přiloženého souboru `sandisolar_modbus_rtu.zip`
u vybraného vydání na GitHubu. Nejde o počet lidí ani funkčních instalací:
započítají se také aktualizace, opakovaná i ruční stažení stejného balíčku.

## Nové vydání

1. Aktualizuj verzi v `custom_components/sandisolar_modbus_rtu/manifest.json`.
2. Vytvoř tag z commitu, který obsahuje nové nastavení `hacs.json`, a publikuj
   GitHub Release. Udržuj verzi v manifestu a tag vydání shodné (tag může mít `v`).
3. Workflow **Package HACS release** automaticky vytvoří instalační ZIP
   a přiloží jej do sekce Assets. Před oznámením vydání vyčkej na dokončení workflow.
4. Po obnovení údajů v HACS bude dostupný počet stažení tohoto souboru.

ZIP obsahuje přímo `manifest.json`, `__init__.py`, překlady a ostatní soubory
integrace. Neobsahuje nadřazený adresář `custom_components` ani celý repozitář.
Automatické odkazy GitHubu **Source code (zip/tar.gz)** tento balíček nenahrazují.

## Doplnění ZIPu ke staršímu vydání

Na GitHubu otevři **Actions → Package HACS release → Run workflow**, vyber
větev `main` a do pole `tag` napiš existující tag (např. `9.2.5`). Balíček bude
vytvořen přesně ze souborů tohoto tagu, nikoliv z aktuální větve `main`.

Tím se zpřístupní počítadlo přiloženého souboru; staré stažení se nedopočítá.
Pokud starý tag neobsahuje `zip_release` a `filename` v `hacs.json`, instalace
přes HACS mohou nadále stahovat archiv repozitáře a počítadlo ZIPu nezvyšovat.
Úplný přechod na stahování ZIPu tedy zajistí až nové vydání s novým `hacs.json`.
Staré tagy kvůli tomu nepřepisuj.

Existující ZIP se nikdy automaticky nenahrazuje: jeho smazání a nové nahrání
by ztratilo dosavadní počítadlo. Opravy distribuuj pod novým tagem.

Při pushi a pull requestu workflow pouze sestaví a ověří archiv; nic nepublikuje.
Žádná telemetrie ani diagnostická data se z Home Assistantu neodesílají.
