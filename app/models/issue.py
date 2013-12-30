from app import db
from gfm import markdown
from . import ago, parse_mentions
from . import comment, event
import datetime

class Issue(db.Document):
    created_at = db.DateTimeField(default=datetime.datetime.now, required=True)
    title = db.StringField(max_length=255, required=True, default='Issue')
    body = db.StringField(verbose_name='Issue')
    author = db.ReferenceField('User')
    comments = db.ListField(db.EmbeddedDocumentField(comment.Comment))
    events = db.ListField(db.EmbeddedDocumentField(event.Event))
    labels = db.ListField(db.StringField(max_length=50))
    open = db.BooleanField(default=True)
    project = db.ReferenceField('Project')
    github_id = db.IntField()

    meta = {
            'allow_inheritance': True,
            'indexes': ['-created_at', 'author'],
            'ordering': ['-created_at']
    }

    def ago(self):
        return ago(time=self.created_at)

    def parsed(self):
        parsed = self.body
        parsed = parse_mentions(parsed)
        return markdown(parsed)

    def last_closed_event(self):
        return next((e for e in reversed(self.events) if e.type=='closed'), None)

    def last_opened_event(self):
        return next((e for e in reversed(self.events) if e.type=='opened'), None)

    def find_comment(self, id):
        return next((c for c in self.comments if c.id==id), None)
