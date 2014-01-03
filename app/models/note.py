from app import db
from datetime import datetime
from app.util import ago, parse_markup, parse_mentions, parse_issues
from gfm import markdown
from app.models.user import current_user, User

# Generic class
class Note(db.Document):
    created_at = db.DateTimeField(default=datetime.utcnow, required=True)
    updated_at = db.DateTimeField(default=datetime.utcnow, required=True)
    author = db.ReferenceField('User', required=True, default=current_user)
    mentions = db.ListField(db.ReferenceField('User'))
    attachments = db.ListField(db.ReferenceField('Attachment'))
    body = db.StringField(default='')

    meta = {
            'allow_inheritance': True
    }

    # Called prior to saving.
    def clean(self):
        self.updated_at = datetime.utcnow()

    # Do some processing and then save.
    def process(self):
        self.save()
        self.parse_mentions()

    def ago(self):
        return ago(time=self.created_at)

    # GitHub flavored Markdown & mention parsing.
    def parsed(self):
        parsed = self.body
        parsed = parse_markup(parsed)
        return markdown(parsed)

    # Parse out mentions and find authors.
    def parse_mentions(self):
        current_mentioned_ids = set([e.google_id for e in self.mentions])
        mentioned_ids = set([(match.group('id')) for match in parse_mentions(self.body)])
        new_mentions = mentioned_ids - current_mentioned_ids
        old_mentions = current_mentioned_ids - mentioned_ids

        # Add in new mentions.
        for id in new_mentions:
            u = User.objects(google_id=id).first()
            if u:
                self.mentions.append(u)
                u.references.append(self) # Add issue to the user as well
                u.save()

        # Remove mentions that are gone now.
        for id in old_mentions:
            u = next((u_ for u_ in self.mentions if u_.google_id==id), 0)
            if u:
                self.mentions.remove(u)
                u.references.remove(self) # Remove from the user as well
                u.save()
        self.save()
