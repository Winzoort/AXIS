
import os
import json
import hmac
import hashlib
import secrets
import threading

from pathlib import Path
from flask import (
    Flask, render_template, request, redirect,
    url_for, session, flash, abort
)
from flask_wtf.csrf import CSRFProtect


app = Flask(__name__)

# ==============================
# CONFIGURACIÓN Y SEGURIDAD
# ==============================

app.secret_key = os.environ.get("AXIS_SECRET_KEY")

if not app.secret_key:
    raise RuntimeError("Falta configurar AXIS_SECRET_KEY")

app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=bool(os.environ.get("RENDER")),
)

csrf = CSRFProtect(app)

ADMIN_USER = os.environ.get("AXIS_ADMIN_USER")
ADMIN_PASSWORD = os.environ.get("AXIS_ADMIN_PASSWORD")

if not ADMIN_USER or not ADMIN_PASSWORD:
    raise RuntimeError("Faltan las credenciales del administrador")


# ==============================
# ALMACENAMIENTO JSON
# ==============================

DATA_DIR = Path(
    os.environ.get("AXIS_DATA_DIR", "instance")
)

DATA_DIR.mkdir(parents=True, exist_ok=True)

DATA_FILE = DATA_DIR / "axis_data.json"

data_lock = threading.Lock()


def default_data():
    return {
        "invitations": {},
        "reviews": [],
        "christmas_mode": False
    }


def load_data():
    with data_lock:
        if not DATA_FILE.exists():
            return default_data()

        try:
            with open(DATA_FILE, "r", encoding="utf-8") as file:
                return json.load(file)
        except (json.JSONDecodeError, OSError):
            app.logger.exception("No se pudo leer axis_data.json")
            raise RuntimeError("No se pudo leer el almacenamiento de AXIS")


def save_data(data):
    with data_lock:
        temporary_file = DATA_FILE.with_suffix(".tmp")

        with open(temporary_file, "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=4)

        os.replace(temporary_file, DATA_FILE)


# Crear archivo inicial si no existe
if not DATA_FILE.exists():
    save_data(default_data())


# ==============================
# FUNCIONES AUXILIARES
# ==============================

def is_admin():
    return session.get("admin") is True


def admin_required():
    if not is_admin():
        abort(403)


def hash_token(token):
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


# ==============================
# PÁGINA PRINCIPAL
# ==============================

@app.route("/")
def inicio():
    data = load_data()

    approved_reviews = [
        review for review in data["reviews"]
        if review["status"] == "approved"
    ]

    return render_template(
        "index.html",
        christmas_mode=data["christmas_mode"],
        reviews=approved_reviews
    )


# ==============================
# INICIO DE SESIÓN ADMINISTRADOR
# ==============================

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():

    if is_admin():
        return redirect(url_for("admin_panel"))

    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")

        valid_user = hmac.compare_digest(username, ADMIN_USER)
        valid_password = hmac.compare_digest(password, ADMIN_PASSWORD)

        if valid_user and valid_password:
            session.clear()
            session["admin"] = True
            return redirect(url_for("admin_panel"))

        flash("Usuario o contraseña incorrectos.")

    return render_template("admin_login.html")


@app.route("/admin/logout", methods=["POST"])
def admin_logout():
    session.clear()
    return redirect(url_for("inicio"))


# ==============================
# PANEL ADMINISTRATIVO
# ==============================

@app.route("/admin")
def admin_panel():
    admin_required()

    data = load_data()

    return render_template(
        "admin.html",
        invitations=data["invitations"],
        reviews=data["reviews"],
        christmas_mode=data["christmas_mode"]
    )


# ==============================
# CREAR INVITACIONES
# ==============================

@app.route("/admin/invitations/create", methods=["POST"])
def create_invitation():
    admin_required()

    data = load_data()

    token = secrets.token_urlsafe(32)
    token_hash = hash_token(token)

    data["invitations"][token_hash] = {
        "used": False
    }

    save_data(data)

    invitation_url = url_for(
        "submit_review",
        token=token,
        _external=True
    )

    flash("Invitación creada correctamente.")

    return render_template(
        "admin.html",
        invitations=data["invitations"],
        reviews=data["reviews"],
        christmas_mode=data["christmas_mode"],
        invitation_url=invitation_url
    )


# ==============================
# ENVIAR RESEÑA CON INVITACIÓN
# ==============================

@app.route("/review/<token>", methods=["GET", "POST"])
def submit_review(token):

    token_hash = hash_token(token)
    data = load_data()

    invitation = data["invitations"].get(token_hash)

    if not invitation or invitation["used"]:
        return render_template("invitation_invalid.html"), 403

    if request.method == "POST":

        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        comment = request.form.get("comment", "").strip()
        rating = request.form.get("rating", "")

        if (
            not username or len(username) > 60
            or not email or len(email) > 254
            or not comment or len(comment) > 1000
            or rating not in ["1", "2", "3", "4", "5"]
            or "@" not in email
        ):
            flash("Revisa los datos e inténtalo nuevamente.")
            return render_template("review_form.html", token=token)

        # Volver a leer antes de consumir la invitación
        data = load_data()
        invitation = data["invitations"].get(token_hash)

        if not invitation or invitation["used"]:
            return render_template("invitation_invalid.html"), 403

        data["reviews"].append({
            "id": secrets.token_hex(8),
            "username": username,
            "email": email,
            "comment": comment,
            "rating": int(rating),
            "status": "pending"
        })

        invitation["used"] = True
        save_data(data)

        return render_template("review_success.html")

    return render_template("review_form.html", token=token)


# ==============================
# ADMINISTRAR RESEÑAS
# ==============================

@app.route("/admin/review/<review_id>/<action>", methods=["POST"])
def manage_review(review_id, action):
    admin_required()

    if action not in ["approve", "reject", "delete"]:
        abort(400)

    data = load_data()

    if action == "delete":
        data["reviews"] = [
            review for review in data["reviews"]
            if review["id"] != review_id
        ]
    else:
        for review in data["reviews"]:
            if review["id"] == review_id:
                review["status"] = (
                    "approved" if action == "approve" else "rejected"
                )
                break

    save_data(data)

    return redirect(url_for("admin_panel"))


# ==============================
# MODO NAVIDEÑO GLOBAL
# ==============================

@app.route("/admin/christmas", methods=["POST"])
def toggle_christmas():
    admin_required()

    data = load_data()

    data["christmas_mode"] = not data["christmas_mode"]

    save_data(data)

    return redirect(url_for("admin_panel"))


# ==============================
# EJECUCIÓN LOCAL
# ==============================

if __name__ == "__main__":
    app.run(debug=True, port=5000)
