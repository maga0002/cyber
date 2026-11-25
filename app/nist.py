"""NIST CSF: initiële vulling, scoreberekening, import en export."""
import io
from datetime import date, datetime

import pandas as pd
from sqlalchemy.orm import selectinload

from . import nist_data
from .database import db
from .importer import ImportFout, lees_bestand
from .models import NistActie, NistBewijs, NistCategorie, NistFunctie, NistSubcategorie, nu

NIVEAU_NAMEN = {n: naam for n, naam, _ in nist_data.VOLWASSENHEID}


# ---------------------------------------------------------------- vullen

def vul_framework():
    """Voegt ontbrekende functies/categorieën/subcategorieën toe (idempotent)."""
    functies = {f.code: f for f in NistFunctie.query.all()}
    for i, (code, en, nl, oms) in enumerate(nist_data.FUNCTIES):
        if code not in functies:
            functies[code] = NistFunctie(code=code, naam_en=en, naam=nl, omschrijving=oms, volgorde=i)
            db.session.add(functies[code])
    db.session.flush()

    categorieen = {c.code: c for c in NistCategorie.query.all()}
    for i, (code, en, nl, oms) in enumerate(nist_data.CATEGORIEEN):
        if code not in categorieen:
            categorieen[code] = NistCategorie(code=code, naam_en=en, naam=nl, omschrijving=oms,
                                              functie=functies[code[:2]])
            db.session.add(categorieen[code])
        categorieen[code].volgorde = i
    db.session.flush()

    bestaande = {s.code for s in NistSubcategorie.query.with_entities(NistSubcategorie.code)}
    for code, oms in nist_data.SUBCATEGORIEEN:
        if code not in bestaande:
            db.session.add(NistSubcategorie(code=code, omschrijving=oms, doel=nist_data.STANDAARD_DOEL,
                                            categorie=categorieen[code.split("-")[0]]))
    db.session.commit()


# ---------------------------------------------------------------- scores

def bereken(subs) -> dict:
    van_toepassing = [s for s in subs if not s.nvt]
    beoordeeld = [s for s in van_toepassing if s.huidig is not None]
    huidig = round(sum(s.huidig for s in beoordeeld) / len(beoordeeld), 1) if beoordeeld else None
    doelen = [s.doel for s in van_toepassing if s.doel is not None]
    doel = round(sum(doelen) / len(doelen), 1) if doelen else None
    return {
        "huidig": huidig,
        "doel": doel,
        "gat": round(doel - huidig, 1) if huidig is not None and doel is not None else None,
        "beoordeeld": len(beoordeeld),
        "totaal": len(van_toepassing),
        "nvt": len(subs) - len(van_toepassing),
        "kleur": kleur(huidig, doel),
        "voortgang": round(100 * len(beoordeeld) / len(van_toepassing)) if van_toepassing else 0,
    }


def kleur(huidig, doel) -> str:
    if huidig is None:
        return "grijs"
    if doel is None or huidig >= doel:
        return "groen"
    if doel - huidig <= 1:
        return "oranje"
    return "rood"


def laad_functies():
    return (NistFunctie.query
            .options(selectinload(NistFunctie.categorieen).selectinload(NistCategorie.subcategorieen))
            .order_by(NistFunctie.volgorde).all())


def overzicht() -> dict:
    functies = laad_functies()
    alle_subs = []
    per_functie, per_categorie = {}, {}
    for f in functies:
        f_subs = []
        for c in f.categorieen:
            per_categorie[c.code] = bereken(c.subcategorieen)
            f_subs.extend(c.subcategorieen)
        per_functie[f.code] = bereken(f_subs)
        alle_subs.extend(f_subs)

    acties = NistActie.query.all()
    open_acties = [a for a in acties if not a.afgerond]
    actie_telling = {}
    for a in open_acties:
        code = a.categorie.code
        actie_telling[code] = actie_telling.get(code, 0) + 1
        actie_telling[code[:2]] = actie_telling.get(code[:2], 0) + 1

    grootste_gaten = sorted(
        (s for s in alle_subs if not s.nvt and s.huidig is not None and (s.doel or 0) > s.huidig),
        key=lambda s: (s.huidig - (s.doel or 0), s.code),
    )[:10]

    return {
        "functies": functies,
        "per_functie": per_functie,
        "per_categorie": per_categorie,
        "totaal": bereken(alle_subs),
        "acties": {
            "totaal": len(acties),
            "open": len(open_acties),
            "te_laat": sum(1 for a in open_acties if a.te_laat),
            "gereed": sum(1 for a in acties if a.status == "Gereed"),
            "per_code": actie_telling,
        },
        "grootste_gaten": grootste_gaten,
    }


FUNCTIE_KLEUREN = {"GV": "#475569", "ID": "#2563eb", "PR": "#7c3aed", "DE": "#0891b2", "RS": "#db2777", "RC": "#4f46e5"}


def radar_grafiek(ov: dict) -> dict:
    return {
        "type": "radar",
        "labels": [f.naam for f in ov["functies"]],
        "datasets": [
            {"label": "Huidig", "data": [ov["per_functie"][f.code]["huidig"] for f in ov["functies"]], "kleur": "#2563eb"},
            {"label": "Doel", "data": [ov["per_functie"][f.code]["doel"] for f in ov["functies"]], "kleur": "#94a3b8", "stippel": True},
        ],
    }


def trend_grafiek(ov: dict, metingen) -> dict:
    datasets = [{"label": "Totaal", "data": [m.totaal for m in metingen], "kleur": "#0b1f44", "dik": True}]
    for f in ov["functies"]:
        datasets.append({"label": f.naam, "data": [m.data.get("functies", {}).get(f.code) for m in metingen],
                         "kleur": FUNCTIE_KLEUREN.get(f.code, "#999")})
    return {"type": "line", "labels": [m.label for m in metingen], "datasets": datasets}


def categorie_grafiek(f, ov: dict) -> dict:
    return {
        "type": "bar",
        "labels": [c.code for c in f.categorieen],
        "titels": [c.naam for c in f.categorieen],
        "datasets": [
            {"label": "Huidig", "data": [ov["per_categorie"][c.code]["huidig"] for c in f.categorieen], "kleur": "#2563eb"},
            {"label": "Doel", "data": [ov["per_categorie"][c.code]["doel"] for c in f.categorieen], "kleur": "#cbd5e1"},
        ],
    }


def bewijs_statistiek() -> dict:
    """Hoeveel (van toepassing zijnde) subcategorieën zijn onderbouwd met bewijs, per functie."""
    subs = (NistSubcategorie.query.filter(NistSubcategorie.nvt.is_(False))
            .options(selectinload(NistSubcategorie.bewijzen)).all())
    per_functie = {}
    for s in subs:
        f = per_functie.setdefault(s.code[:2], {"met": 0, "totaal": 0})
        f["totaal"] += 1
        f["met"] += 1 if s.bewijzen else 0
    alle = NistBewijs.query.all()
    met = sum(1 for s in subs if s.bewijzen)
    return {
        "met": met, "totaal": len(subs),
        "procent": round(100 * met / len(subs)) if subs else 0,
        "stukken": len(alle),
        "verlopen": sum(1 for b in alle if b.verlopen),
        "per_functie": per_functie,
    }


def momentopname_data(ov: dict) -> dict:
    return {
        "functies": {k: v["huidig"] for k, v in ov["per_functie"].items()},
        "categorieen": {k: v["huidig"] for k, v in ov["per_categorie"].items()},
    }


# ---------------------------------------------------------------- import

KOLOM_ALIASSEN = {
    "code": ["code", "subcategorie", "subcategory", "id", "nist", "nist code", "control", "maatregel code"],
    "huidig": ["huidig", "huidige score", "score", "niveau", "huidig niveau", "volwassenheid", "current", "current score", "maturity"],
    "doel": ["doel", "doelniveau", "doelscore", "gewenst", "gewenst niveau", "target", "target score"],
    "toelichting": ["toelichting", "opmerking", "opmerkingen", "onderbouwing", "bewijs", "notes", "comment"],
    "eigenaar": ["eigenaar", "owner", "verantwoordelijke"],
    "nvt": ["nvt", "n.v.t.", "niet van toepassing", "not applicable"],
    "actie": ["actie", "titel", "action", "verbeteractie", "maatregel"],
    "omschrijving": ["omschrijving", "beschrijving", "description"],
    "status": ["status"],
    "prioriteit": ["prioriteit", "priority"],
    "deadline": ["deadline", "einddatum", "due date", "streefdatum", "datum gereed"],
}


def _zoek_kolommen(kolommen: list[str]) -> dict:
    lager = {k.lower().strip(): k for k in kolommen}
    gevonden = {}
    for veld, aliassen in KOLOM_ALIASSEN.items():
        for alias in aliassen:
            if alias in lager:
                gevonden[veld] = lager[alias]
                break
    return gevonden


def _niveau(waarde):
    """Geeft (niveau, nvt) terug. Accepteert 0-5, '3 - Gedefinieerd', 'n.v.t.'."""
    if waarde in (None, ""):
        return None, False
    tekst = str(waarde).strip().lower()
    if tekst in ("nvt", "n.v.t.", "n.v.t", "na", "n/a"):
        return None, True
    try:
        getal = int(round(float(tekst.split()[0].replace(",", "."))))
    except (ValueError, IndexError):
        for n, naam in NIVEAU_NAMEN.items():
            if naam.lower() in tekst:
                return n, False
        return None, False
    return max(0, min(5, getal)), False


def _code(waarde) -> str:
    return str(waarde or "").strip().upper().replace(" ", "")


def importeer(bestandsnaam: str, inhoud: bytes) -> dict:
    kolommen, rijen = lees_bestand(bestandsnaam, inhoud)
    k = _zoek_kolommen(kolommen)
    if "code" not in k:
        raise ImportFout("Geen kolom met NIST-codes gevonden. Noem de kolom bijvoorbeeld 'Code' (waarden zoals GV.OC-01).")

    subs = {s.code: s for s in NistSubcategorie.query.all()}
    cats = {c.code: c for c in NistCategorie.query.all()}
    resultaat = {"beoordelingen": 0, "acties": 0, "onbekend": []}

    for rij in rijen:
        code = _code(rij.get(k["code"]))
        if not code:
            continue
        sub = subs.get(code)
        cat = sub.categorie if sub else cats.get(code)
        if not cat:
            resultaat["onbekend"].append(code)
            continue

        if "actie" in k and rij.get(k["actie"]):
            resultaat["acties"] += 1
            db.session.add(_actie_uit_rij(rij, k, cat, sub))
            continue

        if not sub:
            resultaat["onbekend"].append(code)
            continue
        gewijzigd = False
        if "huidig" in k:
            niveau, nvt = _niveau(rij.get(k["huidig"]))
            if niveau is not None or nvt:
                sub.huidig, sub.nvt, gewijzigd = niveau, nvt, True
        if "nvt" in k and str(rij.get(k["nvt"]) or "").strip().lower() in ("ja", "j", "x", "yes", "true", "1", "nvt"):
            sub.nvt, gewijzigd = True, True
        if "doel" in k:
            niveau, _ = _niveau(rij.get(k["doel"]))
            if niveau is not None:
                sub.doel, gewijzigd = niveau, True
        for veld in ("toelichting", "eigenaar"):
            if veld in k and rij.get(k[veld]) not in (None, ""):
                setattr(sub, veld, str(rij.get(k[veld])))
                gewijzigd = True
        if gewijzigd:
            sub.beoordeeld_op = nu()
            resultaat["beoordelingen"] += 1

    db.session.commit()
    return resultaat


def _actie_uit_rij(rij, k, cat, sub) -> NistActie:
    status = str(rij.get(k.get("status")) or "Open").strip().capitalize() if "status" in k else "Open"
    status = next((s for s in NistActie.STATUSSEN if s.lower() == status.lower()), "Open")
    prio = str(rij.get(k.get("prioriteit")) or "Middel").strip().capitalize() if "prioriteit" in k else "Middel"
    prio = prio if prio in NistActie.PRIORITEITEN else "Middel"
    return NistActie(
        categorie=cat, subcategorie=sub,
        titel=str(rij.get(k["actie"]))[:200],
        omschrijving=str(rij.get(k["omschrijving"]) or "") if "omschrijving" in k else "",
        eigenaar=str(rij.get(k["eigenaar"]) or "") if "eigenaar" in k else "",
        status=status, prioriteit=prio,
        deadline=parse_datum(rij.get(k["deadline"])) if "deadline" in k else None,
    )


def parse_datum(waarde) -> date | None:
    if waarde in (None, ""):
        return None
    if isinstance(waarde, datetime):
        return waarde.date()
    if isinstance(waarde, date):
        return waarde
    tekst = str(waarde).strip()
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%Y-%m-%dT%H:%M:%S", "%d.%m.%Y"):
        try:
            return datetime.strptime(tekst[:19], fmt).date()
        except ValueError:
            continue
    return None


# ---------------------------------------------------------------- export

def exporteer_excel(met_bewijs: bool = False) -> bytes:
    ov = overzicht()
    functies = ov["functies"]

    samenvatting = [{
        "Functie": f"{f.code} {f.naam} ({f.naam_en})",
        "Huidig": ov["per_functie"][f.code]["huidig"],
        "Doel": ov["per_functie"][f.code]["doel"],
        "Gat": ov["per_functie"][f.code]["gat"],
        "Beoordeeld": f'{ov["per_functie"][f.code]["beoordeeld"]}/{ov["per_functie"][f.code]["totaal"]}',
        "Open acties": ov["acties"]["per_code"].get(f.code, 0),
    } for f in functies]

    categorieen, subs = [], []
    for f in functies:
        for c in f.categorieen:
            s = ov["per_categorie"][c.code]
            categorieen.append({"Code": c.code, "Categorie": c.naam, "Category (EN)": c.naam_en,
                                "Huidig": s["huidig"], "Doel": s["doel"], "Gat": s["gat"],
                                "Beoordeeld": f'{s["beoordeeld"]}/{s["totaal"]}',
                                "Open acties": ov["acties"]["per_code"].get(c.code, 0),
                                "Toelichting": c.toelichting or ""})
            for sc in c.subcategorieen:
                subs.append({"Code": sc.code, "Omschrijving": sc.omschrijving,
                             "Huidig": "n.v.t." if sc.nvt else sc.huidig,
                             "Doel": None if sc.nvt else sc.doel,
                             "Eigenaar": sc.eigenaar or "", "Toelichting": sc.toelichting or "",
                             **({"Bewijsstukken": len(sc.bewijzen)} if met_bewijs else {}),
                             "Beoordeeld op": sc.beoordeeld_op.strftime("%Y-%m-%d") if sc.beoordeeld_op else ""})

    acties = [{"Code": (a.subcategorie.code if a.subcategorie else a.categorie.code), "Actie": a.titel,
               "Omschrijving": a.omschrijving or "", "Eigenaar": a.eigenaar or "", "Status": a.status,
               "Prioriteit": a.prioriteit, "Deadline": a.deadline.isoformat() if a.deadline else "",
               "Te laat": "ja" if a.te_laat else ""}
              for a in NistActie.query.order_by(NistActie.deadline).all()]

    bladen = [("Samenvatting", samenvatting), ("Categorieën", categorieen),
              ("Subcategorieën", subs), ("Acties", acties)]
    if met_bewijs:
        bewijzen = [{"Code": b.subcategorie.code, "Titel": b.titel, "Omschrijving": b.omschrijving or "",
                     "Soort": "Bestand" if b.is_bestand else "Link",
                     "Bestand / link": b.bestandsnaam if b.is_bestand else b.url,
                     "Geldig tot": b.geldig_tot.isoformat() if b.geldig_tot else "",
                     "Verlopen": "ja" if b.verlopen else "",
                     "Toegevoegd door": b.toegevoegd_door or "",
                     "Toegevoegd op": b.created_at.strftime("%Y-%m-%d") if b.created_at else ""}
                    for b in NistBewijs.query.join(NistSubcategorie).join(NistCategorie)
                    .order_by(NistCategorie.volgorde, NistSubcategorie.code).all()]
        bladen.append(("Bewijsstukken", bewijzen))

    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as xl:
        for naam, data in bladen:
            df = pd.DataFrame(data) if data else pd.DataFrame({"": []})
            df.to_excel(xl, sheet_name=naam, index=False)
            blad = xl.sheets[naam]
            for i, kolom in enumerate(df.columns, start=1):
                breedte = max([len(str(kolom))] + [len(str(v)) for v in df[kolom].head(200)]) + 2
                blad.column_dimensions[blad.cell(row=1, column=i).column_letter].width = min(breedte, 70)
    return buf.getvalue()


def sjabloon_csv() -> str:
    regels = ["Code;Huidig;Doel;Eigenaar;Toelichting"]
    regels += [f"{code};;{nist_data.STANDAARD_DOEL};;" for code, _ in nist_data.SUBCATEGORIEEN]
    return "\n".join(regels) + "\n"
