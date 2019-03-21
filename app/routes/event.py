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


class EventCreateSchema(Schema):
    title = fields.String(validate=validate.Length(max=max_len), required=True)
    description = fields.String(validate=validate.Length(max=max_len))
    category = fields.String(validate=validate.Length(max=max_len))
    start_date = fields.Date()
    end_date = fields.Date()
    location_id = fields.Integer()
    type = fields.String(validate=validate.Length(max=max_len))
    

class EventUpdateSchema(Schema):
    title = fields.String(validate=validate.Length(max=max_len))
    description = fields.String(validate=validate.Length(max=max_len))
    category = fields.String(validate=validate.Length(max=max_len))
    start_date = fields.Date()
    end_date = fields.Date()
    type = fields.String(validate=validate.Length(max=max_len))
    location_id = fields.Integer()


@app.route(app.config['PREFIX'] + '/events/create', methods=['POST'])
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
        raise Error(status_code=StatusCode.BAD_REQUEST, error_message='Location not found')
    
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
        type=args['type']
    )
    
    db.session.add(event)
    db.session.commit()

    return jsonify({
        'message': 'Event created successfully',
        'data': event.serialize()
    }), 201


@app.route(app.config['PREFIX'] + '/events/update/<int:event_id>', methods=['PUT'])
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


@app.route(app.config['PREFIX'] + '/events/delete/<int:event_id>', methods=['DELETE'])
@token_auth_required
def event_delete(user, user_type, event_id):
    if user_type != 'Organizer':
        raise Error(status_code=StatusCode.UNAUTHORIZED, error_message='Invalid token')
    event = Event.query.filter_by(id=event_id, owner_id=user.id).first()
    if event is None:
        raise Error(status_code=StatusCode.BAD_REQUEST, error_message='Location not found')
    event.delete()
    db.session.commit()
    return jsonify({
        'message': 'Event deleted successfully'
    }), 201


@app.route(app.config['PREFIX'] + '/events/', methods=['GET'])
def event_list_all():
    page = None if request.args.get('page') is None else int(request.args.get('page'))
    result = Event.query.paginate(page=page, per_page=15)
    has_next = 1
    if page is not None and page == -(-result.total // 10):
        has_next = 0
    elif page is None:
        has_next = 0

    return jsonify({
        'has_next': has_next,
        'events': [x.serialize() for x in result.items]
    }), 200


@app.route(app.config['PREFIX'] + '/events/<int:event_id>', methods=['GET'])
def event_get_info(event_id):
    event = Event.query.filter_by(id=event_id).first()
    if event is None:
        raise Error(status_code=StatusCode.BAD_REQUEST, error_message='Event not found')
    return jsonify({
        'result': event.serialize()
    }), 200


@app.route(app.config['PREFIX'] + '/events/upload/<int:event_id>', methods=['POST'])
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
        new_file_name = str(datetime.datetime.now()) + '_' + str(random.randint(0,9999999)) \
                        + '.' + img.filename.rsplit('.', 1)[1].lower()
        img.save(os.path.join('uploads', new_file_name))
        return jsonify({'message': 'Image uploaded'}), 201
    else:
        return jsonify({'message': 'Extension not allowed'})
