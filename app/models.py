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
