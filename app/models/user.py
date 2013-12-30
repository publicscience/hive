from app import db
from flask import url_for
import datetime

class User(db.Document):
    created_at = db.DateTimeField(default=datetime.datetime.now, required=True)
    name = db.StringField(max_length=255)
    picture = db.URLField()
    google_id = db.StringField(required=True, unique=True)
    github_id = db.IntField() # note: setting unique=True automatically sets required=True

# Create the default Github user.
if not User.objects(google_id='0'):
    user = User(
            google_id='0',
            github_id=0,
            name='A pal on Github',
            picture='http://localhost:5000/assets/img/github_pal.png'
    )
    user.save()
