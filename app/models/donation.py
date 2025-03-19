from datetime import datetime
from app import db

class Donation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    quantity = db.Column(db.String(50), nullable=False)
    condition = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), default='available')
    contact_phone = db.Column(db.String(20), nullable=False)
    
    # Location information
    pickup_location = db.Column(db.String(200), nullable=False)
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    expiry_time = db.Column(db.DateTime, nullable=False)
    reserved_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    
    # Category-specific details stored as JSON
    details = db.Column(db.JSON, nullable=True)
    
    # Relationships
    reviews = db.relationship('Review', backref='donation', lazy=True, cascade='all, delete-orphan')
    
    # Define relationships to User model for donor and recipient
    donor = db.relationship('User', 
                          foreign_keys=[user_id],
                          backref=db.backref('donations_as_donor', lazy='dynamic'))
    recipient = db.relationship('User',
                              foreign_keys=[recipient_id],
                              backref=db.backref('donations_as_recipient', lazy='dynamic'))

    def __repr__(self):
        return f'<Donation {self.title}>'

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'recipient_id': self.recipient_id,
            'title': self.title,
            'description': self.description,
            'category': self.category,
            'quantity': self.quantity,
            'condition': self.condition,
            'status': self.status,
            'contact_phone': self.contact_phone,
            'pickup_location': self.pickup_location,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'expiry_time': self.expiry_time.isoformat() if self.expiry_time else None,
            'reserved_at': self.reserved_at.isoformat() if self.reserved_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'details': self.details,
            'donor_name': self.donor.username if self.donor else None,
            'recipient_name': self.recipient.username if self.recipient else None
        }

    def is_available(self):
        return self.status == 'available' and self.expiry_time > datetime.utcnow()

    def is_expired(self):
        return self.expiry_time <= datetime.utcnow()

    def can_be_reserved_by(self, user):
        return (user.user_type == 'recipient' and 
                self.is_available() and 
                not self.is_expired() and 
                self.user_id != user.id)

    def reserve(self, recipient):
        if not self.can_be_reserved_by(recipient):
            return False, "This donation cannot be reserved."
        
        try:
            self.status = 'reserved'
            self.recipient_id = recipient.id
            self.reserved_at = datetime.utcnow()
            return True, "Donation successfully reserved!"
        except Exception as e:
            return False, str(e)

    def complete(self, user):
        if self.status != 'reserved':
            return False, "Only reserved donations can be marked as completed."
        if self.user_id != user.id:
            return False, "Only the donor can mark a donation as completed."
        
        try:
            self.status = 'completed'
            self.completed_at = datetime.utcnow()
            return True, "Donation marked as completed!"
        except Exception as e:
            return False, str(e)

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    donation_id = db.Column(db.Integer, db.ForeignKey('donation.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Review {self.id}>'

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'donation_id': self.donation_id,
            'rating': self.rating,
            'comment': self.comment,
            'created_at': self.created_at.isoformat()
        }
