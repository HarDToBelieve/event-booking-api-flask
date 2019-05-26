from app import db, max_len
from app.models.timestamp import TimestampMixin


class Location(db.Model, TimestampMixin):
    __tablename__ = 'locations'
    id = db.Column(db.Integer, primary_key=True)
    name_location = db.Column(db.String(max_len))
    address = db.Column(db.String(max_len), index=True, unique=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('organizers.id'))
    
    events = db.relationship('Event')
    
    def __init__(self, *args, **kwargs):
        super(Location, self).__init__(*args, **kwargs)

    def serialize(self):
        return {
            'id': self.id,
            'name_location': self.name_location,
            'address': self.address,
            'owner_id': self.owner_id
        }

    def update(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
