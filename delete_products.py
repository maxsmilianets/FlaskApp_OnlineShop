from main import app, db, Product

TO_DELETE = [
    "Koszulka Flask",
    "Kubek SQLite",
    "Naklejki Python",
    "Plecak dev",
    "Notes A5",
]

with app.app_context():
    deleted = (
        Product.query
        .filter(Product.name.in_(TO_DELETE))
        .delete(synchronize_session=False)
    )
    db.session.commit()
    print(f"Usunięto: {deleted} produktów.")
