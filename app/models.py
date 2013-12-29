import datetime
from app import db

class User(db.Document):
    created_at = db.DateTimeField(default=datetime.datetime.now, required=True)
    name = db.StringField(max_length=255)
    picture = db.URLField()
    google_id = db.StringField(required=True, unique=True)

class Comment(db.EmbeddedDocument):
    created_at = db.DateTimeField(default=datetime.datetime.now, required=True)
    body = db.StringField(verbose_name="Comment", required=True)
    author = db.ReferenceField(User)

class Event(db.EmbeddedDocument):
    created_at = db.DateTimeField(default=datetime.datetime.now, required=True)
    type = db.StringField(required=True, max_length=255)
    author = db.ReferenceField(User)

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

    def last_closed_event(self):
        return next((e for e in self.events if e.type=='closed'), None)

    def last_opened_event(self):
        return next((e for e in self.events if e.type=='opened'), None)

