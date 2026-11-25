import io
from datetime import date, timedelta

import pandas as pd
import pytest

from app import create_app
from app.database import db
from app.models import Instelling, NistBewijs, NistSubcategorie


@pytest.fixture()
def app(tmp_path):
    return create_app({"TESTING": True, "TESTING_SKIP_CSRF": True,
                       "SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmp_path / 't.db'}"})


@pytest.fixture()
def admin(app):
    c = app.test_client()
    c.post("/setup", data={"username": "beheer", "password": "geheim123", "password2": "geheim123"})
    return c


def upload(client, sub="PR.AA-01", naam="beleid.pdf", inhoud=b"%PDF-1.4 test", **extra):
    data = {"bestand": (io.BytesIO(inhoud), naam), **extra}
    return client.post(f"/nist/bewijs/nieuw?sub={sub}", data=data, content_type="multipart/form-data")


def test_bestand_uploaden_en_downloaden(app, admin):
    r = upload(admin, titel="Toegangsbeleid", omschrijving="Vastgesteld door MT")
    assert r.status_code == 302 and "PR.AA" in r.headers["Location"]
    with app.app_context():
        b = NistBewijs.query.one()
        assert b.titel == "Toegangsbeleid" and b.grootte == 13 and b.toegevoegd_door == "beheer"
        assert b.subcategorie.code == "PR.AA-01"
        bid = b.id
    r = admin.get(f"/nist/bewijs/{bid}/bestand")
    assert r.data == b"%PDF-1.4 test" and r.mimetype == "application/pdf"
    assert r.headers["Content-Disposition"].startswith("inline")
    assert r.headers["X-Content-Type-Options"] == "nosniff"
    assert admin.get(f"/nist/bewijs/{bid}/bestand?download=1").headers["Content-Disposition"].startswith("attachment")
    assert "Toegangsbeleid" in admin.get("/nist/categorie/PR.AA").get_data(as_text=True)


def test_titel_standaard_bestandsnaam_en_office_als_download(app, admin):
    upload(admin, naam="Rapport pentest 2026.docx", inhoud=b"PK\x03\x04")
    with app.app_context():
        b = NistBewijs.query.one()
        assert b.titel == "Rapport pentest 2026"
        bid = b.id
    r = admin.get(f"/nist/bewijs/{bid}/bestand")
    assert r.headers["Content-Disposition"].startswith("attachment")
    assert "sandbox" in r.headers["Content-Security-Policy"]


def test_link_als_bewijs(app, admin):
    admin.post("/nist/bewijs/nieuw?sub=GV.PO-01", data={"url": "https://intranet.example/beleid", "titel": "Beleid"})
    with app.app_context():
        b = NistBewijs.query.one()
        assert b.url == "https://intranet.example/beleid" and not b.is_bestand


@pytest.mark.parametrize("naam", ["aanval.html", "x.svg", "script.js", "virus.exe"])
def test_gevaarlijke_bestanden_geweigerd(app, admin, naam):
    r = upload(admin, naam=naam)
    assert "niet toegestaan" in r.get_data(as_text=True)
    with app.app_context():
        assert NistBewijs.query.count() == 0


def test_ongeldige_link_geweigerd(app, admin):
    r = admin.post("/nist/bewijs/nieuw?sub=GV.PO-01", data={"url": "javascript:alert(1)", "titel": "x"})
    assert "http://" in r.get_data(as_text=True)
    with app.app_context():
        assert NistBewijs.query.count() == 0


def test_leeg_formulier_geweigerd(app, admin):
    r = admin.post("/nist/bewijs/nieuw?sub=GV.PO-01", data={"titel": "x"})
    assert "Upload een bestand of vul een link in" in r.get_data(as_text=True)


def test_verlopen_bewijs_en_overzicht(app, admin):
    gisteren = (date.today() - timedelta(days=1)).isoformat()
    upload(admin, titel="Oud rapport", geldig_tot=gisteren)
    upload(admin, sub="DE.CM-01", titel="Actueel", geldig_tot="2099-01-01")
    html = admin.get("/nist/bewijs?filter=verlopen").get_data(as_text=True)
    assert "Oud rapport" in html and "Actueel" not in html
    html = admin.get("/nist/").get_data(as_text=True)
    assert "Onderbouwd met bewijs: 2 van 106" in html and "1 verlopen" in html
    assert "Onderbouwing met bewijsstukken" in admin.get("/nist/rapport").get_data(as_text=True)


def test_bewerken_vervangen_en_verwijderen(app, admin):
    upload(admin)
    with app.app_context():
        bid = NistBewijs.query.one().id
    admin.post(f"/nist/bewijs/{bid}/bewerken", data={"titel": "Nieuwe titel"})
    with app.app_context():
        b = db.session.get(NistBewijs, bid)
        assert b.titel == "Nieuwe titel" and b.is_bestand  # bestand blijft staan
    admin.post(f"/nist/bewijs/{bid}/bewerken", data={"titel": "Nu een link", "url": "https://dms.example/1"})
    with app.app_context():
        b = db.session.get(NistBewijs, bid)
        assert not b.is_bestand and b.url == "https://dms.example/1" and b.inhoud is None
    admin.post(f"/nist/bewijs/{bid}/verwijderen")
    with app.app_context():
        assert NistBewijs.query.count() == 0


def test_bezoekers_zien_geen_bewijs(app, admin):
    upload(admin, titel="Geheim pentestrapport")
    with app.app_context():
        bid = NistBewijs.query.one().id
        Instelling.set("nist_publiek", "1")
        db.session.commit()
    admin.post("/logout")
    assert "Geheim pentestrapport" not in admin.get("/nist/categorie/PR.AA").get_data(as_text=True)
    assert "Onderbouwd met bewijs" not in admin.get("/nist/").get_data(as_text=True)
    assert admin.get(f"/nist/bewijs/{bid}/bestand").status_code == 302
    assert admin.get("/nist/bewijs").status_code == 302
    assert upload(admin).status_code == 302
    bladen = pd.read_excel(io.BytesIO(admin.get("/nist/export.xlsx").data), sheet_name=None)
    assert "Bewijsstukken" not in bladen


def test_onbekende_subcategorie(admin):
    assert admin.get("/nist/bewijs/nieuw?sub=XX.YY-99").status_code == 404
