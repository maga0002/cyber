import re

from flask import (Blueprint, abort, current_app, flash, redirect, render_template,
                   request, url_for)
from flask_login import current_user, login_required, login_user, logout_user

from .database import db
from .importer import ImportFout, analyseer, kies_standaard_groepkolom, lees_bestand
from .models import Dataset, DatasetRow, NewsPost, User
from .nist_routes import nist_publiek

bp = Blueprint("main", __name__)


# ---------------------------------------------------------------- algemeen

@bp.app_context_processor
def globale_context():
    return {
        "app_naam": current_app.config["APP_NAAM"],
        "db_type": current_app.config["DB_TYPE"],
    }


@bp.before_app_request
def eerste_installatie():
    """Zolang er geen beheerder is, alles doorsturen naar de setup-pagina."""
    if request.endpoint in ("main.setup", "static"):
        return
    if User.query.count() == 0:
        return redirect(url_for("main.setup"))


@bp.route("/setup", methods=["GET", "POST"])
def setup():
    if User.query.count() > 0:
        return redirect(url_for("main.index"))
    if request.method == "POST":
        naam = request.form.get("username", "").strip()
        ww = request.form.get("password", "")
        if not naam or len(ww) < 8:
            flash("Vul een gebruikersnaam in en een wachtwoord van minimaal 8 tekens.", "fout")
        elif ww != request.form.get("password2"):
            flash("De wachtwoorden komen niet overeen.", "fout")
        else:
            user = User(username=naam)
            user.set_password(ww)
            db.session.add(user)
            db.session.commit()
            login_user(user)
            flash("Beheerder aangemaakt. Welkom!", "ok")
            return redirect(url_for("main.index"))
    return render_template("setup.html")


@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = User.query.filter_by(username=request.form.get("username", "").strip()).first()
        if user and user.check_password(request.form.get("password", "")):
            login_user(user, remember=bool(request.form.get("remember")))
            volgende = request.args.get("next", "")
            if not volgende.startswith("/") or volgende.startswith("//"):
                volgende = url_for("main.index")
            return redirect(volgende)
        flash("Onjuiste gebruikersnaam of wachtwoord.", "fout")
    return render_template("login.html")


@bp.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    return redirect(url_for("main.index"))


# ---------------------------------------------------------------- nieuws

@bp.route("/")
def index():
    q = NewsPost.query
    if not current_user.is_authenticated:
        q = q.filter_by(published=True)
    categorie = request.args.get("categorie")
    if categorie:
        q = q.filter_by(category=categorie)
    berichten = q.order_by(NewsPost.pinned.desc(), NewsPost.created_at.desc()).all()
    datasets = Dataset.query.order_by(Dataset.updated_at.desc()).limit(6).all()
    nist_ov = None
    if current_user.is_authenticated or nist_publiek():
        from . import nist
        nist_ov = nist.overzicht()
    return render_template("index.html", berichten=berichten, datasets=datasets, nist_ov=nist_ov,
                           categorieen=NewsPost.CATEGORIEEN, actieve_categorie=categorie)


@bp.route("/nieuws/<int:post_id>")
def nieuws_detail(post_id):
    post = db.get_or_404(NewsPost, post_id)
    if not post.published and not current_user.is_authenticated:
        abort(404)
    return render_template("nieuws_detail.html", post=post)


@bp.route("/nieuws/nieuw", methods=["GET", "POST"])
@login_required
def nieuws_nieuw():
    post = NewsPost(category="Algemeen", published=True)
    if request.method == "POST" and _vul_post(post):
        post.author = current_user
        db.session.add(post)
        db.session.commit()
        flash("Bericht geplaatst.", "ok")
        return redirect(url_for("main.index"))
    return render_template("nieuws_form.html", post=post, categorieen=NewsPost.CATEGORIEEN)


@bp.route("/nieuws/<int:post_id>/bewerken", methods=["GET", "POST"])
@login_required
def nieuws_bewerken(post_id):
    post = db.get_or_404(NewsPost, post_id)
    if request.method == "POST" and _vul_post(post):
        db.session.commit()
        flash("Bericht bijgewerkt.", "ok")
        return redirect(url_for("main.nieuws_detail", post_id=post.id))
    return render_template("nieuws_form.html", post=post, categorieen=NewsPost.CATEGORIEEN)


@bp.route("/nieuws/<int:post_id>/verwijderen", methods=["POST"])
@login_required
def nieuws_verwijderen(post_id):
    post = db.get_or_404(NewsPost, post_id)
    db.session.delete(post)
    db.session.commit()
    flash("Bericht verwijderd.", "ok")
    return redirect(url_for("main.index"))


def _vul_post(post: NewsPost) -> bool:
    post.title = request.form.get("title", "").strip()
    post.body = request.form.get("body", "").strip()
    cat = request.form.get("category", "Algemeen")
    post.category = cat if cat in NewsPost.CATEGORIEEN else "Algemeen"
    post.pinned = bool(request.form.get("pinned"))
    post.published = bool(request.form.get("published"))
    if not post.title or not post.body:
        flash("Titel en tekst zijn verplicht.", "fout")
        return False
    return True


# ---------------------------------------------------------------- dashboards

@bp.route("/dashboards")
def dashboards():
    datasets = Dataset.query.order_by(Dataset.updated_at.desc()).all()
    overzicht = []
    for ds in datasets:
        rijen = [r.data for r in ds.rows]
        analyse = analyseer(ds.columns, rijen)
        hoofd = next((c for c in analyse["categorisch"] if c["kolom"] == ds.group_column), None)
        overzicht.append({"ds": ds, "analyse": analyse, "hoofd": hoofd})
    return render_template("dashboards.html", overzicht=overzicht)


@bp.route("/dashboards/importeren", methods=["GET", "POST"])
@login_required
def dashboard_importeren():
    if request.method == "POST":
        bestand = request.files.get("bestand")
        naam = request.form.get("name", "").strip()
        if not bestand or not bestand.filename:
            flash("Kies een bestand om te importeren.", "fout")
            return render_template("dashboard_import.html")
        try:
            kolommen, rijen = lees_bestand(bestand.filename, bestand.read())
        except ImportFout as exc:
            flash(str(exc), "fout")
            return render_template("dashboard_import.html")

        ds = Dataset(
            name=naam or bestand.filename.rsplit(".", 1)[0],
            description=request.form.get("description", "").strip(),
            source_filename=bestand.filename,
        )
        _zet_rijen(ds, kolommen, rijen)
        db.session.add(ds)
        db.session.commit()
        flash(f"{len(rijen)} regels geïmporteerd.", "ok")
        return redirect(url_for("main.dashboard_detail", ds_id=ds.id))
    return render_template("dashboard_import.html")


@bp.route("/dashboards/<int:ds_id>")
def dashboard_detail(ds_id):
    ds = db.get_or_404(Dataset, ds_id)
    alle_rijen = [r.data for r in ds.rows]

    # optioneel filter: ?f_kolom=Status&f_waarde=Open
    f_kolom = request.args.get("f_kolom")
    f_waarde = request.args.get("f_waarde")
    rijen = alle_rijen
    if f_kolom in ds.columns and f_waarde is not None:
        if re.fullmatch(r"\d{4}-\d{2}", f_waarde):  # maand uit een datumkolom
            rijen = [r for r in alle_rijen if str(r.get(f_kolom) or "").startswith(f_waarde)]
        else:
            rijen = [r for r in alle_rijen if str(r.get(f_kolom)) == f_waarde]

    analyse = analyseer(ds.columns, rijen)
    groep = request.args.get("groep") or ds.group_column
    hoofd = next((c for c in analyse["categorisch"] if c["kolom"] == groep), None)
    return render_template("dashboard_detail.html", ds=ds, rijen=rijen, analyse=analyse,
                           hoofd=hoofd, groep=groep, f_kolom=f_kolom, f_waarde=f_waarde,
                           totaal=len(alle_rijen))


@bp.route("/dashboards/<int:ds_id>/bewerken", methods=["GET", "POST"])
@login_required
def dashboard_bewerken(ds_id):
    ds = db.get_or_404(Dataset, ds_id)
    analyse = analyseer(ds.columns, [r.data for r in ds.rows])
    if request.method == "POST":
        ds.name = request.form.get("name", "").strip() or ds.name
        ds.description = request.form.get("description", "").strip()
        groep = request.form.get("group_column")
        ds.group_column = groep if groep in ds.columns else None

        bestand = request.files.get("bestand")
        if bestand and bestand.filename:
            try:
                kolommen, rijen = lees_bestand(bestand.filename, bestand.read())
            except ImportFout as exc:
                flash(str(exc), "fout")
                return render_template("dashboard_bewerken.html", ds=ds, analyse=analyse)
            ds.rows.clear()
            db.session.flush()
            ds.source_filename = bestand.filename
            behoud_groep = ds.group_column if ds.group_column in kolommen else None
            _zet_rijen(ds, kolommen, rijen)
            if behoud_groep:
                ds.group_column = behoud_groep
            flash(f"Gegevens vervangen door {len(rijen)} nieuwe regels.", "ok")
        db.session.commit()
        flash("Dashboard opgeslagen.", "ok")
        return redirect(url_for("main.dashboard_detail", ds_id=ds.id))
    return render_template("dashboard_bewerken.html", ds=ds, analyse=analyse)


@bp.route("/dashboards/<int:ds_id>/verwijderen", methods=["POST"])
@login_required
def dashboard_verwijderen(ds_id):
    ds = db.get_or_404(Dataset, ds_id)
    db.session.delete(ds)
    db.session.commit()
    flash("Dashboard verwijderd.", "ok")
    return redirect(url_for("main.dashboards"))


def _zet_rijen(ds: Dataset, kolommen: list[str], rijen: list[dict]):
    ds.columns = kolommen
    ds.rows = [DatasetRow(position=i, data=r) for i, r in enumerate(rijen)]
    ds.group_column = kies_standaard_groepkolom(analyseer(kolommen, rijen))


# ---------------------------------------------------------------- beheer

@bp.route("/beheer")
@login_required
def beheer():
    from . import demo
    return render_template("beheer.html", leeg=demo.is_leeg())


@bp.route("/beheer/voorbeelddata", methods=["POST"])
@login_required
def voorbeelddata():
    from . import demo
    if not demo.is_leeg():
        flash("Voorbeelddata kan alleen in een lege omgeving worden geladen. Wis eerst de inhoud.", "fout")
        return redirect(url_for("main.beheer"))
    r = demo.laad_voorbeelddata(current_user)
    flash(f"Voorbeelddata geladen: {r['nieuws']} nieuwsberichten, {r['dashboards']} dashboards, "
          f"een volledige NIST-beoordeling met acties, {r['bewijs']} bewijsstukken en een trend.", "ok")
    return redirect(url_for("main.index"))


@bp.route("/beheer/wissen", methods=["POST"])
@login_required
def inhoud_wissen():
    from . import demo
    if request.form.get("bevestiging", "").strip().upper() != "WISSEN":
        flash("Typ WISSEN om te bevestigen.", "fout")
        return redirect(url_for("main.beheer"))
    demo.wis_inhoud()
    flash("Alle inhoud is gewist. Gebruikersaccounts zijn behouden.", "ok")
    return redirect(url_for("main.beheer"))
