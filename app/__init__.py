from flask import Flask
from flask.ext.mongoengine import MongoEngine
from os import environ as env

app = Flask(__name__, static_folder='static', static_url_path='')

# Load config.
if env.get('HIVE_TESTING'):
    app.config.from_object('config')
    app.config['MONGODB_SETTINGS'] = {'DB': 'hive_testing'}
elif env.get('HEROKU'):
    app.config.from_object('config_heroku')
else:
    app.config.from_object('config')

# Setup the database.
db = MongoEngine(app)

from app import routes, models