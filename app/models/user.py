from app import db
from flask import url_for, session
import datetime
from app.routes.oauth import google

class User(db.Document):
    created_at = db.DateTimeField(default=datetime.datetime.utcnow(), required=True)
    name = db.StringField(max_length=255)
    email = db.EmailField(required=True)
    picture = db.URLField()
    google_id = db.StringField(required=True, unique=True)
    github_id = db.IntField() # note: setting unique=True automatically sets required=True
    github_access = db.StringField()
    google_creds = db.StringField()

    # When A mentions B, B is referenced by A.
    references = db.ListField(db.GenericReferenceField())

    # Linked to Github or not.
    def linked(self):
        return bool(self.github_id)

    @classmethod
    def default(cls):
        # Return a default user.
        def_user = User.objects(github_id=0).first()
        if not def_user:
            def_user = User(
                    google_id='0',
                    github_id=0,
                    name='A pal on Github',
                    picture='http://localhost:5000/assets/img/github_pal.png'
            )
            def_user.save()
        return def_user

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
     "locale": "en",
     "email": "someemail@gmail.com"
    }
    """

    if not session.get('user_id', False):
        # Get and store user info in session.
        g_user = google.user_info()
        user, created = User.objects.get_or_create(google_id=g_user['id'], email=g_user['email'])
        user.name = g_user['name']
        user.picture = g_user.get('picture', url_for('static', filename='/assets/img/default_pic.png', _external=True))
        user.save()
        session['user_id'] = g_user['id']
    else:
        user = User.objects.get(google_id=session['user_id'])
    return user
