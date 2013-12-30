from app import db
from bson.objectid import ObjectId
from gfm import markdown
from . import ago, parse_mentions
from datetime import datetime

class Comment(db.EmbeddedDocument):
    id = db.ObjectIdField(required=True, default=ObjectId, unique=True)
    created_at = db.DateTimeField(default=datetime.utcnow(), required=True)
    updated_at = db.DateTimeField(default=datetime.utcnow(), required=True)
    body = db.StringField(verbose_name="Comment", required=True)
    author = db.ReferenceField('User')
    github_id = db.IntField()

    # Called prior to saving.
    def clean(self):
        self.updated_at = datetime.utcnow()

    def ago(self):
        return ago(time=self.created_at)

    # GitHub flavorted Markdown & mention parsing.
    def parsed(self):
        parsed = self.body
        parsed = parse_mentions(parsed)
        return markdown(parsed)
