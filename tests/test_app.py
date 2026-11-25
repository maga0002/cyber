import io
import os

import pytest

from app import create_app
from app.database import db, kies_database_uri
from app.models import Dataset, NewsPost, User

VOORBEELD = os.path.join(os.path.dirname(__file__), "..", "voorbeelden", "maatregelen.csv")


@pytest.fixture()
def app(tmp_path):
    app = create_app({
        "TESTING": True,
        "TESTING_SKIP_CSRF": True,
        "SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmp_path / 'test.db'}",
    })
    yield app


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def admin(client):
    client.post("/setup", data={"username": "beheer", "password": "geheim123", "password2": "geheim123"})
    return client


def test_setup_verplicht_zonder_gebruikers(client):
    r = client.get("/")
    assert r.status_code == 302 and "/setup" in r.headers["Location"]


def test_setup_maakt_admin(app, admin):
    with app.app_context():
        assert User.query.count() == 1
    assert admin.get("/setup").status_code == 302


def test_nieuws_plaatsen_en_tonen(app, admin):
    admin.post("/nieuws/nieuw", data={"title": "Phishinggolf", "body": "Let op!\n\nKlik niet.",
                                      "category": "Waarschuwing", "published": "on"})
    admin.post("/nieuws/nieuw", data={"title": "Geheim concept", "body": "x", "category": "Algemeen"})
    admin.post("/logout")
    html = admin.get("/").get_data(as_text=True)
    assert "Phishinggolf" in html
    assert "Geheim concept" not in html  # concepten niet zichtbaar voor bezoekers


def test_html_wordt_ge_escaped(app, admin):
    admin.post("/nieuws/nieuw", data={"title": "x", "body": "<script>alert(1)</script>", "published": "on"})
    with app.app_context():
        pid = NewsPost.query.first().id
    assert "<script>alert(1)" not in admin.get(f"/nieuws/{pid}").get_data(as_text=True)


def test_bezoeker_kan_niet_posten(client, admin):
    admin.post("/logout")
    r = client.post("/nieuws/nieuw", data={"title": "x", "body": "y"})
    assert r.status_code == 302 and "/login" in r.headers["Location"]


def test_csv_import_en_dashboard(app, admin):
    with open(VOORBEELD, "rb") as f:
        r = admin.post("/dashboards/importeren", data={"bestand": (f, "maatregelen.csv"), "name": "BIO"},
                       content_type="multipart/form-data")
    assert r.status_code == 302
    with app.app_context():
        ds = Dataset.query.one()
        assert len(ds.rows) == 12
        assert ds.group_column == "Status"
        assert "Score" in ds.columns
        ds_id = ds.id
    html = admin.get(f"/dashboards/{ds_id}").get_data(as_text=True)
    assert "Verdeling op Status" in html and "Gem. Score" in html
    gefilterd = admin.get(f"/dashboards/{ds_id}?f_kolom=Status&f_waarde=Open").get_data(as_text=True)
    assert "3 van 12 regels" in gefilterd


def test_excel_import_en_vervangen(app, admin):
    import pandas as pd
    buf = io.BytesIO()
    pd.DataFrame({"Systeem": ["A", "B"], "Risico": ["Hoog", "Laag"]}).to_excel(buf, index=False)
    buf.seek(0)
    admin.post("/dashboards/importeren", data={"bestand": (buf, "risico.xlsx")},
               content_type="multipart/form-data")
    with app.app_context():
        ds = Dataset.query.one()
        assert ds.name == "risico" and len(ds.rows) == 2
        ds_id = ds.id
    nieuw = io.BytesIO(b"Systeem,Risico\nA,Hoog\nB,Laag\nC,Middel\n")
    admin.post(f"/dashboards/{ds_id}/bewerken", data={"name": "Risico's", "bestand": (nieuw, "r.csv")},
               content_type="multipart/form-data")
    with app.app_context():
        ds = db.session.get(Dataset, ds_id)
        assert len(ds.rows) == 3 and ds.name == "Risico's"


def test_ongeldig_bestand(admin):
    r = admin.post("/dashboards/importeren", data={"bestand": (io.BytesIO(b"x"), "virus.exe")},
                   content_type="multipart/form-data")
    assert "Alleen CSV- of Excel" in r.get_data(as_text=True)


def test_csrf_actief(tmp_path):
    app = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmp_path / 'c.db'}"})
    r = app.test_client().post("/setup", data={"username": "a", "password": "12345678", "password2": "12345678"})
    assert r.status_code == 400


def test_terugval_naar_sqlite(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://x:y@127.0.0.1:1/bestaatniet")
    uri, soort = kies_database_uri(str(tmp_path))
    assert soort == "sqlite" and uri.startswith("sqlite:///")
