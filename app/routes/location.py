import datetime

from flask import jsonify, request
from marshmallow import Schema, fields, validate

from app import app, db, jwttoken, max_len
from app.common import parse_args_with_schema, token_auth_required
from app.errors import Error, StatusCode
from app.models.location import Location
from app.models.organizer import Organizer


class LocationCreateSchema(Schema):
    name_location = fields.String(validate=validate.Length(max=max_len), required=True)
    address = fields.String(validate=validate.Length(max=max_len), required=True)


class LocationUpdateSchema(Schema):
    name_location = fields.String(validate=validate.Length(max=max_len))
    address = fields.String(validate=validate.Length(max=max_len))


@app.route(app.config['PREFIX'] + '/locations/', methods=['POST'])
@parse_args_with_schema(LocationCreateSchema)
@token_auth_required
def location_create(user, user_type, args):
    if user_type != 'Organizer':
        raise Error(status_code=StatusCode.UNAUTHORIZED, error_message='Invalid token')
    location = Location.query.filter_by(address=args['address']).first()
    if location is not None:
        raise Error(status_code=StatusCode.BAD_REQUEST, error_message='Duplicated location')
    location = Location(
        name_location=args['name_location'],
        address=args['address'],
        owner_id=user.id
    )
    db.session.add(location)
    db.session.commit()
    return jsonify({
        'message': 'Location created successfully',
        'data': location.serialize()
    }), 201


@app.route(app.config['PREFIX'] + '/locations/<int:location_id>/', methods=['PUT'])
@parse_args_with_schema(LocationUpdateSchema)
@token_auth_required
def location_update(user, user_type, location_id, args):
    if user_type != 'Organizer':
        raise Error(status_code=StatusCode.UNAUTHORIZED, error_message='Invalid token')
    location = Location.query.filter_by(id=location_id, owner_id=user.id).first()
    if location is None:
        raise Error(status_code=StatusCode.BAD_REQUEST, error_message='Location not found')
    location.update(**args)
    db.session.commit()
    return jsonify({
        'message': 'Location updated successfully',
        'data': location.serialize()
    }), 201


@app.route(app.config['PREFIX'] + '/locations/<int:location_id>/', methods=['DELETE'])
@token_auth_required
def location_delete(user, user_type, location_id):
    if user_type != 'Organizer':
        raise Error(status_code=StatusCode.UNAUTHORIZED, error_message='Invalid token')
    location = Location.query.filter_by(id=location_id, owner_id=user.id).first()
    if location is None:
        raise Error(status_code=StatusCode.BAD_REQUEST, error_message='Location not found')
    
    events = location.events
    for e in events:
        db.session.delete(e)
    
    db.session.delete(location)
    db.session.commit()
    return jsonify({
        'message': 'Location deleted successfully'
    }), 201


@app.route(app.config['PREFIX'] + '/locations/', methods=['GET'])
def location_list_all():
    page = None if request.args.get('page') is None else int(request.args.get('page'))
    result = Location.query.paginate(page=page, per_page=15)
    has_next = 'YES'
    if page is not None and page == (result.total // 15) + 1:
        has_next = None
    elif page is None:
        has_next = None

    return jsonify({
        'current_page': page,
        'next_page_url': has_next,
        'locations': [x.serialize() for x in result.items]
    }), 200


@app.route(app.config['PREFIX'] + '/locations/<int:location_id>/', methods=['GET'])
def location_get_specific_info(location_id):
    location = Location.query.filter_by(id=location_id).first()
    if location is None:
        raise Error(status_code=StatusCode.BAD_REQUEST, error_message='Location not found')
    return jsonify({'result': location.serialize()}), 200
