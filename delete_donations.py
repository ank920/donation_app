from app import create_app, db
from app.models.donation import Donation

app = create_app()

with app.app_context():
    # Delete all donations
    num_deleted = Donation.query.delete()
    db.session.commit()
    print(f"Successfully deleted {num_deleted} donations from the database.") 