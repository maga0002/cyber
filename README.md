# Cyberweerbaarheid Monitor

Webapplicatie om de cyberweerbaarheid van de organisatie te monitoren en te communiceren.

- **Startpagina met nieuws** – plaats berichten (Algemeen, Waarschuwing, Incident, Tip, Update), zet ze bovenaan vast of bewaar ze als concept.
- **Dashboards uit lijsten** – importeer een CSV- of Excel-bestand; de app maakt er automatisch grafieken, kerncijfers en een doorzoekbare tabel van. Klik op een grafiekdeel om te filteren. Bijwerken met een nieuw bestand houdt dezelfde link.
- **NIST Cybersecurity Framework 2.0** – alle 6 functies, 22 categorieën en 106 subcategorieën zijn ingebouwd. Per subcategorie leg je een volwassenheidsscore (0–5, huidig en doel), eigenaar en onderbouwing vast; per functie en categorie schrijf je een toelichting voor lezers ("Wat doen wij hieraan?"), en je koppelt verbeteracties met eigenaar, prioriteit en deadline. Rapportage via een overzicht (radar, heatmap, grootste gaten, trend), een afdrukbaar managementrapport (opslaan als PDF) en een Excel-export.
- **Database** – gebruikt PostgreSQL als `DATABASE_URL` is ingesteld én bereikbaar is; anders automatisch SQLite (`instance/cyber.db`). De gebruikte database staat (voor beheerders) onderaan de pagina.

Bezoekers kunnen alles lezen; alleen ingelogde beheerders kunnen plaatsen, importeren, bewerken en verwijderen.

## Snel starten op je eigen computer

1. Installeer **Python 3.11 of nieuwer** via https://www.python.org/downloads/ (Windows: vink *Add python.exe to PATH* aan).
2. Download de code: op GitHub **Code → Download ZIP** en pak het bestand uit (of `git clone`).
3. Start de app:
   - **Windows:** dubbelklik op `start.bat`
   - **macOS / Linux:** open een terminal in de map en voer `./start.sh` uit
4. De browser opent http://127.0.0.1:5000. De eerste keer maak je het beheerdersaccount aan.

De eerste start duurt een paar minuten (pakketten installeren); daarna start de app binnen enkele seconden. Je gegevens staan in de map `instance/` naast de code.

## Starten in GitHub Codespaces

1. Ga op GitHub naar de repository → groene knop **Code** → tabblad **Codespaces** → **Create codespace**.
2. Wacht tot de Codespace klaar is (de eerste keer een paar minuten). De afhankelijkheden worden automatisch geïnstalleerd en de app start vanzelf.
3. De app opent in een nieuw browsertabblad. Gebeurt dat niet: open onderin het tabblad **Ports** en klik op het wereldbolletje bij poort **5000**.
4. Maak bij het eerste bezoek het beheerdersaccount aan.

Handmatig (opnieuw) starten in de terminal van de Codespace:

```bash
python run.py
```

Let op: de SQLite-database staat in de Codespace zelf (`instance/cyber.db`). Die blijft bewaard zolang de Codespace bestaat, maar verdwijnt als je de Codespace verwijdert. Gebruik voor blijvend gebruik een server met PostgreSQL (zie hieronder).

## Installeren

```bash
python3 -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Starten

```bash
python run.py
```

Open http://127.0.0.1:5000. Bij de eerste keer maak je het beheerdersaccount aan.

Voor productie (bijv. op een server):

```bash
waitress-serve --host 0.0.0.0 --port 8000 --call app:create_app
```

## PostgreSQL gebruiken

Zet `DATABASE_URL` in je omgeving of in een `.env`-bestand (zie `.env.example`):

```
DATABASE_URL=postgresql://gebruiker:wachtwoord@dbserver:5432/cyber
```

Bij het opstarten test de app de verbinding (3 seconden time-out). Lukt dat niet, dan valt hij terug op SQLite en meldt dat in de log. Tabellen worden automatisch aangemaakt.

## Lijsten importeren

- Eerste regel = kolomnamen. Komma, puntkomma en tab worden automatisch herkend.
- Tekstkolommen (Status, Eigenaar, Prioriteit…) worden geteld en als grafiek getoond; kolommen met alleen unieke waarden (namen, datums) worden overgeslagen.
- Getalkolommen (Score, Kosten…) worden samengevat (gemiddelde, min, max).
- Statuswaarden zoals *Gereed/Voldoet/Groen/Laag*, *Deels/In uitvoering/Gepland/Middel* en *Open/Niet/Rood/Hoog* krijgen automatisch stoplichtkleuren.

Een voorbeeld staat in `voorbeelden/maatregelen.csv`.

## NIST CSF gebruiken

1. Ga naar **NIST CSF** in het menu (na inloggen).
2. Klik een categorie aan (bijv. in de heatmap) en vul per subcategorie de huidige score en het doel in. Of importeer alles in één keer: **Importeren → Download sjabloon**, vul het in Excel in en upload het weer.
3. Schrijf per functie/categorie een toelichting voor lezers, en voeg verbeteracties toe (ook per subcategorie via **+ actie**).
4. Voeg per subcategorie **bewijsstukken** toe (via **+ bewijsstuk**): een bestand (PDF, Office, afbeelding, e-mail, zip; max. 16 MB) of een link naar bijv. SharePoint. Geef optioneel een datum voor herbeoordeling; daarna wordt het stuk als *verlopen* gemarkeerd. **NIST CSF → Bewijsstukken** toont alle stukken, de verlopen stukken en welke subcategorieën nog geen bewijs hebben.
5. Leg periodiek (bijv. per kwartaal) een **momentopname** vast; het overzicht en rapport tonen dan de ontwikkeling.
6. **Rapport** geeft een managementrapport (afdrukken of opslaan als PDF), **Excel-export** levert alle scores en acties in vier tabbladen.

Volwassenheidsschaal: 0 Niet aanwezig · 1 Initieel · 2 Herhaalbaar · 3 Gedefinieerd · 4 Beheerst · 5 Geoptimaliseerd. Subcategorieën kunnen op *n.v.t.* worden gezet en tellen dan niet mee.

Standaard zijn de NIST-pagina's alleen zichtbaar voor ingelogde beheerders. Onderaan het NIST-overzicht kun je ze openbaar maken voor bezoekers (alleen lezen). **Bewijsstukken blijven altijd alleen voor beheerders zichtbaar**, ook als de NIST-pagina's openbaar zijn.

Bewijsbestanden worden in de database opgeslagen (SQLite of PostgreSQL), zodat een back-up van de database ook alle bewijsstukken bevat. Om veiligheidsredenen worden HTML-, SVG-, script- en programmabestanden geweigerd.

Voorbeeldbestanden: `voorbeelden/nist_beoordeling.csv` en `voorbeelden/nist_acties.csv`.

De Nederlandse omschrijvingen zijn samenvattingen van de officiële NIST-teksten; zie https://www.nist.gov/cyberframework voor de bron.

## Beheer via de commandoregel

Extra beheerder aanmaken of wachtwoord resetten:

```bash
flask --app run create-admin <gebruikersnaam>
```

## Tests

```bash
python -m pytest
```
