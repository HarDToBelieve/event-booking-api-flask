from flask import jsonify

from app import app


class StatusCode:
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    METHOD_NOT_ALLOWED = 405
    INTERNAL_SERVER_ERROR = 500


class Error(Exception):
    def __init__(self, status_code, error_message=None, error_data=None):
        self.error_message = error_message or ''
        self.status_code = status_code
        self.error_data = error_data or {}

    def to_response(self):
        return jsonify({
            'error_message': self.error_message,
            'error_data': self.error_data
        }), self.status_code


class TransactionError(Error):
    def __init__(self, *args, **kwargs):
        super(Error, *args, **kwargs)
        self.status_code = StatusCode.BAD_REQUEST
        self.error_message = 'We cannot process your transaction. Please try again.'
        self.error_data = {}


class UnauthorizedError(Error):
    def __init__(self, *args, **kwargs):
        super(Error, *args, **kwargs)
        self.status_code = StatusCode.UNAUTHORIZED
        self.error_message = 'Unauthorized.'
        self.error_data = {}


@app.errorhandler(Error)
def custom_error_handler(error):
    return error.to_response()
