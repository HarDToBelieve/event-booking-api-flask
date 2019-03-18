import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(dotenv_path=os.path.join(basedir, '.env'))


class Config(object):
    SECRET_KEY = os.getenv('SECRET_KEY') or 'app-secret-key'
    SQLALCHEMY_DATABASE_URI = os.getenv('SQLALCHEMY_DATABASE_URI') or 'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET = os.getenv('JWT_SECRET') or 'jwt-secret-key'
    MAIL_SERVER = os.getenv('MAIL_SERVER') or 'smtp.googlemail.com'
    MAIL_PORT = os.getenv('MAIL_PORT') or 587
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS') or 1
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    EMAIL_SENDER = os.getenv('EMAIL_SENDER') or 'haha@yopmail.com'
    REDIS_URL = os.getenv('REDIS_URL') or 'redis://'
    # BRAINTREE_MERCHANT_ID = os.getenv('BRAINTREE_MERCHANT_ID')
    # BRAINTREE_PUBLIC_KEY = os.getenv('BRAINTREE_PUBLIC_KEY')
    # BRAINTREE_PRIVATE_KEY = os.getenv('BRAINTREE_PRIVATE_KEY')
