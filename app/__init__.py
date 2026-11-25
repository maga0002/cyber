import os
import secrets

import click
from flask import Flask, abort, request, session
from flask_login import LoginManager
from markupsafe import Markup, escape

from .database import db, kies_database_uri
from .models import User

login_manager = LoginManager()
login_manager.login_view = "main.login"
login_manager.login_message = "Log in om deze pagina te bekijken."


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


def _secret_key(instance_path: str) -> str:
    if os.environ.get("SECRET_KEY"):
        return os.environ["SECRET_KEY"]
    # Bewaar een gegenereerde sleutel zodat sessies een herstart overleven.
    pad = os.path.join(instance_path, "secret_key")
    if os.path.exists(pad):
        with open(pad) as f:
            return f.read().strip()
    sleutel = secrets.token_hex(32)
    with open(pad, "w") as f:
        f.write(sleutel)
    os.chmod(pad, 0o600)
    return sleutel


def create_app(test_config: dict | None = None) -> Flask:
    app = Flask(__name__, instance_relative_config=True)
    os.makedirs(app.instance_path, exist_ok=True)

    if test_config and "SQLALCHEMY_DATABASE_URI" in test_config:
        uri, db_type = test_config["SQLALCHEMY_DATABASE_URI"], "sqlite"
    else:
        uri, db_type = kies_database_uri(app.instance_path)

    app.config.update(
        SECRET_KEY=_secret_key(app.instance_path),
        SQLALCHEMY_DATABASE_URI=uri,
        SQLALCHEMY_ENGINE_OPTIONS={"pool_pre_ping": True},
        DB_TYPE=db_type,
        MAX_CONTENT_LENGTH=16 * 1024 * 1024,  # max 16 MB per upload
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        APP_NAAM=os.environ.get("APP_NAAM", "Cyberweerbaarheid Monitor"),
    )
    if test_config:
        app.config.update(test_config)

    db.init_app(app)
    login_manager.init_app(app)

    from .nist_routes import bp as nist_bp
    from .routes import bp
    app.register_blueprint(bp)
    app.register_blueprint(nist_bp)

    _registreer_csrf(app)
    _registreer_filters(app)
    _registreer_cli(app)

    with app.app_context():
        db.create_all()
        from .nist import vul_framework
        vul_framework()

    app.logger.info("Database in gebruik: %s", db_type)
    return app


def _registreer_csrf(app: Flask):
    def csrf_token():
        if "_csrf" not in session:
            session["_csrf"] = secrets.token_urlsafe(32)
        return session["_csrf"]

    app.jinja_env.globals["csrf_token"] = csrf_token

    @app.before_request
    def check_csrf():
        if app.config.get("TESTING_SKIP_CSRF"):
            return
        if request.method == "POST":
            token = request.form.get("_csrf")
            if not token or token != session.get("_csrf"):
                abort(400, "Ongeldig of verlopen formulier. Probeer het opnieuw.")


def _registreer_filters(app: Flask):
    @app.template_filter("alinea")
    def alinea(tekst: str):
        """Zet platte tekst om naar alinea's, veilig ge-escaped."""
        blokken = [b.strip() for b in (tekst or "").replace("\r\n", "\n").split("\n\n") if b.strip()]
        html = "".join(f"<p>{escape(b).replace(chr(10), Markup('<br>'))}</p>" for b in blokken)
        return Markup(html)

    @app.template_filter("datum")
    def datum(dt):
        if not dt:
            return ""
        maanden = ["jan", "feb", "mrt", "apr", "mei", "jun", "jul", "aug", "sep", "okt", "nov", "dec"]
        return f"{dt.day} {maanden[dt.month - 1]} {dt.year}"


def _registreer_cli(app: Flask):
    @app.cli.command("voorbeelddata")
    def voorbeelddata():
        """Vul een lege omgeving met fictieve voorbeelddata."""
        from . import demo
        if not demo.is_leeg():
            raise click.ClickException("Er staat al inhoud in de database; voorbeelddata wordt niet geladen.")
        r = demo.laad_voorbeelddata(User.query.first())
        click.echo(f"Voorbeelddata geladen ({r['nieuws']} berichten, {r['dashboards']} dashboards, NIST-beoordeling).")

    @app.cli.command("create-admin")
    @click.argument("username")
    @click.password_option()
    def create_admin(username, password):
        """Maak een beheerder aan (of wijzig het wachtwoord)."""
        user = User.query.filter_by(username=username).first() or User(username=username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        click.echo(f"Beheerder '{username}' opgeslagen.")
