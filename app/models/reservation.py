from app import db, max_len
import hashlib
import uuid
from app.models.timestamp import TimestampMixin


class Reservation(db.Model, TimestampMixin):
    __tablename__ = 'reservations'
    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.String(max_len))
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'))
    attendee_id = db.Column(db.Integer, db.ForeignKey('attendees.id'))

    events = db.relationship("Event")
    attendees = db.relationship("Attendee")

    def __init__(self, *args, **kwargs):
        super(Reservation, self).__init__(*args, **kwargs)

    def serialize(self):
        return {
            'id': self.id,
            'status': self.status,
            'event_id': self.event_id,
            'attendee_id': self.attendee_id
        }
