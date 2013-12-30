from app import db
import datetime
from . import ago

class Event(db.EmbeddedDocument):
    created_at = db.DateTimeField(default=datetime.datetime.now, required=True)
    type = db.StringField(required=True, max_length=255)
    author = db.ReferenceField('User')

    def ago(self):
        return ago(time=self.created_at)
