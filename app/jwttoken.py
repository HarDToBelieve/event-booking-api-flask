import jwt

from config import Config


def encode(user_id):
    token = jwt.encode({'id': user_id}, Config.JWT_SECRET)
    return str(token, 'utf-8')


def decode(token):
    try:
        payload = jwt.decode(token, Config.JWT_SECRET)
        return payload
    except:
        return None
