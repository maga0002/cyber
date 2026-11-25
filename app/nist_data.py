"""NIST Cybersecurity Framework (CSF) 2.0 — functies, categorieën en subcategorieën.

De codes en structuur volgen CSF 2.0 (NIST CSWP 29, februari 2024). De Nederlandse
omschrijvingen zijn samenvattingen; raadpleeg voor de officiële tekst
https://www.nist.gov/cyberframework.
"""

VOLWASSENHEID = [
    (0, "Niet aanwezig", "Er is niets geregeld."),
    (1, "Initieel", "Ad hoc, afhankelijk van individuen, niet vastgelegd."),
    (2, "Herhaalbaar", "Wordt regelmatig gedaan, maar niet formeel vastgelegd."),
    (3, "Gedefinieerd", "Vastgelegd in beleid en processen, organisatiebreed toegepast."),
    (4, "Beheerst", "Wordt gemeten, gemonitord en bijgestuurd."),
    (5, "Geoptimaliseerd", "Continu verbeterd op basis van metingen en ervaringen."),
]

STANDAARD_DOEL = 3

FUNCTIES = [
    ("GV", "Govern", "Besturen",
     "De cybersecuritystrategie, verwachtingen en het beleid van de organisatie worden vastgesteld, gecommuniceerd en gemonitord."),
    ("ID", "Identify", "Identificeren",
     "De huidige cybersecurityrisico's voor de organisatie worden begrepen."),
    ("PR", "Protect", "Beschermen",
     "Er worden maatregelen genomen om de cybersecurityrisico's van de organisatie te beheersen."),
    ("DE", "Detect", "Detecteren",
     "Mogelijke cyberaanvallen en compromitteringen worden gevonden en geanalyseerd."),
    ("RS", "Respond", "Reageren",
     "Er wordt actie ondernomen op een gedetecteerd cybersecurity-incident."),
    ("RC", "Recover", "Herstellen",
     "Bedrijfsmiddelen en processen die door een cybersecurity-incident zijn getroffen, worden hersteld."),
]

# (code, Engelse naam, Nederlandse naam, omschrijving)
CATEGORIEEN = [
    ("GV.OC", "Organizational Context", "Organisatiecontext",
     "De omstandigheden rond de cybersecurity-risicobeslissingen (missie, belanghebbenden, wet- en regelgeving) worden begrepen."),
    ("GV.RM", "Risk Management Strategy", "Risicomanagementstrategie",
     "Prioriteiten, randvoorwaarden, risicobereidheid en aannames worden vastgesteld en gebruikt voor operationele risicobeslissingen."),
    ("GV.RR", "Roles, Responsibilities, and Authorities", "Rollen, verantwoordelijkheden en bevoegdheden",
     "Rollen, verantwoordelijkheden en bevoegdheden voor cybersecurity zijn belegd en gecommuniceerd."),
    ("GV.PO", "Policy", "Beleid",
     "Cybersecuritybeleid wordt vastgesteld, gecommuniceerd en gehandhaafd."),
    ("GV.OV", "Oversight", "Toezicht",
     "Resultaten van risicomanagement worden gebruikt om de strategie te evalueren en bij te sturen."),
    ("GV.SC", "Cybersecurity Supply Chain Risk Management", "Ketenrisicomanagement",
     "Risico's in de toeleveringsketen worden geïdentificeerd, beoordeeld en beheerst."),
    ("ID.AM", "Asset Management", "Beheer van bedrijfsmiddelen",
     "Bedrijfsmiddelen (data, hardware, software, systemen, diensten, mensen) zijn bekend en worden beheerd naar belang en risico."),
    ("ID.RA", "Risk Assessment", "Risicobeoordeling",
     "De cybersecurityrisico's voor de organisatie, bedrijfsmiddelen en personen worden begrepen."),
    ("ID.IM", "Improvement", "Verbetering",
     "Verbeteringen in processen en activiteiten worden over alle functies heen geïdentificeerd."),
    ("PR.AA", "Identity Management, Authentication, and Access Control", "Identiteit, authenticatie en toegangsbeheer",
     "Toegang tot middelen is beperkt tot geautoriseerde gebruikers, diensten en hardware, passend bij het risico."),
    ("PR.AT", "Awareness and Training", "Bewustwording en training",
     "Medewerkers krijgen bewustwording en training om hun taken met oog voor cybersecurity uit te voeren."),
    ("PR.DS", "Data Security", "Gegevensbeveiliging",
     "Gegevens worden beheerd conform de risicostrategie om vertrouwelijkheid, integriteit en beschikbaarheid te beschermen."),
    ("PR.PS", "Platform Security", "Platformbeveiliging",
     "Hardware, software en diensten van fysieke en virtuele platforms worden veilig beheerd."),
    ("PR.IR", "Technology Infrastructure Resilience", "Weerbaarheid van de infrastructuur",
     "Beveiligingsarchitecturen worden beheerd om beschikbaarheid en weerbaarheid te waarborgen."),
    ("DE.CM", "Continuous Monitoring", "Continue monitoring",
     "Bedrijfsmiddelen worden gemonitord om afwijkingen, indicatoren van compromittering en andere mogelijk nadelige gebeurtenissen te vinden."),
    ("DE.AE", "Adverse Event Analysis", "Analyse van nadelige gebeurtenissen",
     "Afwijkingen en mogelijk nadelige gebeurtenissen worden geanalyseerd om aanvallen en incidenten te karakteriseren."),
    ("RS.MA", "Incident Management", "Incidentmanagement",
     "Reacties op gedetecteerde cybersecurity-incidenten worden beheerd."),
    ("RS.AN", "Incident Analysis", "Incidentanalyse",
     "Onderzoek wordt uitgevoerd voor een effectieve respons en ondersteuning van forensisch onderzoek en herstel."),
    ("RS.CO", "Incident Response Reporting and Communication", "Rapportage en communicatie bij incidenten",
     "Responsactiviteiten worden afgestemd met interne en externe belanghebbenden, zoals wettelijk vereist."),
    ("RS.MI", "Incident Mitigation", "Incidentbeperking",
     "Activiteiten worden uitgevoerd om uitbreiding van een incident te voorkomen en de gevolgen te beperken."),
    ("RC.RP", "Incident Recovery Plan Execution", "Uitvoering herstelplan",
     "Herstelactiviteiten worden uitgevoerd om systemen en diensten die door incidenten zijn getroffen operationeel te maken."),
    ("RC.CO", "Incident Recovery Communication", "Communicatie bij herstel",
     "Herstelactiviteiten worden afgestemd met interne en externe partijen."),
]

SUBCATEGORIEEN = [
    # GV.OC
    ("GV.OC-01", "De missie van de organisatie is begrepen en vormt de basis voor cybersecurity-risicomanagement."),
    ("GV.OC-02", "Interne en externe belanghebbenden en hun verwachtingen ten aanzien van cybersecurity-risicomanagement zijn begrepen en worden meegewogen."),
    ("GV.OC-03", "Wettelijke, regelgevende en contractuele eisen op het gebied van cybersecurity (inclusief privacy) zijn begrepen en worden beheerd."),
    ("GV.OC-04", "Kritieke doelstellingen, capaciteiten en diensten waar externe belanghebbenden op rekenen zijn begrepen en gecommuniceerd."),
    ("GV.OC-05", "Resultaten, capaciteiten en diensten waarvan de organisatie afhankelijk is zijn begrepen en gecommuniceerd."),
    # GV.RM
    ("GV.RM-01", "Doelstellingen voor risicomanagement zijn vastgesteld en onderschreven door belanghebbenden."),
    ("GV.RM-02", "Risicobereidheid en risicotolerantie zijn vastgesteld, gecommuniceerd en worden onderhouden."),
    ("GV.RM-03", "Cybersecurity-risicomanagement is onderdeel van het organisatiebrede risicomanagement (ERM)."),
    ("GV.RM-04", "Een strategische richting met passende risicoresponsopties is vastgesteld en gecommuniceerd."),
    ("GV.RM-05", "Communicatielijnen voor cybersecurityrisico's, ook van leveranciers en derden, zijn ingericht."),
    ("GV.RM-06", "Een gestandaardiseerde methode voor het berekenen, vastleggen, categoriseren en prioriteren van risico's is vastgesteld."),
    ("GV.RM-07", "Strategische kansen (positieve risico's) worden benoemd en meegenomen in risicodiscussies."),
    # GV.RR
    ("GV.RR-01", "Het leiderschap is verantwoordelijk voor cybersecurityrisico's en bevordert een risicobewuste, ethische en lerende cultuur."),
    ("GV.RR-02", "Rollen, verantwoordelijkheden en bevoegdheden voor cybersecurity-risicomanagement zijn vastgesteld, gecommuniceerd en gehandhaafd."),
    ("GV.RR-03", "Er zijn voldoende middelen toegewezen passend bij de risicostrategie, rollen en beleid."),
    ("GV.RR-04", "Cybersecurity is opgenomen in HR-processen (zoals in- en uitdiensttreding en screening)."),
    # GV.PO
    ("GV.PO-01", "Beleid voor het beheersen van cybersecurityrisico's is vastgesteld op basis van context, strategie en prioriteiten, en wordt gecommuniceerd en gehandhaafd."),
    ("GV.PO-02", "Het beleid wordt periodiek herzien en bijgewerkt bij veranderingen in eisen, dreigingen, technologie en missie."),
    # GV.OV
    ("GV.OV-01", "Resultaten van de risicomanagementstrategie worden beoordeeld om strategie en koers bij te sturen."),
    ("GV.OV-02", "De risicomanagementstrategie wordt herzien om te zorgen dat eisen en risico's voldoende zijn afgedekt."),
    ("GV.OV-03", "De prestaties van cybersecurity-risicomanagement worden geëvalueerd en waar nodig bijgestuurd."),
    # GV.SC
    ("GV.SC-01", "Een programma, strategie, doelen, beleid en processen voor ketenrisicomanagement zijn vastgesteld en onderschreven."),
    ("GV.SC-02", "Cybersecurityrollen en -verantwoordelijkheden van leveranciers, klanten en partners zijn vastgesteld en afgestemd."),
    ("GV.SC-03", "Ketenrisicomanagement is geïntegreerd in cybersecurity- en organisatiebreed risicomanagement."),
    ("GV.SC-04", "Leveranciers zijn bekend en geprioriteerd naar kritikaliteit."),
    ("GV.SC-05", "Eisen om ketenrisico's te beheersen zijn opgenomen in contracten en overeenkomsten met leveranciers en derden."),
    ("GV.SC-06", "Planning en due diligence worden uitgevoerd vóór het aangaan van leveranciersrelaties."),
    ("GV.SC-07", "Risico's van leveranciers, hun producten en diensten worden gedurende de hele relatie beoordeeld en gemonitord."),
    ("GV.SC-08", "Relevante leveranciers en derden zijn betrokken bij incidentplanning, -respons en -herstel."),
    ("GV.SC-09", "Ketenbeveiliging is geïntegreerd in risicomanagementprogramma's en wordt gedurende de levenscyclus gemonitord."),
    ("GV.SC-10", "Ketenrisicomanagementplannen bevatten afspraken voor activiteiten na beëindiging van een samenwerking of dienst."),
    # ID.AM
    ("ID.AM-01", "Een overzicht van de hardware die de organisatie beheert wordt bijgehouden."),
    ("ID.AM-02", "Een overzicht van software, diensten en systemen die de organisatie beheert wordt bijgehouden."),
    ("ID.AM-03", "Overzichten van geautoriseerde netwerkcommunicatie en interne en externe datastromen worden bijgehouden."),
    ("ID.AM-04", "Een overzicht van door leveranciers geleverde diensten wordt bijgehouden."),
    ("ID.AM-05", "Bedrijfsmiddelen zijn geprioriteerd op basis van classificatie, kritikaliteit en impact op de missie."),
    ("ID.AM-07", "Overzichten van gegevens en bijbehorende metadata voor aangewezen gegevenstypen worden bijgehouden."),
    ("ID.AM-08", "Systemen, hardware, software, diensten en gegevens worden gedurende hun hele levenscyclus beheerd."),
    # ID.RA
    ("ID.RA-01", "Kwetsbaarheden in bedrijfsmiddelen worden geïdentificeerd, gevalideerd en vastgelegd."),
    ("ID.RA-02", "Dreigingsinformatie (threat intelligence) wordt ontvangen uit informatiedelingsfora en bronnen."),
    ("ID.RA-03", "Interne en externe dreigingen voor de organisatie worden geïdentificeerd en vastgelegd."),
    ("ID.RA-04", "Mogelijke impact en waarschijnlijkheid van dreigingen die kwetsbaarheden misbruiken worden vastgelegd."),
    ("ID.RA-05", "Dreigingen, kwetsbaarheden, waarschijnlijkheid en impact worden gebruikt om het risico te bepalen en de respons te prioriteren."),
    ("ID.RA-06", "Risicoresponsen worden gekozen, geprioriteerd, gepland, gevolgd en gecommuniceerd."),
    ("ID.RA-07", "Wijzigingen en uitzonderingen worden beheerd, beoordeeld op risico, vastgelegd en gevolgd."),
    ("ID.RA-08", "Processen voor het ontvangen, analyseren en afhandelen van kwetsbaarheidsmeldingen zijn ingericht."),
    ("ID.RA-09", "Echtheid en integriteit van hardware en software worden beoordeeld vóór aanschaf en gebruik."),
    ("ID.RA-10", "Kritieke leveranciers worden beoordeeld vóór aanschaf."),
    # ID.IM
    ("ID.IM-01", "Verbeteringen worden geïdentificeerd uit evaluaties."),
    ("ID.IM-02", "Verbeteringen worden geïdentificeerd uit beveiligingstesten en oefeningen, ook met leveranciers en derden."),
    ("ID.IM-03", "Verbeteringen worden geïdentificeerd uit de uitvoering van operationele processen en activiteiten."),
    ("ID.IM-04", "Incidentresponsplannen en andere operationele cybersecurityplannen zijn vastgesteld, gecommuniceerd, onderhouden en verbeterd."),
    # PR.AA
    ("PR.AA-01", "Identiteiten en inloggegevens van geautoriseerde gebruikers, diensten en hardware worden beheerd."),
    ("PR.AA-02", "Identiteiten worden geverifieerd en gekoppeld aan inloggegevens op basis van de context."),
    ("PR.AA-03", "Gebruikers, diensten en hardware worden geauthenticeerd."),
    ("PR.AA-04", "Identiteitsbeweringen (assertions) worden beschermd, doorgegeven en geverifieerd."),
    ("PR.AA-05", "Toegangsrechten zijn vastgelegd in beleid, worden beheerd, gehandhaafd en herzien, volgens least privilege en functiescheiding."),
    ("PR.AA-06", "Fysieke toegang tot bedrijfsmiddelen wordt beheerd, gemonitord en gehandhaafd passend bij het risico."),
    # PR.AT
    ("PR.AT-01", "Medewerkers krijgen bewustwording en training om algemene taken met oog voor cybersecurityrisico's uit te voeren."),
    ("PR.AT-02", "Medewerkers in gespecialiseerde rollen krijgen specifieke bewustwording en training voor hun taken."),
    # PR.DS
    ("PR.DS-01", "Vertrouwelijkheid, integriteit en beschikbaarheid van opgeslagen gegevens (data-at-rest) zijn beschermd."),
    ("PR.DS-02", "Vertrouwelijkheid, integriteit en beschikbaarheid van gegevens tijdens transport (data-in-transit) zijn beschermd."),
    ("PR.DS-10", "Vertrouwelijkheid, integriteit en beschikbaarheid van gegevens in gebruik (data-in-use) zijn beschermd."),
    ("PR.DS-11", "Back-ups van gegevens worden gemaakt, beschermd, onderhouden en getest."),
    # PR.PS
    ("PR.PS-01", "Configuratiebeheer is ingericht en wordt toegepast."),
    ("PR.PS-02", "Software wordt onderhouden, vervangen en verwijderd passend bij het risico (o.a. patchen)."),
    ("PR.PS-03", "Hardware wordt onderhouden, vervangen en verwijderd passend bij het risico."),
    ("PR.PS-04", "Logregistraties worden gegenereerd en beschikbaar gesteld voor continue monitoring."),
    ("PR.PS-05", "Installatie en uitvoering van niet-geautoriseerde software worden voorkomen."),
    ("PR.PS-06", "Veilige softwareontwikkeling is geïntegreerd in de ontwikkelcyclus en wordt gemonitord."),
    # PR.IR
    ("PR.IR-01", "Netwerken en omgevingen zijn beschermd tegen ongeautoriseerde logische toegang en gebruik."),
    ("PR.IR-02", "Technologische middelen zijn beschermd tegen omgevingsdreigingen (zoals brand, water, stroomuitval)."),
    ("PR.IR-03", "Mechanismen zijn geïmplementeerd om weerbaarheidseisen in normale en verstoorde situaties te halen."),
    ("PR.IR-04", "Er is voldoende capaciteit om beschikbaarheid te waarborgen."),
    # DE.CM
    ("DE.CM-01", "Netwerken en netwerkdiensten worden gemonitord om mogelijk nadelige gebeurtenissen te vinden."),
    ("DE.CM-02", "De fysieke omgeving wordt gemonitord om mogelijk nadelige gebeurtenissen te vinden."),
    ("DE.CM-03", "Activiteiten van medewerkers en technologiegebruik worden gemonitord om mogelijk nadelige gebeurtenissen te vinden."),
    ("DE.CM-06", "Activiteiten en diensten van externe dienstverleners worden gemonitord om mogelijk nadelige gebeurtenissen te vinden."),
    ("DE.CM-09", "Hardware, software, runtime-omgevingen en hun gegevens worden gemonitord om mogelijk nadelige gebeurtenissen te vinden."),
    # DE.AE
    ("DE.AE-02", "Mogelijk nadelige gebeurtenissen worden geanalyseerd om de bijbehorende activiteiten beter te begrijpen."),
    ("DE.AE-03", "Informatie uit meerdere bronnen wordt gecorreleerd."),
    ("DE.AE-04", "De geschatte impact en omvang van nadelige gebeurtenissen worden begrepen."),
    ("DE.AE-06", "Informatie over nadelige gebeurtenissen wordt beschikbaar gesteld aan bevoegde medewerkers en tools."),
    ("DE.AE-07", "Dreigingsinformatie en andere context worden meegenomen in de analyse."),
    ("DE.AE-08", "Incidenten worden uitgeroepen wanneer nadelige gebeurtenissen voldoen aan de vastgestelde incidentcriteria."),
    # RS.MA
    ("RS.MA-01", "Het incidentresponsplan wordt na het uitroepen van een incident uitgevoerd, in afstemming met relevante derden."),
    ("RS.MA-02", "Incidentmeldingen worden getrieerd en gevalideerd."),
    ("RS.MA-03", "Incidenten worden gecategoriseerd en geprioriteerd."),
    ("RS.MA-04", "Incidenten worden waar nodig geëscaleerd."),
    ("RS.MA-05", "De criteria voor het starten van incidentherstel worden toegepast."),
    # RS.AN
    ("RS.AN-03", "Analyse wordt uitgevoerd om vast te stellen wat er tijdens een incident is gebeurd en wat de oorzaak is."),
    ("RS.AN-06", "Acties tijdens een onderzoek worden vastgelegd; integriteit en herkomst van de vastleggingen worden geborgd."),
    ("RS.AN-07", "Incidentgegevens en metadata worden verzameld; integriteit en herkomst worden geborgd."),
    ("RS.AN-08", "De omvang van een incident wordt geschat en gevalideerd."),
    # RS.CO
    ("RS.CO-02", "Interne en externe belanghebbenden worden op de hoogte gesteld van incidenten."),
    ("RS.CO-03", "Informatie wordt gedeeld met aangewezen interne en externe belanghebbenden."),
    # RS.MI
    ("RS.MI-01", "Incidenten worden ingedamd."),
    ("RS.MI-02", "Incidenten worden uitgeroeid (oorzaak verwijderd)."),
    # RC.RP
    ("RC.RP-01", "Het herstelgedeelte van het incidentresponsplan wordt uitgevoerd zodra het vanuit de incidentrespons is gestart."),
    ("RC.RP-02", "Herstelacties worden geselecteerd, afgebakend, geprioriteerd en uitgevoerd."),
    ("RC.RP-03", "De integriteit van back-ups en andere herstelmiddelen wordt gecontroleerd vóór gebruik."),
    ("RC.RP-04", "Kritieke bedrijfsfuncties en risicomanagement worden meegewogen bij het vaststellen van de normale situatie na een incident."),
    ("RC.RP-05", "De integriteit van herstelde middelen wordt gecontroleerd, systemen en diensten worden hersteld en de normale situatie wordt bevestigd."),
    ("RC.RP-06", "Het einde van het herstel wordt op basis van criteria vastgesteld en de incidentdocumentatie wordt afgerond."),
    # RC.CO
    ("RC.CO-03", "Herstelactiviteiten en voortgang worden gecommuniceerd aan aangewezen interne en externe belanghebbenden."),
    ("RC.CO-04", "Publieke updates over het herstel worden gedeeld via goedgekeurde kanalen en boodschappen."),
]
