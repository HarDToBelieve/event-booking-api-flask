import datetime
import os
import random

from flask import jsonify, request
from marshmallow import Schema, fields, validate

from app import app, db, jwttoken, max_len
from app.common import parse_args_with_schema, token_auth_required
from app.errors import Error, StatusCode
from app.helper import allowed_image
from app.models.event import Event
from app.models.location import Location
from app.models.organizer import Organizer


class EventCreateSchema(Schema):
    title = fields.String(validate=validate.Length(max=max_len), required=True)
    description = fields.String(validate=validate.Length(max=max_len))
    category = fields.String(validate=validate.Length(max=max_len))
    start_date = fields.Date()
    end_date = fields.Date()
    location_id = fields.Integer(required=True)
    type = fields.String(validate=validate.Length(max=max_len))
    capacity = fields.Integer()
    

class EventUpdateSchema(Schema):
    title = fields.String(validate=validate.Length(max=max_len))
    description = fields.String(validate=validate.Length(max=max_len))
    category = fields.String(validate=validate.Length(max=max_len))
    start_date = fields.Date()
    end_date = fields.Date()
    type = fields.String(validate=validate.Length(max=max_len))
    location_id = fields.Integer()
    capacity = fields.Integer()


@app.route(app.config['PREFIX'] + '/events', methods=['POST'])
@parse_args_with_schema(EventCreateSchema)
@token_auth_required
def event_create(user, user_type, args):
    if user_type != 'Organizer':
        raise Error(status_code=StatusCode.UNAUTHORIZED, error_message='Invalid token')

    event = Event.query.filter_by(title=args['title']).first()
    if event is not None:
        raise Error(status_code=StatusCode.BAD_REQUEST, error_message='Duplicated event')

    location = Location.query.filter_by(id=args['location_id'], owner_id=user.id).first()
    if location is None:
        raise Error(status_code=StatusCode.BAD_REQUEST, error_message='Location not belongs to owner')
    
    if args['type'] != 'public' and args['type'] != 'private':
        raise Error(status_code=StatusCode.BAD_REQUEST, error_message='Invalid type of event')
    
    event = Event(
        title=args['title'],
        description=args['description'],
        category=args['category'],
        # start_date=datetime.datetime.strptime(args['start_date'], '%d-%m-%Y %H:%M'),
        # end_date=datetime.datetime.strptime(args['end_Date'], '%d-%m-%Y %H:%M'),
        start_date=args['start_date'],
        end_date=args['end_date'],
        location_id=location.id,
        owner_id=user.id,
        type=args['type'],
        capacity=args['capacity']
    )
    
    db.session.add(event)
    db.session.commit()

    return jsonify({
        'message': 'Event created successfully',
        'data': event.serialize()
    }), 201


@app.route(app.config['PREFIX'] + '/events/<int:event_id>', methods=['PUT'])
@parse_args_with_schema(EventUpdateSchema)
@token_auth_required
def event_update(user, user_type, event_id, args):
    if user_type != 'Organizer':
        raise Error(status_code=StatusCode.UNAUTHORIZED, error_message='Invalid token')
    event = Event.query.filter_by(id=event_id, owner_id=user.id).first()
    if event is None:
        raise Error(status_code=StatusCode.BAD_REQUEST, error_message='Event not found')
    event.update(**args)
    db.session.commit()
    return jsonify({
        'message': 'Location updated successfully',
        'data': event.serialize()
    }), 201


@app.route(app.config['PREFIX'] + '/events/<int:event_id>', methods=['DELETE'])
@token_auth_required
def event_delete(user, user_type, event_id):
    if user_type != 'Organizer':
        raise Error(status_code=StatusCode.UNAUTHORIZED, error_message='Invalid token')
    event = Event.query.filter_by(id=event_id, owner_id=user.id).first()
    if event is None:
        raise Error(status_code=StatusCode.BAD_REQUEST, error_message='Location not found')
    db.session.delete(event)
    db.session.commit()
    return jsonify({
        'message': 'Event deleted successfully'
    }), 201


@app.route(app.config['PREFIX'] + '/events', methods=['GET'])
def event_list_all():
    page = None if request.args.get('page') is None else int(request.args.get('page'))
    result = Event.query.filter_by(type='public').paginate(page=page, per_page=15)
    has_next = 'YES'
    if page is not None and page == -(-result.total // 15):
        has_next = None
    elif page is None:
        has_next = None

    return jsonify({
        'current_page': page,
        'next_page_url': has_next,
        'data': [{
            'detail': x.serialize(),
            'nummber_of_attendees': len(x.reservations),
            'contact': x.owner.email,
            'location_name': x.location.name_location,
            'location_address': x.location.address
        } for x in result.items]
    }), 200


@app.route(app.config['PREFIX'] + '/events/<int:event_id>', methods=['GET'])
@token_auth_required
def event_get_info(user, user_type, event_id):
    if user_type != 'Attendee':
        raise Error(status_code=StatusCode.UNAUTHORIZED, error_message='Invalid token')
    event = Event.query.filter_by(id=event_id).first()
    
    if event is None:
        raise Error(status_code=StatusCode.BAD_REQUEST, error_message='Event not found')
    
    # owner = Organizer.query.filter_by(id=event.owner_id).first()
    # location = Location.query.filter_by(id=event.location_id).first()
    
    if event.type == 'private':
        for tmp in event.attendees:
            if tmp.id == user.id:
                return jsonify({
                    'detail': event.serialize(),
                    'nummber_of_attendees': len(event.reservations),
                    'contact': event.owner.email,
                    'location_name': event.location.name_location,
                    'location_address': event.location.address
                }), 200
        raise Error(status_code=StatusCode.FORBIDDEN, error_message='Permission denied')
    else:
        return jsonify({
            'detail': event.serialize(),
            'nummber_of_attendees': len(event.reservations),
            'contact': event.owner.email,
            'location_name': event.location.name_location,
            'location_address': event.location.address
        }), 200


@app.route(app.config['PREFIX'] + '/events/<int:event_id>/upload', methods=['POST'])
@token_auth_required
def event_upload_image(user, user_type, event_id):
    if user_type != 'Organizer':
        raise Error(status_code=StatusCode.UNAUTHORIZED, error_message='Invalid token')
    event = Event.query.filter_by(id=event_id, owner_id=user.id).first()
    if event is None:
        raise Error(status_code=StatusCode.BAD_REQUEST, error_message='Event not found')
    if 'image' not in request.files:
        raise Error(status_code=StatusCode.BAD_REQUEST, error_message='Need image part')
    img = request.files['image']
    if img.filename == '':
        raise Error(status_code=StatusCode.BAD_REQUEST, error_message='Not selected image')
    if img and allowed_image(img.filename):
        new_file_name = str(datetime.datetime.now()) + '_' + str(random.randint(0, 9999999)) \
                        + '.' + img.filename.rsplit('.', 1)[1].lower()
        img.save(os.path.join('uploads', new_file_name))
        return jsonify({'message': 'Image uploaded'}), 201
    else:
        return jsonify({'message': 'Extension not allowed'})


@app.route(app.config['PREFIX'] + '/events/organizer_events', methods=['GET'])
@token_auth_required
def event_get_by_organizer(user, user_type):
    if user_type != 'Organizer':
        raise Error(status_code=StatusCode.UNAUTHORIZED, error_message='Invalid token')
    
    return jsonify([x.serialize() for x in user.events]), 200


@app.route(app.config['PREFIX'] + '/events/<int:event_id>/reservations', methods=['GET'])
@token_auth_required
def attendee_get_by_event(user, user_type, event_id):
    event = Event.query.filter_by(id=event_id, owner_id=user.id).first()
    if event is None:
        raise Error(status_code=StatusCode.BAD_REQUEST, error_message='Event not found')

    if user_type == 'Attendee' and event.type == 'private':
        found = False
        for re in event.reservations:
            if re.attendee_id == user.id:
                found = True
        if found is False:
            raise Error(status_code=StatusCode.BAD_REQUEST, error_message='Permission denied')
        
    result = []
    for re in event.reservations:
        tmp = {}
        at = re.attendees
        tmp['user'] = at.serialize()
        tmp['status'] = re.status
        tmp['user_id'] = at.id
        result.append(tmp)
    
    return jsonify(result), 200
