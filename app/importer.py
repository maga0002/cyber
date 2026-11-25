"""Lijsten (CSV / Excel) inlezen en dashboard-statistieken berekenen."""
import io
import math
from collections import Counter

import pandas as pd

TOEGESTANE_EXTENSIES = {".csv", ".txt", ".xlsx", ".xls"}
MAX_CATEGORIEEN = 25


class ImportFout(Exception):
    pass


def lees_bestand(bestandsnaam: str, inhoud: bytes) -> tuple[list[str], list[dict]]:
    naam = bestandsnaam.lower()
    ext = naam[naam.rfind("."):] if "." in naam else ""
    if ext not in TOEGESTANE_EXTENSIES:
        raise ImportFout("Alleen CSV- of Excel-bestanden (.csv, .xlsx, .xls) zijn toegestaan.")

    try:
        if ext in {".xlsx", ".xls"}:
            df = pd.read_excel(io.BytesIO(inhoud))
        else:
            tekst = _decodeer(inhoud)
            # sep=None laat pandas het scheidingsteken raden (, ; tab)
            df = pd.read_csv(io.StringIO(tekst), sep=None, engine="python")
    except ImportFout:
        raise
    except Exception as exc:  # noqa: BLE001
        raise ImportFout(f"Bestand kon niet worden gelezen: {exc}") from exc

    df = df.dropna(how="all")
    df.columns = [str(c).strip() or f"Kolom {i + 1}" for i, c in enumerate(df.columns)]
    if df.empty or not len(df.columns):
        raise ImportFout("Het bestand bevat geen gegevens.")

    rijen = []
    for record in df.to_dict(orient="records"):
        rijen.append({k: _schoon(v) for k, v in record.items()})
    return list(df.columns), rijen


def _decodeer(inhoud: bytes) -> str:
    for codering in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            return inhoud.decode(codering)
        except UnicodeDecodeError:
            continue
    raise ImportFout("Onbekende tekstcodering.")


def _schoon(waarde):
    if waarde is None:
        return None
    if isinstance(waarde, float) and math.isnan(waarde):
        return None
    if isinstance(waarde, pd.Timestamp):
        return waarde.isoformat()
    if hasattr(waarde, "item"):  # numpy-types
        waarde = waarde.item()
    if isinstance(waarde, float) and waarde.is_integer():
        return int(waarde)
    if isinstance(waarde, str):
        return waarde.strip()
    return waarde


def _is_getal(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def analyseer(columns: list[str], rijen: list[dict]) -> dict:
    """Bepaalt per kolom of hij numeriek of categorisch is en berekent cijfers."""
    numeriek, categorisch = [], []
    for kolom in columns:
        waarden = [r.get(kolom) for r in rijen if r.get(kolom) not in (None, "")]
        if not waarden:
            continue
        if all(_is_getal(v) for v in waarden):
            numeriek.append({
                "kolom": kolom,
                "som": round(sum(waarden), 2),
                "gemiddelde": round(sum(waarden) / len(waarden), 2),
                "min": min(waarden),
                "max": max(waarden),
                "aantal": len(waarden),
            })
        else:
            telling = Counter(str(v) for v in waarden)
            # Kolommen waarin elke waarde uniek is (namen, ID's, datums) zijn geen categorie.
            alles_uniek = len(waarden) > 3 and len(telling) == len(waarden)
            if len(telling) <= MAX_CATEGORIEEN and not alles_uniek:
                categorisch.append({
                    "kolom": kolom,
                    "labels": [k for k, _ in telling.most_common()],
                    "waarden": [n for _, n in telling.most_common()],
                    "leeg": len(rijen) - len(waarden),
                })
    return {"aantal_rijen": len(rijen), "numeriek": numeriek, "categorisch": categorisch}


def kies_standaard_groepkolom(analyse: dict) -> str | None:
    """Voorkeur voor een kolom die naar status/score klinkt, anders de eerste categorische."""
    voorkeur = ("status", "score", "niveau", "risico", "prioriteit", "categorie")
    for cat in analyse["categorisch"]:
        if any(w in cat["kolom"].lower() for w in voorkeur):
            return cat["kolom"]
    return analyse["categorisch"][0]["kolom"] if analyse["categorisch"] else None
