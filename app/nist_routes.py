from datetime import date
from functools import wraps

from flask import (Blueprint, Response, abort, flash, redirect, render_template, request,
                   url_for)
from flask_login import current_user, login_required

from . import nist
from .database import db
from .importer import ImportFout
from .models import (Instelling, NistActie, NistCategorie, NistFunctie, NistMeting,
                     NistSubcategorie, nu)
from .nist_data import VOLWASSENHEID

bp = Blueprint("nist", __name__, url_prefix="/nist")


def nist_publiek() -> bool:
    return Instelling.get("nist_publiek", "0") == "1"


@bp.app_context_processor
def nist_context():
    return {"nist_zichtbaar": current_user.is_authenticated or nist_publiek(),
            "niveaus": VOLWASSENHEID}


def lezen(view):
    """Toegang voor beheerders; bezoekers alleen als de NIST-pagina's openbaar zijn."""
    @wraps(view)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated and not nist_publiek():
            return redirect(url_for("main.login", next=request.full_path))
        return view(*args, **kwargs)
    return wrapper


def _functie(code: str) -> NistFunctie:
    f = NistFunctie.query.filter_by(code=code.upper()).first()
    return f or abort(404)


def _categorie(code: str) -> NistCategorie:
    c = NistCategorie.query.filter_by(code=code.upper()).first()
    return c or abort(404)


# ---------------------------------------------------------------- overzicht

@bp.route("/")
@lezen
def overzicht():
    ov = nist.overzicht()
    metingen = NistMeting.query.order_by(NistMeting.datum).all()
    return render_template("nist/overzicht.html", ov=ov, metingen=metingen, publiek=nist_publiek(),
                           radar=nist.radar_grafiek(ov), trend=nist.trend_grafiek(ov, metingen))


@bp.route("/functie/<code>")
@lezen
def functie(code):
    f = _functie(code)
    ov = nist.overzicht()
    acties = (NistActie.query.join(NistCategorie).filter(NistCategorie.functie_id == f.id)
              .order_by(NistActie.deadline).all())
    return render_template("nist/functie.html", f=f, ov=ov, acties=acties,
                           grafiek=nist.categorie_grafiek(f, ov))


@bp.route("/functie/<code>/toelichting", methods=["POST"])
@login_required
def functie_toelichting(code):
    f = _functie(code)
    f.toelichting = request.form.get("toelichting", "").strip()
    db.session.commit()
    flash("Toelichting opgeslagen.", "ok")
    return redirect(url_for("nist.functie", code=f.code))


@bp.route("/categorie/<code>")
@lezen
def categorie(code):
    c = _categorie(code)
    return render_template("nist/categorie.html", c=c, score=nist.bereken(c.subcategorieen),
                           statussen=NistActie.STATUSSEN)


@bp.route("/categorie/<code>/toelichting", methods=["POST"])
@login_required
def categorie_toelichting(code):
    c = _categorie(code)
    c.toelichting = request.form.get("toelichting", "").strip()
    db.session.commit()
    flash("Toelichting opgeslagen.", "ok")
    return redirect(url_for("nist.categorie", code=c.code))


@bp.route("/categorie/<code>/beoordeling", methods=["POST"])
@login_required
def beoordeling(code):
    c = _categorie(code)
    gewijzigd = 0
    for s in c.subcategorieen:
        oud = (s.huidig, s.doel, s.nvt, s.toelichting, s.eigenaar)
        s.huidig = _int_of_none(request.form.get(f"huidig_{s.id}"))
        s.doel = _int_of_none(request.form.get(f"doel_{s.id}"))
        s.nvt = bool(request.form.get(f"nvt_{s.id}"))
        s.toelichting = request.form.get(f"toelichting_{s.id}", "").strip()
        s.eigenaar = request.form.get(f"eigenaar_{s.id}", "").strip()
        if (s.huidig, s.doel, s.nvt, s.toelichting, s.eigenaar) != oud:
            s.beoordeeld_op = nu()
            gewijzigd += 1
    db.session.commit()
    flash(f"Beoordeling opgeslagen ({gewijzigd} gewijzigd).", "ok")
    return redirect(url_for("nist.categorie", code=c.code))


def _int_of_none(waarde):
    try:
        return max(0, min(5, int(waarde)))
    except (TypeError, ValueError):
        return None


# ---------------------------------------------------------------- acties

@bp.route("/acties")
@lezen
def acties():
    q = NistActie.query.join(NistCategorie)
    f_status = request.args.get("status", "actief")
    f_functie = request.args.get("functie", "")
    f_eigenaar = request.args.get("eigenaar", "")
    if f_status == "actief":
        q = q.filter(NistActie.status.in_(["Open", "In uitvoering"]))
    elif f_status in NistActie.STATUSSEN:
        q = q.filter(NistActie.status == f_status)
    if f_functie:
        q = q.filter(NistCategorie.code.like(f"{f_functie}.%"))
    if f_eigenaar:
        q = q.filter(NistActie.eigenaar == f_eigenaar)
    lijst = q.all()
    lijst.sort(key=lambda a: (not a.te_laat, a.deadline or date.max, NistActie.PRIORITEITEN.index(a.prioriteit)))
    eigenaren = sorted({e for (e,) in db.session.query(NistActie.eigenaar).distinct() if e})
    return render_template("nist/acties.html", acties=lijst, statussen=NistActie.STATUSSEN,
                           functies=NistFunctie.query.order_by(NistFunctie.volgorde).all(),
                           eigenaren=eigenaren, f_status=f_status, f_functie=f_functie, f_eigenaar=f_eigenaar)


@bp.route("/acties/nieuw", methods=["GET", "POST"])
@login_required
def actie_nieuw():
    actie = NistActie(status="Open", prioriteit="Middel")
    koppeling = request.args.get("sub") or request.args.get("categorie") or ""
    if request.method == "POST" and _vul_actie(actie):
        db.session.add(actie)
        db.session.commit()
        flash("Actie toegevoegd.", "ok")
        terug = request.args.get("terug", "")
        if not terug.startswith("/") or terug.startswith("//"):
            terug = url_for("nist.categorie", code=actie.categorie.code)
        return redirect(terug)
    return _actie_formulier(actie, request.form.get("koppeling", koppeling))


@bp.route("/acties/<int:actie_id>/bewerken", methods=["GET", "POST"])
@login_required
def actie_bewerken(actie_id):
    actie = db.get_or_404(NistActie, actie_id)
    if request.method == "POST" and _vul_actie(actie):
        db.session.commit()
        flash("Actie bijgewerkt.", "ok")
        return redirect(url_for("nist.categorie", code=actie.categorie.code))
    huidig = actie.subcategorie.code if actie.subcategorie else actie.categorie.code
    return _actie_formulier(actie, request.form.get("koppeling", huidig))


@bp.route("/acties/<int:actie_id>/status", methods=["POST"])
@login_required
def actie_status(actie_id):
    actie = db.get_or_404(NistActie, actie_id)
    status = request.form.get("status")
    if status in NistActie.STATUSSEN:
        actie.status = status
        db.session.commit()
    return redirect(request.referrer or url_for("nist.acties"))


@bp.route("/acties/<int:actie_id>/verwijderen", methods=["POST"])
@login_required
def actie_verwijderen(actie_id):
    actie = db.get_or_404(NistActie, actie_id)
    code = actie.categorie.code
    db.session.delete(actie)
    db.session.commit()
    flash("Actie verwijderd.", "ok")
    return redirect(url_for("nist.categorie", code=code))


def _actie_formulier(actie, koppeling: str):
    categorieen = NistCategorie.query.order_by(NistCategorie.volgorde).all()
    return render_template("nist/actie_form.html", actie=actie, categorieen=categorieen, koppeling=koppeling,
                           statussen=NistActie.STATUSSEN, prioriteiten=NistActie.PRIORITEITEN)


def _vul_actie(actie: NistActie) -> bool:
    actie.titel = request.form.get("titel", "").strip()
    actie.omschrijving = request.form.get("omschrijving", "").strip()
    actie.eigenaar = request.form.get("eigenaar", "").strip()
    status, prio = request.form.get("status"), request.form.get("prioriteit")
    actie.status = status if status in NistActie.STATUSSEN else "Open"
    actie.prioriteit = prio if prio in NistActie.PRIORITEITEN else "Middel"
    actie.deadline = nist.parse_datum(request.form.get("deadline"))
    koppeling = request.form.get("koppeling", "")
    sub = NistSubcategorie.query.filter_by(code=koppeling).first()
    cat = sub.categorie if sub else NistCategorie.query.filter_by(code=koppeling).first()
    if not actie.titel or not cat:
        flash("Titel en koppeling aan een NIST-categorie of -subcategorie zijn verplicht.", "fout")
        return False
    actie.categorie_id, actie.subcategorie_id = cat.id, (sub.id if sub else None)
    return True


# ---------------------------------------------------------------- rapportage

@bp.route("/rapport")
@lezen
def rapport():
    ov = nist.overzicht()
    open_acties = [a for a in NistActie.query.order_by(NistActie.deadline).all() if not a.afgerond]
    open_acties.sort(key=lambda a: (not a.te_laat, NistActie.PRIORITEITEN.index(a.prioriteit),
                                    a.deadline or date.max))
    metingen = NistMeting.query.order_by(NistMeting.datum).all()
    return render_template("nist/rapport.html", ov=ov, open_acties=open_acties, metingen=metingen,
                           vandaag=date.today(), radar=nist.radar_grafiek(ov),
                           trend=nist.trend_grafiek(ov, metingen))


@bp.route("/export.xlsx")
@lezen
def export():
    data = nist.exporteer_excel()
    naam = f"nist-csf-rapportage-{date.today().isoformat()}.xlsx"
    return Response(data, mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    headers={"Content-Disposition": f'attachment; filename="{naam}"'})


@bp.route("/sjabloon.csv")
@login_required
def sjabloon():
    return Response("﻿" + nist.sjabloon_csv(), mimetype="text/csv; charset=utf-8",
                    headers={"Content-Disposition": 'attachment; filename="nist-csf-sjabloon.csv"'})


@bp.route("/importeren", methods=["GET", "POST"])
@login_required
def importeren():
    if request.method == "POST":
        bestand = request.files.get("bestand")
        if not bestand or not bestand.filename:
            flash("Kies een bestand.", "fout")
        else:
            try:
                r = nist.importeer(bestand.filename, bestand.read())
            except ImportFout as exc:
                flash(str(exc), "fout")
            else:
                flash(f"{r['beoordelingen']} beoordelingen en {r['acties']} acties geïmporteerd.", "ok")
                if r["onbekend"]:
                    flash("Onbekende codes overgeslagen: " + ", ".join(sorted(set(r["onbekend"]))[:20]), "fout")
                return redirect(url_for("nist.overzicht"))
    return render_template("nist/importeren.html")


@bp.route("/meting", methods=["POST"])
@login_required
def meting():
    ov = nist.overzicht()
    if ov["totaal"]["huidig"] is None:
        flash("Er zijn nog geen scores om vast te leggen.", "fout")
        return redirect(url_for("nist.overzicht"))
    label = request.form.get("label", "").strip() or nu().strftime("%Y-%m-%d")
    db.session.add(NistMeting(label=label, totaal=ov["totaal"]["huidig"], data=nist.momentopname_data(ov)))
    db.session.commit()
    flash(f"Momentopname '{label}' vastgelegd.", "ok")
    return redirect(url_for("nist.overzicht"))


@bp.route("/meting/<int:meting_id>/verwijderen", methods=["POST"])
@login_required
def meting_verwijderen(meting_id):
    db.session.delete(db.get_or_404(NistMeting, meting_id))
    db.session.commit()
    flash("Momentopname verwijderd.", "ok")
    return redirect(url_for("nist.overzicht"))


@bp.route("/zichtbaarheid", methods=["POST"])
@login_required
def zichtbaarheid():
    Instelling.set("nist_publiek", "1" if request.form.get("publiek") else "0")
    db.session.commit()
    flash("Zichtbaarheid van de NIST-pagina's aangepast.", "ok")
    return redirect(url_for("nist.overzicht"))
