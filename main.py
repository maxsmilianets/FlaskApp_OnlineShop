from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "maksym"  # zmień później na losowe

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///shop.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)


# --- MODELE ---

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(80), nullable=False)
    last_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(200), unique=True, nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(300), nullable=False)


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(160), nullable=False)
    price_grosze = db.Column(db.Integer, nullable=False)
    image_url = db.Column(db.String(400), nullable=True)
    is_active = db.Column(db.Boolean, default=True)

    def price_pln(self) -> str:
        return f"{self.price_grosze / 100:.2f}"


# --- INIT DB + SEED ---

def seed_hats():
    hats = [
        ("Czapka Classic 1", 6999, "hat_1.png"),
        ("Czapka Classic 2", 7499, "hat_2.png"),
        ("Czapka Street 3", 5999, "hat_3.png"),
        ("Czapka Winter 4", 8999, "hat_4.png"),
        ("Czapka Snapback 5", 7999, "hat_5.png"),
        ("Czapka Sport 6", 6499, "hat_6.png"),
    ]

    names = [n for (n, _, _) in hats]
    existing = {p.name for p in Product.query.filter(Product.name.in_(names)).all()}

    added = 0
    for name, price_grosze, image_url in hats:
        if name in existing:
            continue
        db.session.add(Product(
            name=name,
            price_grosze=price_grosze,
            image_url=image_url,  # trzymamy tylko nazwę pliku
            is_active=True
        ))
        added += 1

    if added:
        db.session.commit()

def seed_sneakers():
    sneakers = [
        ("Sneakersy Urban 1", 19999, "sneakersy_1.png"),
        ("Sneakersy Urban 2", 21999, "sneakersy_2.png"),
        ("Sneakersy Runner 3", 24999, "sneakersy_3.png"),
        ("Sneakersy Classic 4", 17999, "sneakersy_4.png"),
        ("Sneakersy Street 5", 28999, "sneakersy_5.png"),
        ("Sneakersy Sport 6", 15999, "sneakersy_6.png"),
    ]

    names = [n for (n, _, _) in sneakers]
    existing = {p.name for p in Product.query.filter(Product.name.in_(names)).all()}

    added = 0
    for name, price_grosze, image_url in sneakers:
        if name in existing:
            continue
        db.session.add(Product(
            name=name,
            price_grosze=price_grosze,
            image_url=image_url,
            is_active=True
        ))
        added += 1

    if added:
        db.session.commit()


def ensure_db():
    with app.app_context():
        db.create_all()
        seed_sneakers()
        seed_hats()

ensure_db()


# --- POMOCNICZE ---

def current_user():
    uid = session.get("user_id")
    if not uid:
        return None
    return User.query.get(uid)


def login_required():
    if not session.get("user_id"):
        flash("Zaloguj się, aby wejść do katalogu.", "warning")
        return redirect(url_for("home"))
    return None


# --- ROUTES ---

@app.route("/", methods=["GET", "POST"])
def home():
    # Logowanie
    if request.method == "POST":
        login_or_email = request.form.get("login_or_email", "").strip()
        password = request.form.get("password", "")

        if not login_or_email or not password:
            flash("Podaj login/e-mail i hasło.", "danger")
            return redirect(url_for("home"))

        user = User.query.filter(
            (User.username == login_or_email) | (User.email == login_or_email)
        ).first()

        if not user or not check_password_hash(user.password_hash, password):
            flash("Niepoprawny login/e-mail lub hasło.", "danger")
            return redirect(url_for("home"))

        session["user_id"] = user.id
        flash(f"Witaj, {user.first_name} 👋", "success")
        return redirect(url_for("catalog"))

    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    # Rejestracja
    if request.method == "POST":
        first_name = request.form.get("first_name", "").strip()
        last_name = request.form.get("last_name", "").strip()
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        if not all([first_name, last_name, username, email, password]):
            flash("Uzupełnij wszystkie pola.", "danger")
            return redirect(url_for("register"))

        if len(password) < 8:
            flash("Hasło musi mieć min. 8 znaków.", "danger")
            return redirect(url_for("register"))

        if User.query.filter_by(username=username).first():
            flash("Taki login już istnieje.", "danger")
            return redirect(url_for("register"))

        if User.query.filter_by(email=email).first():
            flash("Taki e-mail już istnieje.", "danger")
            return redirect(url_for("register"))

        user = User(
            first_name=first_name,
            last_name=last_name,
            username=username,
            email=email,
            password_hash=generate_password_hash(password)
        )
        db.session.add(user)
        db.session.commit()

        flash("Konto utworzone. Możesz się zalogować.", "success")
        return redirect(url_for("home"))

    return render_template("register.html")

@app.route("/news")
def news():
    # publiczne — dostępne bez logowania (żeby przycisk na ekranie logowania działał)
    products = (
        Product.query
        .filter_by(is_active=True)
        .order_by(Product.id.desc())
        .limit(12)
        .all()
    )
    return render_template("news.html", products=products, user=current_user())


@app.route("/catalog")
def catalog():
    gate = login_required()
    if gate:
        return gate

    q = request.args.get("q", "").strip()
    query = Product.query.filter_by(is_active=True)
    if q:
        query = query.filter(Product.name.ilike(f"%{q}%"))

    products = query.order_by(Product.id.desc()).all()
    return render_template("catalog.html", products=products, user=current_user(), q=q)

@app.route("/profile", methods=["GET", "POST"])
def profile():
    gate = login_required()
    if gate:
        return gate

    user = current_user()

    if request.method == "POST":
        first_name = request.form.get("first_name", "").strip()
        last_name = request.form.get("last_name", "").strip()
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()

        new_password = request.form.get("new_password", "")
        new_password2 = request.form.get("new_password2", "")

        if not all([first_name, last_name, username, email]):
            flash("Uzupełnij wszystkie pola (oprócz hasła).", "danger")
            return redirect(url_for("profile"))

        # sprawdź unikalność loginu/email (pomijając aktualnego usera)
        if User.query.filter(User.username == username, User.id != user.id).first():
            flash("Taki login już istnieje.", "danger")
            return redirect(url_for("profile"))

        if User.query.filter(User.email == email, User.id != user.id).first():
            flash("Taki e-mail już istnieje.", "danger")
            return redirect(url_for("profile"))

        # aktualizacja danych
        user.first_name = first_name
        user.last_name = last_name
        user.username = username
        user.email = email

        # zmiana hasła (opcjonalna)
        if new_password or new_password2:
            if new_password != new_password2:
                flash("Hasła nie są takie same.", "danger")
                return redirect(url_for("profile"))
            if len(new_password) < 8:
                flash("Hasło musi mieć min. 8 znaków.", "danger")
                return redirect(url_for("profile"))

            user.password_hash = generate_password_hash(new_password)

        db.session.commit()
        flash("Zapisano zmiany.", "success")
        return redirect(url_for("profile"))

    return render_template("profile.html", user=user)

def get_cart() -> dict:
    """
    Zwraca koszyk z sesji jako dict: {product_id(str): qty(int)}
    """
    cart = session.get("cart")
    if not isinstance(cart, dict):
        cart = {}
        session["cart"] = cart
    return cart


def format_pln(grosze: int) -> str:
    return f"{grosze / 100:.2f}"

@app.post("/cart/add/<int:product_id>")
def cart_add(product_id: int):
    gate = login_required()
    if gate:
        return gate

    p = Product.query.get_or_404(product_id)
    if not p.is_active:
        flash("Produkt jest niedostępny.", "warning")
        return redirect(url_for("catalog"))

    cart = get_cart()
    key = str(product_id)
    cart[key] = int(cart.get(key, 0)) + 1
    session["cart"] = cart
    session.modified = True

    flash(f"Dodano do koszyka: {p.name}", "success")
    # wróć tam, gdzie był użytkownik
    return redirect(request.referrer or url_for("catalog"))


@app.route("/cart")
def cart():
    gate = login_required()
    if gate:
        return gate

    user = current_user()
    cart = get_cart()

    ids = [int(pid) for pid in cart.keys()]
    products = Product.query.filter(Product.id.in_(ids), Product.is_active == True).all() if ids else []

    # map id -> Product
    by_id = {p.id: p for p in products}

    items = []
    total_grosze = 0

    for pid_str, qty in cart.items():
        pid = int(pid_str)
        p = by_id.get(pid)
        if not p:
            continue
        qty = int(qty)
        subtotal = p.price_grosze * qty
        total_grosze += subtotal
        items.append({
            "id": p.id,
            "name": p.name,
            "image_url": p.image_url,
            "price_grosze": p.price_grosze,
            "price_pln": p.price_pln(),
            "qty": qty,
            "subtotal_pln": format_pln(subtotal),
        })

    # sort: najnowsze na górze
    items.sort(key=lambda x: x["id"], reverse=True)

    return render_template(
        "cart.html",
        user=user,
        items=items,
        total_pln=format_pln(total_grosze),
    )


@app.post("/cart/remove/<int:product_id>")
def cart_remove(product_id: int):
    gate = login_required()
    if gate:
        return gate

    cart = get_cart()
    key = str(product_id)

    if key in cart:
        cart[key] = int(cart[key]) - 1
        if cart[key] <= 0:
            del cart[key]

    session["cart"] = cart
    session.modified = True
    return redirect(url_for("cart"))


@app.post("/cart/remove_all/<int:product_id>")
def cart_remove_all(product_id: int):
    gate = login_required()
    if gate:
        return gate

    cart = get_cart()
    key = str(product_id)
    if key in cart:
        del cart[key]

    session["cart"] = cart
    session.modified = True
    return redirect(url_for("cart"))


@app.post("/cart/clear")
def cart_clear():
    gate = login_required()
    if gate:
        return gate

    session["cart"] = {}
    session.modified = True
    return redirect(url_for("cart"))


@app.post("/cart/checkout")
def cart_checkout():
    gate = login_required()
    if gate:
        return gate

    cart = get_cart()
    if not cart:
        flash("Koszyk jest pusty.", "warning")
        return redirect(url_for("cart"))

    # tutaj później podepniemy płatności / zamówienia
    session["cart"] = {}
    session.modified = True
    flash("Płatność zakończona. Dziękujemy! ", "success")
    return redirect(url_for("catalog"))
    

@app.route("/logout")
def logout():
    session.clear()
    flash("Wylogowano.", "info")
    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(debug=True)

