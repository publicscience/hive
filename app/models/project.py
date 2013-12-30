from app import db
from slugify import slugify
from mongoengine import signals
import datetime

class Project(db.Document):
    created_at = db.DateTimeField(default=datetime.datetime.now, required=True)
    updated_at = db.DateTimeField(default=datetime.datetime.now, required=True)
    name = db.StringField(max_length=255, required=True, unique=True)
    repo = db.StringField(max_length=255)
    slug = db.StringField(max_length=255)
    issues = db.ListField(db.ReferenceField('Issue'))
    author = db.ReferenceField('User')

    # Not being used yet but later there may be need for this.
    users = db.ListField(db.ReferenceField('User'))

    meta = {
            'allow_inheritance': True,
            'indexes': ['-created_at'],
            'ordering': ['-updated_at']
    }

    def clean(self):
        self.slug = slugify(self.name)
        self.updated_at = datetime.datetime.now

    def open(self):
        return [issue for issue in self.issues if issue.open]

    def closed(self):
        return [issue for issue in self.issues if not issue.open]

    @classmethod
    def pre_delete(cls, sender, document, **kwargs):
        for issue in document.issues:
            issue.delete()

signals.pre_delete.connect(Project.pre_delete, sender=Project)
