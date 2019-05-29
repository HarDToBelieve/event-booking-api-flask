from flask import Flask, jsonify, url_for, send_from_directory
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_mail import Mail
from flask_cors import CORS
from redis import Redis
import rq
import urllib.parse


app = Flask(__name__)
CORS(app)
app.config.from_object(Config)
db = SQLAlchemy(app)
mail = Mail(app)
migrate = Migrate(app, db)
max_len = 500
task_queue = rq.Queue('flask', connection=Redis.from_url(Config.REDIS_URL))


from app import routes, models
