"""Voorbeelddata: vult de app met fictieve nieuwsberichten, dashboards en een NIST-beoordeling.

Alle organisaties, personen, systemen en links zijn verzonnen.
"""
import os
from datetime import date, datetime, timedelta, timezone

from . import nist
from .database import db
from .importer import kies_standaard_groepkolom, analyseer, lees_bestand
from .models import (Dataset, DatasetRow, NewsPost, NistActie, NistBewijs, NistCategorie,
                     NistFunctie, NistMeting, NistSubcategorie)

MAP = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "voorbeelden")

DASHBOARDS = [  # (bestand, naam, omschrijving, kolom voor de hoofdgrafiek)
    ("maatregelen.csv", "Maatregelen cyberweerbaarheid",
     "Voortgang van de belangrijkste beveiligingsmaatregelen uit het jaarplan.", "Status"),
    ("kwetsbaarheden.csv", "Kwetsbaarheden",
     "Uitkomsten van de maandelijkse kwetsbaarheidsscans en de afhandeling daarvan.", "Status"),
    ("phishing_simulatie.csv", "Phishingsimulaties",
     "Resultaten van de phishingtests in Q3 en Q4, per afdeling.", "Resultaat"),
    ("incidenten.csv", "Beveiligingsincidenten 2026",
     "Geregistreerde beveiligingsincidenten dit jaar.", "Type incident"),
]

NIEUWS = [
    (2, "Waarschuwing", True, "Let op: nepmails over 'verlopen wachtwoord'",
     "Sinds vanochtend ontvangen collega's e-mails waarin staat dat hun wachtwoord verloopt. "
     "De link leidt naar een nagemaakte inlogpagina.\n\n"
     "Klik niet op de link en vul nergens je gegevens in. Gebruik de knop 'Phishing melden' in Outlook "
     "of stuur de mail door naar de servicedesk. Heb je al wel iets ingevuld? Bel dan direct de servicedesk."),
    (9, "Update", False, "MFA verplicht voor iedereen vanaf 1 december",
     "Vanaf 1 december is inloggen met multifactorauthenticatie (MFA) verplicht voor alle accounts. "
     "Daarmee verkleinen we de kans dat een gestolen wachtwoord tot misbruik leidt aanzienlijk.\n\n"
     "Heb je de authenticator-app nog niet ingesteld? Volg de handleiding op het intranet of loop "
     "binnen bij het ICT-spreekuur op dinsdag en donderdag."),
    (16, "Tip", False, "Tip: vergrendel je scherm",
     "Loop je even weg van je werkplek? Vergrendel je scherm met Windows-toets + L (Mac: Control + Command + Q). "
     "Zo voorkom je dat iemand anders meekijkt of jouw account gebruikt."),
    (23, "Algemeen", False, "Resultaten phishingtest Q4",
     "In oktober hebben we een phishingsimulatie gehouden. Het aantal collega's dat op de link klikte "
     "is gedaald ten opzichte van de vorige test, en er werd vaker gemeld. Goed werk!\n\n"
     "De resultaten per afdeling staan op het dashboard Phishingsimulaties."),
    (37, "Incident", False, "Storing VPN opgelost",
     "Op 12 oktober was de VPN-verbinding enkele uren niet beschikbaar door een fout in een update van de "
     "VPN-gateway. Er is geen sprake geweest van een aanval. De update is teruggedraaid en de leverancier "
     "werkt aan een oplossing."),
]

TOELICHTING_FUNCTIES = {
    "GV": "De CISO rapporteert elk kwartaal aan de directie over de stand van zaken. Het "
          "informatiebeveiligingsbeleid is in 2025 vastgesteld en wordt jaarlijks herzien. "
          "Aandachtspunt is het vastleggen van onze risicobereidheid.",
    "ID": "We houden een overzicht bij van alle systemen en leveranciers. Maandelijks scannen we op "
          "kwetsbaarheden; de resultaten staan op het dashboard Kwetsbaarheden.",
    "PR": "Alle medewerkers loggen in met MFA, laptops zijn versleuteld en er wordt dagelijks een "
          "back-up gemaakt. Elk jaar volgt iedereen de e-learning informatiebeveiliging.",
    "DE": "Logging van servers en firewalls komt samen in ons SIEM. Het Security Team bekijkt meldingen "
          "op werkdagen. Monitoring buiten kantoortijd is nog in ontwikkeling.",
    "RS": "Er is een incidentresponsplan met een vast meldpunt (de servicedesk). Datalekken worden "
          "binnen 72 uur beoordeeld en waar nodig gemeld bij de Autoriteit Persoonsgegevens.",
    "RC": "Herstelprocedures voor de belangrijkste systemen zijn beschreven. In 2027 oefenen we voor het "
          "eerst een volledige hersteltest met de directie.",
}

TOELICHTING_CATEGORIEEN = {
    "PR.AA": "Alle medewerkers loggen in via één centraal account met MFA. Beheerders hebben een apart "
             "beheeraccount.\n\nWat moet jij doen? Deel nooit je MFA-code en keur geen inlogverzoeken goed "
             "die je niet zelf hebt gestart.",
    "PR.AT": "Iedereen volgt jaarlijks de e-learning en we houden elk kwartaal een phishingsimulatie.",
    "RS.MA": "Meld een (vermoedelijk) incident altijd direct bij de servicedesk, ook buiten kantoortijd.",
}

BEWIJS = [
    ("GV.PO-01", "Informatiebeveiligingsbeleid 2025", "https://intranet.example/beleid/informatiebeveiliging",
     "Vastgesteld door de directie", 400),
    ("GV.RR-02", "RACI informatiebeveiliging", "https://intranet.example/beleid/raci", "", 200),
    ("ID.AM-01", "Export CMDB hardware", "https://cmdb.example/rapporten/hardware", "", 30),
    ("ID.RA-01", "Rapport kwetsbaarheidsscan oktober", "https://security.example/scans/2026-10", "", 60),
    ("PR.AA-03", "Configuratie MFA", "https://intranet.example/ict/mfa-configuratie", "Screenshot van het beleid", 300),
    ("PR.AT-01", "Deelnameoverzicht e-learning 2026", "https://lms.example/rapport/2026", "", 120),
    ("PR.DS-11", "Verslag hersteltest back-ups Q2", "https://intranet.example/ict/hersteltest-q2", "", -10),
    ("RS.MA-01", "Incidentresponsplan v2.1", "https://intranet.example/security/irp", "", 200),
]


def is_leeg() -> bool:
    return (NewsPost.query.count() == 0 and Dataset.query.count() == 0 and NistActie.query.count() == 0
            and NistSubcategorie.query.filter(NistSubcategorie.huidig.isnot(None)).count() == 0)


def _lees(naam: str):
    with open(os.path.join(MAP, naam), "rb") as f:
        return lees_bestand(naam, f.read())


def laad_voorbeelddata(gebruiker=None) -> dict:
    nu = datetime.now(timezone.utc)

    for dagen, cat, vast, titel, tekst in NIEUWS:
        tijd = nu - timedelta(days=dagen)
        db.session.add(NewsPost(title=titel, body=tekst, category=cat, pinned=vast, published=True,
                                created_at=tijd, updated_at=tijd, author=gebruiker))

    # In omgekeerde volgorde, zodat de maatregelen bovenaan het overzicht staan
    for i, (bestand, naam, oms, groep) in enumerate(reversed(DASHBOARDS)):
        kolommen, rijen = _lees(bestand)
        tijd = nu - timedelta(minutes=len(DASHBOARDS) - i)
        ds = Dataset(name=naam, description=oms, source_filename=bestand, columns=kolommen,
                     group_column=groep if groep in kolommen else kies_standaard_groepkolom(analyseer(kolommen, rijen)),
                     created_at=tijd, updated_at=tijd)
        ds.rows = [DatasetRow(position=i, data=r) for i, r in enumerate(rijen)]
        db.session.add(ds)
    db.session.commit()

    # NIST: eerst een oudere stand vastleggen voor de trend, dan de huidige beoordeling
    for bestand in ("nist_beoordeling.csv", "nist_acties.csv"):
        with open(os.path.join(MAP, bestand), "rb") as f:
            nist.importeer(bestand, f.read())
    _maak_trend(nu)

    for code, tekst in TOELICHTING_FUNCTIES.items():
        NistFunctie.query.filter_by(code=code).one().toelichting = tekst
    for code, tekst in TOELICHTING_CATEGORIEEN.items():
        NistCategorie.query.filter_by(code=code).one().toelichting = tekst

    subs = {s.code: s for s in NistSubcategorie.query.all()}
    for code, titel, url, oms, geldig in BEWIJS:
        db.session.add(NistBewijs(subcategorie=subs[code], titel=titel, url=url, omschrijving=oms,
                                  geldig_tot=date.today() + timedelta(days=geldig),
                                  toegevoegd_door=gebruiker.username if gebruiker else "voorbeeld"))
    db.session.commit()
    return {"nieuws": len(NIEUWS), "dashboards": len(DASHBOARDS), "bewijs": len(BEWIJS)}


def _maak_trend(nu: datetime):
    """Twee eerdere momentopnames (lager dan nu) plus de huidige."""
    ov = nist.overzicht()
    huidig = nist.momentopname_data(ov)
    for label, dagen, verschil in (("2026 Q2", 150, 0.9), ("2026 Q3", 60, 0.4)):
        data = {soort: {k: (round(max(0, v - verschil), 1) if v is not None else None) for k, v in waarden.items()}
                for soort, waarden in huidig.items()}
        db.session.add(NistMeting(label=label, datum=nu - timedelta(days=dagen),
                                  totaal=round(max(0, ov["totaal"]["huidig"] - verschil), 1), data=data))
    db.session.add(NistMeting(label="2026 Q4", datum=nu, totaal=ov["totaal"]["huidig"], data=huidig))
    db.session.commit()


def wis_inhoud():
    """Verwijdert alle inhoud (nieuws, dashboards, NIST-beoordeling, acties, bewijs, momentopnames).
    Gebruikersaccounts en het NIST-framework zelf blijven staan."""
    NistBewijs.query.delete()
    NistActie.query.delete()
    NistMeting.query.delete()
    DatasetRow.query.delete()
    Dataset.query.delete()
    NewsPost.query.delete()
    NistSubcategorie.query.update({"huidig": None, "doel": 3, "nvt": False, "toelichting": "",
                                   "eigenaar": "", "beoordeeld_op": None})
    NistCategorie.query.update({"toelichting": ""})
    NistFunctie.query.update({"toelichting": ""})
    db.session.commit()
