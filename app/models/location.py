from app import db, max_len
import hashlib
import uuid
from app.models.timestamp import TimestampMixin


class Location(db.Model, TimestampMixin):
    __tablename__ = 'locations'
    id = db.Column(db.Integer, primary_key=True)
    name_location = db.Column(db.String(max_len))
    address = db.Column(db.String(max_len), index=True, unique=True)
    capacity = db.Column(db.Integer)
    owner_id = db.Column(db.Integer, db.ForeignKey('organizers.id'))

    def serialize(self):
        return {
            'id': self.id,
            'name_location': self.name_location,
            'address': self.address,
            'capacity': self.capacity,
            'owner_id': self.owner_id
        }
