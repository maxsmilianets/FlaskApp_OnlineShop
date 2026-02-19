from main import app, db, Product

with app.app_context():
    p = Product.query.filter_by(name="Sneakersy Sport 6").first()
    if not p:
        print("Nie znaleziono produktu")
        raise SystemExit

    p.price_grosze = 15999  # 159.99 zł
    db.session.commit()
    print("Zmieniono cenę.")
