from flask import Flask
from flask.ext.mongoengine import MongoEngine
from os import environ as env

app = Flask(__name__, static_folder='static', static_url_path='')

# Load config.
if not env.get('HEROKU'):
    app.config.from_object('config')
else:
    app.config.from_object('config_heroku')

# Setup the database.
db = MongoEngine(app)

from app import routes