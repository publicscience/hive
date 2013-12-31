from app import db
from gfm import markdown
from . import ago, parse_markup, parse_mentions
from app.routes.oauth import github
from . import event, user
from datetime import datetime
from flask import url_for
from bson.objectid import ObjectId

class Comment(db.EmbeddedDocument):
    id = db.ObjectIdField(required=True, default=ObjectId, unique=True)
    created_at = db.DateTimeField(default=datetime.utcnow(), required=True)
    updated_at = db.DateTimeField(default=datetime.utcnow(), required=True)
    body = db.StringField(verbose_name="Comment", required=True)
    author = db.ReferenceField('User')
    github_id = db.IntField()
    mentions = db.ListField(db.ReferenceField('User'))

    # Called prior to saving.
    def clean(self):
        self.updated_at = datetime.utcnow()

    def ago(self):
        return ago(time=self.created_at)

    # GitHub flavorted Markdown & mention parsing.
    def parsed(self):
        parsed = self.body
        parsed = parse_markup(parsed)
        return markdown(parsed)

    def process(self):
        # Parse out mentions and find authors.
        current_mentioned_ids = set([e.id for e in self.mentions])
        mentioned_ids = set([match.group('id') for match in parse_mentions(self.body)])
        new_mentions = mentioned_ids - current_mentioned_ids
        old_mentions = current_mentioned_ids - mentioned_ids

        # Add in new mentions.
        for id in new_mentions:
            u = user.User.objects(id=id).first()
            if u:
                self.mentions.append(u)
                u.references.append(self) # Add issue to the user as well

        # Remove mentions that are gone now.
        for id in old_mentions:
            u = next((u_ for u_ in self.mentions if u_.id==id), 0)
            if u:
                self.mentions.remove(u)
                u.references.remove(self) # Remove from the user as well

    def destroy(self):
        # Have to manually clean up references to this comment.
        for u in self.mentions:
            u.references = [r for r in u.references if r != self]


