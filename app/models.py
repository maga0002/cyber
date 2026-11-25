from datetime import datetime, timezone

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from .database import db


def nu():
    return datetime.now(timezone.utc)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=nu)

    def set_password(self, wachtwoord: str):
        self.password_hash = generate_password_hash(wachtwoord)

    def check_password(self, wachtwoord: str) -> bool:
        return check_password_hash(self.password_hash, wachtwoord)


class NewsPost(db.Model):
    CATEGORIEEN = ["Algemeen", "Waarschuwing", "Incident", "Tip", "Update"]

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    body = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(40), default="Algemeen", nullable=False)
    pinned = db.Column(db.Boolean, default=False, nullable=False)
    published = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=nu)
    updated_at = db.Column(db.DateTime(timezone=True), default=nu, onupdate=nu)
    author_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    author = db.relationship("User")


class Dataset(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, default="")
    source_filename = db.Column(db.String(255))
    columns = db.Column(db.JSON, nullable=False, default=list)
    group_column = db.Column(db.String(200))  # kolom voor de hoofdgrafiek
    created_at = db.Column(db.DateTime(timezone=True), default=nu)
    updated_at = db.Column(db.DateTime(timezone=True), default=nu, onupdate=nu)
    rows = db.relationship(
        "DatasetRow", backref="dataset", cascade="all, delete-orphan",
        order_by="DatasetRow.position",
    )


class DatasetRow(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    dataset_id = db.Column(db.Integer, db.ForeignKey("dataset.id"), nullable=False, index=True)
    position = db.Column(db.Integer, nullable=False, default=0)
    data = db.Column(db.JSON, nullable=False)


# ---------------------------------------------------------------- NIST CSF

class Instelling(db.Model):
    sleutel = db.Column(db.String(80), primary_key=True)
    waarde = db.Column(db.Text, default="")

    @staticmethod
    def get(sleutel: str, standaard: str = "") -> str:
        rij = db.session.get(Instelling, sleutel)
        return rij.waarde if rij else standaard

    @staticmethod
    def set(sleutel: str, waarde: str):
        rij = db.session.get(Instelling, sleutel) or Instelling(sleutel=sleutel)
        rij.waarde = waarde
        db.session.add(rij)


class NistFunctie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(4), unique=True, nullable=False)
    naam_en = db.Column(db.String(80), nullable=False)
    naam = db.Column(db.String(80), nullable=False)
    omschrijving = db.Column(db.Text, default="")
    toelichting = db.Column(db.Text, default="")  # eigen informatie van de organisatie
    volgorde = db.Column(db.Integer, default=0)
    categorieen = db.relationship("NistCategorie", backref="functie", order_by="NistCategorie.volgorde")


class NistCategorie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(8), unique=True, nullable=False)
    functie_id = db.Column(db.Integer, db.ForeignKey("nist_functie.id"), nullable=False)
    naam_en = db.Column(db.String(120), nullable=False)
    naam = db.Column(db.String(120), nullable=False)
    omschrijving = db.Column(db.Text, default="")
    toelichting = db.Column(db.Text, default="")
    volgorde = db.Column(db.Integer, default=0)
    subcategorieen = db.relationship("NistSubcategorie", backref="categorie", order_by="NistSubcategorie.code")
    acties = db.relationship("NistActie", backref="categorie", order_by="NistActie.deadline")


class NistSubcategorie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(12), unique=True, nullable=False)
    categorie_id = db.Column(db.Integer, db.ForeignKey("nist_categorie.id"), nullable=False)
    omschrijving = db.Column(db.Text, default="")
    # beoordeling
    huidig = db.Column(db.Integer)          # 0-5, None = nog niet beoordeeld
    doel = db.Column(db.Integer, default=3)  # 0-5
    nvt = db.Column(db.Boolean, default=False, nullable=False)
    toelichting = db.Column(db.Text, default="")  # onderbouwing / bewijs
    eigenaar = db.Column(db.String(120), default="")
    beoordeeld_op = db.Column(db.DateTime(timezone=True))
    acties = db.relationship("NistActie", backref="subcategorie")
    bewijzen = db.relationship("NistBewijs", backref="subcategorie", cascade="all, delete-orphan",
                               order_by="NistBewijs.created_at.desc()")


class NistActie(db.Model):
    STATUSSEN = ["Open", "In uitvoering", "Gereed", "Geannuleerd"]
    PRIORITEITEN = ["Hoog", "Middel", "Laag"]

    id = db.Column(db.Integer, primary_key=True)
    categorie_id = db.Column(db.Integer, db.ForeignKey("nist_categorie.id"), nullable=False, index=True)
    subcategorie_id = db.Column(db.Integer, db.ForeignKey("nist_subcategorie.id"), index=True)
    titel = db.Column(db.String(200), nullable=False)
    omschrijving = db.Column(db.Text, default="")
    eigenaar = db.Column(db.String(120), default="")
    status = db.Column(db.String(20), default="Open", nullable=False)
    prioriteit = db.Column(db.String(10), default="Middel", nullable=False)
    deadline = db.Column(db.Date)
    created_at = db.Column(db.DateTime(timezone=True), default=nu)
    updated_at = db.Column(db.DateTime(timezone=True), default=nu, onupdate=nu)

    @property
    def afgerond(self) -> bool:
        return self.status in ("Gereed", "Geannuleerd")

    @property
    def te_laat(self) -> bool:
        return bool(self.deadline and not self.afgerond and self.deadline < nu().date())


class NistMeting(db.Model):
    """Momentopname van de scores, voor trendrapportage."""
    id = db.Column(db.Integer, primary_key=True)
    label = db.Column(db.String(120), nullable=False)
    datum = db.Column(db.DateTime(timezone=True), default=nu)
    totaal = db.Column(db.Float)
    data = db.Column(db.JSON, nullable=False)  # {"functies": {"GV": 2.4, ...}, "categorieen": {...}}


class NistBewijs(db.Model):
    """Bewijsstuk bij een subcategorie: een geüpload bestand of een link."""
    id = db.Column(db.Integer, primary_key=True)
    subcategorie_id = db.Column(db.Integer, db.ForeignKey("nist_subcategorie.id"), nullable=False, index=True)
    titel = db.Column(db.String(200), nullable=False)
    omschrijving = db.Column(db.Text, default="")
    url = db.Column(db.String(1000))              # bij een link
    bestandsnaam = db.Column(db.String(255))      # originele naam bij een upload
    mimetype = db.Column(db.String(120))
    grootte = db.Column(db.Integer)
    inhoud = db.deferred(db.Column(db.LargeBinary))  # alleen laden bij downloaden
    geldig_tot = db.Column(db.Date)               # datum voor herbeoordeling
    toegevoegd_door = db.Column(db.String(80))
    created_at = db.Column(db.DateTime(timezone=True), default=nu)

    @property
    def is_bestand(self) -> bool:
        return self.bestandsnaam is not None

    @property
    def verlopen(self) -> bool:
        return bool(self.geldig_tot and self.geldig_tot < nu().date())

    @property
    def grootte_tekst(self) -> str:
        n = self.grootte or 0
        if n < 1024:
            return f"{n} B"
        if n < 1024 * 1024:
            return f"{n / 1024:.0f} KB"
        return f"{n / 1024 / 1024:.1f} MB"
