from functools import wraps

from flask import request

from app.errors import Error, StatusCode, UnauthorizedError
from app.models.users import User
from app import jwttoken, task_queue


def parse_args_with_schema(schema):
    def parse_args_with_decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if request.method == 'GET':
                requested_args = request.args.to_dict()
            else:
                requested_args = request.json or {}
            parsed_args, errors = schema().load(requested_args)
            if errors:
                raise Error(status_code=StatusCode.BAD_REQUEST, error_data=errors)
            kwargs['args'] = parsed_args
            return f(*args, **kwargs)
        return decorated_function
    return parse_args_with_decorator


def token_auth_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        authorization_header = request.headers.get('Authorization')
        if not authorization_header:
            raise UnauthorizedError()
        if 'Bearer' not in authorization_header:
            raise UnauthorizedError()
        access_token = request.headers['Authorization'][len('Bearer '):]
        payload = jwttoken.decode(access_token)

        if payload is None:
            raise UnauthorizedError
        user_id = payload['id']
		if payload['user_type'] == 'Organizer':
			user = Organizer.query.filter_by(id=user_id).first()
		else:
        	user = Attendee.query.filter_by(id=user_id).first()
        if user is None:
            raise UnauthorizedError()
        kwargs['user'] = user
		kwargs['user_type'] = payload['user_type']
        return f(*args, **kwargs)
    return decorated_function


def queue_deferred(task, *args, **kwargs):
    task_queue.enqueue(task, *args, **kwargs)
