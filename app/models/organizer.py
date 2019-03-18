from app import db, max_len
import hashlib
import uuid
from app.models.timestamp import TimestampMixin


class Organizer(db.Model, TimestampMixin):
    __tablename__ = 'organizers'
    id = db.Column(db.Integer, primary_key=True)
    firstname = db.Column(db.String(max_len))
    lastname = db.Column(db.String(max_len))
    email = db.Column(db.String(max_len), index=True, unique=True)
    phone = db.Column(db.String(max_len))
    password_hash = db.Column(db.String(max_len))
    password_salt = db.Column(db.String(max_len))

    def set_password(self, password):
        salt = uuid.uuid4().hex
        hashed_password = hashlib.sha512((password + salt).encode('utf-8')).hexdigest()
        self.password_salt = salt
        self.password_hash = hashed_password

    def check_password(self, password):
        hashed_password = hashlib.sha512((password + self.password_salt).encode('utf-8')).hexdigest()
        return self.password_hash == hashed_password

    def serialize(self):
        return {
            'id': self.id,
            'firstname': self.firstname,
            'lastname': self.lastname,
            'email': self.email,
            'phone': self.phone
        }
