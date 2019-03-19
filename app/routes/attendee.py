import datetime

from flask import jsonify
from marshmallow import Schema, fields, validate

from app import app, db, jwttoken, max_len
from app.common import parse_args_with_schema, token_auth_required
from app.errors import Error, StatusCode
from app.models.attendee import Attendee


class UserSignUpSchema(Schema):
    email = fields.Email(validate=validate.Length(max=max_len), required=True)
    password = fields.String(validate=validate.Length(max=max_len), required=True)
    firstname = fields.String(validate=validate.Length(max=max_len), required=True)
    lastname = fields.String(validate=validate.Length(max=max_len), required=True)
    phone = fields.String(validate=validate.Length(max=max_len), required=True)
    signup_code = fields.String(validate=validate.Length(max=max_len))


class UserLogInSchema(Schema):
    email = fields.Email(validate=validate.Length(max=max_len), required=True)
    password = fields.String(validate=validate.Length(max=max_len), required=True)


class UserUpdateSchema(Schema):
    email = fields.Email(validate=validate.Length(max=max_len))
    password = fields.String(validate=validate.Length(max=max_len))
    firstname = fields.String(validate=validate.Length(max=max_len))
    lastname = fields.String(validate=validate.Length(max=max_len))
    phone = fields.String(validate=validate.Length(max=max_len))


@app.route('attendee/register', methods=['POST'])
@parse_args_with_schema(UserSignUpSchema)
def attendee_signup(args):
    if len(args['signup_code']) > 0:
        attendee = Attendee.query.filter_by(email=args['email'], signup_code=args['signup_code']).first()
        if attendee is None:
            raise Error(status_code=StatusCode.BAD_REQUEST, error_message='Email not found')
        attendee.update(args)
        attendee.signup_code = ''
        db.session.commit()
        return jsonify({
            'message': 'Attendee created successfully',
            'data': attendee.serialize()
        }), 201
    else:
        attendee = Attendee.query.filter_by(email=args['email']).first()
        if attendee is not None:
            raise Error(status_code=StatusCode.BAD_REQUEST, error_message='Duplicated email')
        attendee = Attendee(**args)
        attendee.set_password(password = args['password'])
        db.session.add(attendee)
        db.session.commit()
        return jsonify({
            'message': 'Attendee created successfully',
            'data': attendee.serialize()
        }), 201


@app.route('attendee/login', methods=['POST'])
@parse_args_with_schema(UserLogInSchema)
def attendee_login(args):
    attendee = Attendee.query.filter_by(email=args['email']).first()
    if attendee and attendee.check_password(args['password']):
        return jsonify({
            'access_token': jwttoken.encode(attendee.id, 'Attendee')
        }), 200
    raise Error(status_code=StatusCode.UNAUTHORIZED, error_message='Invalid email or password.')


@app.route('attendee/info/update', methods=['PUT'])
@parse_args_with_schema(UserUpdateSchema)
@token_auth_required
def attendee_update_info(user, user_type, args):
    if user_type != 'Attendee':
        raise Error(status_code=StatusCode.UNAUTHORIZED, error_message='Invalid token')
    user.update(**args)
    if len(args['password']) > 0:
        user.set_password(args['password'])
    db.session.commit()
    return jsonify({
        'message': 'Attendee updated successfully',
        'data': user.serialize()
    }), 201


@app.route('attendee/info', methods=['GET'])
@token_auth_required
def attendee_get_info(user, user_type):
    if user_type != 'Attendee':
        raise Error(status_code=StatusCode.UNAUTHORIZED, error_message='Invalid token')
    return jsonify({
        'result': user.serialize()
    }), 200
