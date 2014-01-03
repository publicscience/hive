CSRF_ENABLED = True
SECRET_KEY = 'some-passphrase'
MONGODB_SETTINGS = {'DB': 'pubsci_hive'}

UPLOAD_FOLDER = '/tmp/'
ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])

AUTH_USER = 'admin'
AUTH_PASS = 'password'

MAIL_HOST = 'smtp.gmail.com'
MAIL_PORT = 587
MAIL_USER = 'some@email.com'
MAIL_PASS = 'somepass'
MAIL_TARGETS = ['someadmin@email.com']

GOOGLE_CLIENT_ID = 'some-id'
GOOGLE_CLIENT_SECRET = 'some-secret'
GOOGLE_REDIRECT_URI = '/oauth2callback'

GITHUB_CLIENT_ID = 'some-id'
GITHUB_CLIENT_SECRET = 'some-secret'
GITHUB_REDIRECT_URI = '/github_auth'
