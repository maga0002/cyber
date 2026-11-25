import pytest

from app import create_app
from app.models import Dataset, NewsPost, NistActie, NistBewijs, NistMeting, NistSubcategorie, User


@pytest.fixture()
def app(tmp_path):
    return create_app({"TESTING": True, "TESTING_SKIP_CSRF": True,
                       "SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmp_path / 't.db'}"})


@pytest.fixture()
def admin(app):
    c = app.test_client()
    c.post("/setup", data={"username": "beheer", "password": "geheim123", "password2": "geheim123"})
    return c


def test_voorbeelddata_laden_en_alle_paginas(app, admin):
    assert admin.post("/beheer/voorbeelddata").status_code == 302
    with app.app_context():
        assert NewsPost.query.count() == 5 and Dataset.query.count() == 4
        assert NistActie.query.count() == 10 and NistBewijs.query.count() == 8
        assert NistMeting.query.count() == 3
        assert NistSubcategorie.query.filter(NistSubcategorie.huidig.isnot(None)).count() == 106
        ds_ids = [d.id for d in Dataset.query.all()]
        groepen = {d.name: d.group_column for d in Dataset.query.all()}
    assert groepen["Kwetsbaarheden"] == "Status"
    assert groepen["Phishingsimulaties"] == "Resultaat"
    assert groepen["Beveiligingsincidenten 2026"] == "Type incident"
    for url in ["/", "/dashboards", "/nist/", "/nist/rapport", "/nist/bewijs", "/nist/acties", "/beheer"] + \
               [f"/dashboards/{i}" for i in ds_ids]:
        assert admin.get(url).status_code == 200, url
    # een tweede keer laden mag niet
    admin.post("/beheer/voorbeelddata")
    with app.app_context():
        assert NewsPost.query.count() == 5


def test_datumkolom_per_maand_en_filter(app, admin):
    admin.post("/beheer/voorbeelddata")
    with app.app_context():
        ds = Dataset.query.filter_by(name="Beveiligingsincidenten 2026").one()
        ds_id = ds.id
        maart = sum(1 for r in ds.rows if r.data["Datum"].startswith("2026-03"))
    html = admin.get(f"/dashboards/{ds_id}").get_data(as_text=True)
    assert "mrt 2026" in html
    html = admin.get(f"/dashboards/{ds_id}?f_kolom=Datum&f_waarde=2026-03").get_data(as_text=True)
    assert f"({maart} van 28 regels)" in html


def test_wissen_vereist_bevestiging(app, admin):
    admin.post("/beheer/voorbeelddata")
    admin.post("/beheer/wissen", data={"bevestiging": "nee"})
    with app.app_context():
        assert NewsPost.query.count() == 5
    admin.post("/beheer/wissen", data={"bevestiging": "wissen"})
    with app.app_context():
        assert NewsPost.query.count() == 0 and Dataset.query.count() == 0 and NistBewijs.query.count() == 0
        assert NistSubcategorie.query.filter(NistSubcategorie.huidig.isnot(None)).count() == 0
        assert NistSubcategorie.query.count() == 106 and User.query.count() == 1


def test_beheer_alleen_ingelogd(admin):
    admin.post("/logout")
    assert admin.post("/beheer/voorbeelddata").status_code == 302
    assert admin.get("/beheer").status_code == 302
