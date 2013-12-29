import datetime
from app import db
from bson.objectid import ObjectId

def ago(time=False):
    """
    Get a datetime object or a int() Epoch timestamp and return a
    pretty string like 'an hour ago', 'Yesterday', '3 months ago',
    'just now', etc

    From: http://stackoverflow.com/a/1551394
    """
    from datetime import datetime
    now = datetime.now()
    if type(time) is int:
        diff = now - datetime.fromtimestamp(time)
    elif isinstance(time,datetime):
        diff = now - time 
    elif not time:
        diff = now - now
    second_diff = diff.seconds
    day_diff = diff.days

    if day_diff < 0:
        return ''

    if day_diff == 0:
        if second_diff < 10:
            return "just now"
        if second_diff < 60:
            return str(second_diff) + " seconds ago"
        if second_diff < 120:
            return  "a minute ago"
        if second_diff < 3600:
            return str( second_diff / 60 ) + " minutes ago"
        if second_diff < 7200:
            return "an hour ago"
        if second_diff < 86400:
            return str( second_diff / 3600 ) + " hours ago"
    if day_diff == 1:
        return "Yesterday"
    if day_diff < 7:
        return str(day_diff) + " days ago"
    if day_diff < 31:
        return str(day_diff/7) + " weeks ago"
    if day_diff < 365:
        return str(day_diff/30) + " months ago"
    return str(day_diff/365) + " years ago"


class User(db.Document):
    created_at = db.DateTimeField(default=datetime.datetime.now, required=True)
    name = db.StringField(max_length=255)
    picture = db.URLField()
    google_id = db.StringField(required=True, unique=True)

class Comment(db.EmbeddedDocument):
    id = db.ObjectIdField(required=True, default=ObjectId, unique=True)
    created_at = db.DateTimeField(default=datetime.datetime.now, required=True)
    body = db.StringField(verbose_name="Comment", required=True)
    author = db.ReferenceField(User)

    def ago(self):
        return ago(time=self.created_at)

class Event(db.EmbeddedDocument):
    created_at = db.DateTimeField(default=datetime.datetime.now, required=True)
    type = db.StringField(required=True, max_length=255)
    author = db.ReferenceField(User)

    def ago(self):
        return ago(time=self.created_at)

class Issue(db.Document):
    created_at = db.DateTimeField(default=datetime.datetime.now, required=True)
    title = db.StringField(max_length=255, required=True)
    body = db.StringField(verbose_name="Issue", required=True)
    author = db.ReferenceField(User)
    closer = db.ReferenceField(User)
    comments = db.ListField(db.EmbeddedDocumentField(Comment))
    events = db.ListField(db.EmbeddedDocumentField(Event))
    open = db.BooleanField(default=True)

    meta = {
            'allow_inheritance': True,
            'indexes': ['-created_at', 'author'],
            'ordering': ['-created_at']
    }

    def ago(self):
        return ago(time=self.created_at)

    def last_closed_event(self):
        return next((e for e in reversed(self.events) if e.type=='closed'), None)

    def last_opened_event(self):
        return next((e for e in reversed(self.events) if e.type=='opened'), None)

    def find_comment(self, id):
        return next((c for c in self.comments if c.id==id), None)

