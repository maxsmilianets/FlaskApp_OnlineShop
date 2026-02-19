from main import app, db, Product

with app.app_context():
    sneakers = Product.query.filter(Product.name.ilike("%Sneakersy%")).all()
    for p in sneakers:
        last = p.name.strip().split()[-1]
        if last.isdigit():
            p.image_url = f"sneakersy_{last}.png"
    db.session.commit()
    print("OK: zaktualizowano image_url dla sneakersów.")
