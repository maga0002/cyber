import io

import pytest

from app import create_app
from app.models import Instelling, NistActie, NistCategorie, NistFunctie, NistMeting, NistSubcategorie
from app.database import db
from app import nist


@pytest.fixture()
def app(tmp_path):
    return create_app({"TESTING": True, "TESTING_SKIP_CSRF": True,
                       "SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmp_path / 't.db'}"})


@pytest.fixture()
def admin(app):
    c = app.test_client()
    c.post("/setup", data={"username": "beheer", "password": "geheim123", "password2": "geheim123"})
    return c


def test_framework_gevuld_en_idempotent(app):
    with app.app_context():
        assert NistFunctie.query.count() == 6
        assert NistCategorie.query.count() == 22
        assert NistSubcategorie.query.count() == 106
        nist.vul_framework()
        assert NistSubcategorie.query.count() == 106


def test_alle_paginas_laden(app, admin):
    for url in ["/nist/", "/nist/functie/PR", "/nist/categorie/PR.AA", "/nist/acties", "/nist/rapport",
                "/nist/importeren", "/nist/acties/nieuw?sub=PR.AA-01", "/", "/nist/sjabloon.csv"]:
        assert admin.get(url).status_code == 200, url


def test_beoordeling_opslaan_en_score(app, admin):
    with app.app_context():
        subs = NistCategorie.query.filter_by(code="PR.AT").one().subcategorieen
        ids = [s.id for s in subs]
    admin.post("/nist/categorie/PR.AT/beoordeling", data={
        f"huidig_{ids[0]}": "2", f"doel_{ids[0]}": "4",
        f"huidig_{ids[1]}": "4", f"doel_{ids[1]}": "4", f"toelichting_{ids[1]}": "Jaarlijkse training"})
    with app.app_context():
        s = nist.bereken(NistCategorie.query.filter_by(code="PR.AT").one().subcategorieen)
        assert s["huidig"] == 3.0 and s["doel"] == 4.0 and s["kleur"] == "oranje" and s["beoordeeld"] == 2


def test_nvt_telt_niet_mee(app):
    with app.app_context():
        subs = NistCategorie.query.filter_by(code="RS.MI").one().subcategorieen
        subs[0].huidig, subs[1].nvt = 1, True
        s = nist.bereken(subs)
        assert s["totaal"] == 1 and s["nvt"] == 1 and s["huidig"] == 1


def test_import_beoordeling_en_acties(app, admin):
    with open("voorbeelden/nist_beoordeling.csv", "rb") as f:
        admin.post("/nist/importeren", data={"bestand": (f, "b.csv")}, content_type="multipart/form-data")
    with open("voorbeelden/nist_acties.csv", "rb") as f:
        admin.post("/nist/importeren", data={"bestand": (f, "a.csv")}, content_type="multipart/form-data")
    with app.app_context():
        assert NistSubcategorie.query.filter(NistSubcategorie.huidig.isnot(None)).count() == 106
        assert NistActie.query.count() == 10
        a = NistActie.query.filter_by(titel="Incidentresponsplan herzien").one()
        assert a.categorie.code == "RS.MA" and a.subcategorie is None and a.deadline.year == 2026
        assert NistActie.query.filter_by(titel="CMDB actualiseren").one().status == "Gereed"


def test_import_niveau_varianten(app):
    with app.app_context():
        assert nist._niveau("3 - Gedefinieerd") == (3, False)
        assert nist._niveau("n.v.t.") == (None, True)
        assert nist._niveau("Beheerst") == (4, False)
        assert nist._niveau(7) == (5, False)


def test_actie_crud_en_te_laat(app, admin):
    admin.post("/nist/acties/nieuw", data={"koppeling": "DE.CM-01", "titel": "SIEM", "status": "Open",
                                           "prioriteit": "Hoog", "deadline": "2020-01-01"})
    with app.app_context():
        a = NistActie.query.one()
        assert a.te_laat and a.subcategorie.code == "DE.CM-01" and a.categorie.code == "DE.CM"
        aid = a.id
    admin.post(f"/nist/acties/{aid}/status", data={"status": "Gereed"})
    with app.app_context():
        assert not db.session.get(NistActie, aid).te_laat


def test_momentopname_en_export(app, admin):
    with open("voorbeelden/nist_beoordeling.csv", "rb") as f:
        admin.post("/nist/importeren", data={"bestand": (f, "b.csv")}, content_type="multipart/form-data")
    admin.post("/nist/meting", data={"label": "2026 Q4"})
    with app.app_context():
        m = NistMeting.query.one()
        assert m.label == "2026 Q4" and set(m.data["functies"]) == {"GV", "ID", "PR", "DE", "RS", "RC"}
    r = admin.get("/nist/export.xlsx")
    assert r.status_code == 200
    import pandas as pd
    bladen = pd.read_excel(io.BytesIO(r.data), sheet_name=None)
    # beheerders krijgen ook het tabblad met bewijsstukken
    assert set(bladen) == {"Samenvatting", "Categorieën", "Subcategorieën", "Acties", "Bewijsstukken"}
    assert len(bladen["Subcategorieën"]) == 106


def test_zichtbaarheid_voor_bezoekers(app, admin):
    admin.post("/logout")
    assert admin.get("/nist/").status_code == 302
    assert "NIST CSF" not in admin.get("/").get_data(as_text=True)
    with app.app_context():
        Instelling.set("nist_publiek", "1")
        db.session.commit()
    assert admin.get("/nist/").status_code == 200
    assert admin.get("/nist/categorie/GV.OC").status_code == 200
    # bezoekers kunnen niets wijzigen
    assert admin.post("/nist/categorie/GV.OC/toelichting", data={"toelichting": "x"}).status_code == 302
    with app.app_context():
        assert NistCategorie.query.filter_by(code="GV.OC").one().toelichting == ""


def test_open_redirect_geblokkeerd(admin):
    r = admin.post("/nist/acties/nieuw?terug=//evil.example", data={"koppeling": "GV.OC", "titel": "x"})
    assert "evil" not in r.headers["Location"]


def test_officiele_volgorde(app):
    with app.app_context():
        gv = NistFunctie.query.filter_by(code="GV").one()
        assert [c.code for c in gv.categorieen] == ["GV.OC", "GV.RM", "GV.RR", "GV.PO", "GV.OV", "GV.SC"]
