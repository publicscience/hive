from app import db
from datetime import datetime
from . import ago

class Event(db.EmbeddedDocument):
    created_at = db.DateTimeField(default=datetime.utcnow(), required=True)
    type = db.StringField(required=True, max_length=255)
    author = db.ReferenceField('User')
    github_id = db.IntField()
    commit_id = db.StringField(max_length=255)

    def ago(self):
        return ago(time=self.created_at)
