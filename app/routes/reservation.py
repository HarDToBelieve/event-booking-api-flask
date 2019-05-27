from io import StringIO
import datetime
import random
import string

from flask import jsonify, request
from marshmallow import Schema, fields, validate

from app import app, db, jwttoken, max_len
from app.common import parse_args_with_schema, token_auth_required
from app.email import send_email
from app.errors import Error, StatusCode
from app.helper import allowed_image, allowed_csv
from app.models.attendee import Attendee
from app.models.event import Event
from app.models.location import Location
from app.models.reservation import Reservation
import csv


@app.route(app.config['PREFIX'] + '/reservations/confirm/<int:event_id>', methods=['POST'])
@token_auth_required
def event_confirm(user, user_type, event_id):
    if user_type != 'Attendee':
        raise Error(status_code=StatusCode.UNAUTHORIZED, error_message='Invalid token')
    event = Event.query.filter_by(id=event_id).first()
    if event is None:
        raise Error(status_code=StatusCode.BAD_REQUEST, error_message='Event not found')
    if datetime.datetime.now().date() > event.end_date:
        raise Error(status_code=StatusCode.BAD_REQUEST, error_message='Expired event')
    
    reservations = event.attendees
    if len(reservations) == event.capacity:
        raise Error(status_code=StatusCode.BAD_REQUEST, error_message='Out of slot')
    
    reservation = Reservation.query.filter_by(event_id=event_id, attendee_id=user.id,
                                              status='PENDING').first()
    if reservation is None:
        raise Error(status_code=StatusCode.BAD_REQUEST, error_message='Reservation not found')
    existing_slots = Reservation.query.filter_by(event_id=event_id, status='INVITED').all()
    if len(existing_slots) == event.capacity:
        raise Error(status_code=StatusCode.BAD_REQUEST, error_message='Full slots')
    reservation.status = 'INVITED'
    db.session.commit()
    return jsonify({'message': 'Confirmed'}), 201


@app.route(app.config['PREFIX'] + '/reservations', methods=['POST'])
@token_auth_required
def event_booking_handle(user, user_type):
    if 'event_id' not in request.form:
        raise Error(status_code=StatusCode.UNAUTHORIZED, error_message='Invalid parameter')
    
    if request.args.get('type') == 'public':
        if user_type != 'Attendee':
            raise Error(status_code=StatusCode.UNAUTHORIZED, error_message='Invalid token')
        event = Event.query.filter_by(id=request.form['event_id']).first()
        if event is None:
            raise Error(status_code=StatusCode.BAD_REQUEST, error_message='Event not found')
        if datetime.datetime.now().date() > event.end_date:
            raise Error(status_code=StatusCode.BAD_REQUEST, error_message='Expired event')
        
        reservation = Reservation(status='INVITED', event_id=event.id, attendee_id=user.id)
        db.session.add(reservation)
        db.session.commit()
        return jsonify({
            'result': reservation.serialize()
        }), 201
    elif request.args.get('type') == 'private':
        result = []
        if user_type != 'Organizer':
            raise Error(status_code=StatusCode.UNAUTHORIZED, error_message='Invalid token')
        event = Event.query.filter_by(id=request.form['event_id'], owner_id=user.id).first()
        if event is None:
            raise Error(status_code=StatusCode.BAD_REQUEST, error_message='Event not found')
        if 'csv_file' not in request.files:
            raise Error(status_code=StatusCode.BAD_REQUEST, error_message='Need csv_file part')
        csv_file = request.files['csv_file']
        new_file_name = 'tmp/' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=32)) + '.csv'
        csv_file.save(new_file_name)
        if csv_file.filename == '':
            raise Error(status_code=StatusCode.BAD_REQUEST, error_message='Not selected csv')
        if csv_file and allowed_csv(csv_file.filename):
            csv_reader = csv.reader(open(new_file_name))
            
            if csv_reader.line_num != event.capacity:
                raise Error(status_code=StatusCode.BAD_REQUEST, error_message='Too many invitations')
            
            for row in csv_reader:
                user_mail = row[0]
                existing_user = Attendee.query.filter_by(email=user_mail).first()
                if existing_user is not None:
                    reservation = Reservation(status='PENDING', event_id=event.id, attendee_id=user.id)
                    db.session.add(reservation)
                    db.session.commit()
                else:
                    rand_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=32))
                    new_user = Attendee(firstname='', lastname='', email=user_mail, phone='',
                                        signup_code=rand_str, password_hash='', password_salt='')
                    reservation = Reservation(status='PENDING', event_id=event.id, attendee_id=user.id)
                    db.session.add(new_user)
                    db.session.add(reservation)
                    db.session.commit()
                    
                    message = 'Here is your confirm link: {}'.format(rand_str)
                    send_email(subject='Your confirm link',
                               recipients=[user_mail], text_body=message, html_body=None)
                result.append(reservation)
        return jsonify({
            'result': [x.serialize() for x in result]
        }), 201
