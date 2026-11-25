# Cyberweerbaarheid Monitor

Webapplicatie om de cyberweerbaarheid van de organisatie te monitoren en te communiceren.

- **Startpagina met nieuws** – plaats berichten (Algemeen, Waarschuwing, Incident, Tip, Update), zet ze bovenaan vast of bewaar ze als concept.
- **Dashboards uit lijsten** – importeer een CSV- of Excel-bestand; de app maakt er automatisch grafieken, kerncijfers en een doorzoekbare tabel van. Klik op een grafiekdeel om te filteren. Bijwerken met een nieuw bestand houdt dezelfde link.
- **Database** – gebruikt PostgreSQL als `DATABASE_URL` is ingesteld én bereikbaar is; anders automatisch SQLite (`instance/cyber.db`). De gebruikte database staat (voor beheerders) onderaan de pagina.

Bezoekers kunnen alles lezen; alleen ingelogde beheerders kunnen plaatsen, importeren, bewerken en verwijderen.

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

## Beheer via de commandoregel

Extra beheerder aanmaken of wachtwoord resetten:

```bash
flask --app run create-admin <gebruikersnaam>
```

## Tests

```bash
python -m pytest
```
