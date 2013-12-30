from app import db
from flask import url_for, session
import datetime
from app.routes.oauth import google

class User(db.Document):
    created_at = db.DateTimeField(default=datetime.datetime.now, required=True)
    name = db.StringField(max_length=255)
    picture = db.URLField()
    google_id = db.StringField(required=True, unique=True)
    github_id = db.IntField() # note: setting unique=True automatically sets required=True

    def linked(self):
        return bool(self.github_id)

    @classmethod
    def default(cls):
        # Return a default user.
        return User.objects(github_id=0).first()

# Create the default Github user.
if not User.objects(google_id='0'):
    user = User(
            google_id='0',
            github_id=0,
            name='A pal on Github',
            picture='http://localhost:5000/assets/img/github_pal.png'
    )
    user.save()

def current_user():
    """
    Return current session's user,
    or fetch user data from Google.

    Response looks like:
    {
     "id": "1111111111",
     "name": "Francis Tseng",
     "given_name": "Francis",
     "family_name": "Tseng",
     "link": "https://plus.google.com/...",
     "picture": "https://lh6.googleusercontent.com/...",
     "gender": "male",
     "locale": "en"
    }
    """

    if not session.get('user_id', False):
        # Get and store user info in session.
        response = google.api().get('https://www.googleapis.com/oauth2/v1/userinfo?')
        g_user = response.json()
        user, created = User.objects.get_or_create(google_id=g_user['id'])
        user.name = g_user['name']
        user.picture = g_user['picture']
        user.save()
        session['user_id'] = g_user['id']
    else:
        user = User.objects.get(google_id=session['user_id'])
    return user
