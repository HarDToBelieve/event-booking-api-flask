from app import db, max_len
import hashlib
import uuid
from app.models.timestamp import TimestampMixin


class Event(db.Model, TimestampMixin):
    __tablename__ = 'events'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(max_len))
    description = db.Column(db.String(max_len))
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    location_id = db.Column(db.Integer, db.ForeignKey('locations.id'))
    owner_id = db.Column(db.Integer, db.ForeignKey('organizers.id'))
    category = db.Column(db.String(max_len))
    img = db.Column(db.String(max_len))
    type = db.Column(db.String(max_len))
    capacity = db.Column(db.Integer)

    reservations = db.relationship('Reservation')

    def __init__(self, *args, **kwargs):
        super(Event, self).__init__(*args, **kwargs)
        
    def serialize(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'location_id': self.location_id,
            'owner_id': self.owner_id,
            'category': self.category,
            'img': self.img,
            'type': self.type,
            'capacity': self.capacity
        }

    def update(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)