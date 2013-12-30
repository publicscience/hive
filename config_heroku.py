from os import environ as env
import re

# This is a config file for deploying to Heroku.
# Set these values as environment variables in your Heroku environment with:
# $ heroku config:add SOME_VAR=some_value

CSRF_ENABLED = True
SECRET_KEY = env['SECRET_KEY']

# Using MongoHQ on Heroku.
# Ref: https://devcenter.heroku.com/articles/mongohq
# Visit your application on Heroku's dashboard and navigate
# to the MongoHQ dashboard. Under Admin > Users you can manage credentials.
# You don't have to set this env var, MongoHQ sets it for you.
MONGO_URL = env['MONGOHQ_URL']
mongo_re = re.compile('''
        mongodb://
        (?P<user>[^:]+)
        :
        (?P<password>[^@]+)
        @
        (?P<host>[^:]+)
        :
        (?P<port>[0-9]+)
        /
        (?P<db>[a-z0-9]+)
''', re.VERBOSE)
mongo = mongo_re.match(MONGO_URL)
MONGODB_SETTINGS = {
    'DB': mongo.group('db'),
    'USERNAME': mongo.group('username'),
    'PASSWORD': mongo.group('password'),
    'HOST': mongo.group('host'),
    'PORT': mongo.group('port')
}

AUTH_USER = env['AUTH_USER']
AUTH_PASS = env['AUTH_PASS']

MAIL_HOST = 'smtp.gmail.com'
MAIL_PORT = 587
MAIL_USER = env['MAIL_USER']
MAIL_PASS = env['MAIL_PASS']
MAIL_TARGETS = ['ftzeng@gmail.com']

GOOGLE_CLIENT_ID = env['GOOGLE_CLIENT_ID']
GOOGLE_CLIENT_SECRET = env['GOOGLE_CLIENT_SECRET']
GOOGLE_REDIRECT_URI = '/oauth2callback'

GITHUB_CLIENT_ID = env['GITHUB_CLIENT_ID']
GITHUB_CLIENT_SECRET = env['GITHUB_CLIENT_SECRET']
GITHUB_REDIRECT_URI = '/github_auth'
