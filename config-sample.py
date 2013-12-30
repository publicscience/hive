from os import environ as env

if not env.get('HEROKU'):
    CSRF_ENABLED = True
    SECRET_KEY = 'some-passphrase'
    MONGODB_SETTINGS = {'DB': 'pubsci_hive'}

    AUTH_USER = 'admin'
    AUTH_PASS = 'password'

    MAIL_HOST = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USER = 'some@email.com'
    MAIL_PASS = 'somepass'
    MAIL_TARGETS = ['someadmin@email.com']

    GOOGLE_API_KEY = 'some-key'
    GOOGLE_CLIENT_ID = 'some-id'
    GOOGLE_CLIENT_SECRET = 'some-secret'
    GOOGLE_REDIRECT_URI = '/oauth2callback'

    GITHUB_CLIENT_ID = 'some-id'
    GITHUB_CLIENT_SECRET = 'some-secret'
    GITHUB_REDIRECT_URI = '/github_auth'

else:
    # This is a config file for deploying to Heroku.
    # Set these values as environment variables in your Heroku environment with:
    # $ heroku config:add SOME_VAR=some_value

    CSRF_ENABLED = True
    SECRET_KEY = env['SECRET_KEY']
    MONGODB_SETTINGS = {'DB': 'pubsci_hive'}

    AUTH_USER = env['AUTH_USER']
    AUTH_PASS = env['AUTH_PASS']

    MAIL_HOST = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USER = env['MAIL_USER']
    MAIL_PASS = env['MAIL_PASS']
    MAIL_TARGETS = ['someadmin@email.com']

    GOOGLE_API_KEY = env['GOOGLE_API_KEY']
    GOOGLE_CLIENT_ID = env['GOOGLE_CLIENT_ID']
    GOOGLE_CLIENT_SECRET = env['GOOGLE_CLIENT_SECRET']
    GOOGLE_REDIRECT_URI = '/oauth2callback'

    GITHUB_CLIENT_ID = env['GITHUB_CLIENT_ID']
    GITHUB_CLIENT_SECRET = env['GITHUB_CLIENT_SECRET']
    GITHUB_REDIRECT_URI = '/github_auth'
