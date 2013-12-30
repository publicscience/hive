from app import db
from slugify import slugify
from mongoengine import signals
from app.routes.oauth import github
from datetime import datetime
from . import issue

class Project(db.Document):
    created_at = db.DateTimeField(default=datetime.utcnow(), required=True)
    updated_at = db.DateTimeField(default=datetime.utcnow(), required=True)
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
        self.updated_at = datetime.utcnow()

    def open(self):
        return [issue for issue in self.issues if issue.open]

    def closed(self):
        return [issue for issue in self.issues if not issue.open]

    def sync(self):
        if self.linked():
            # Sync on behalf of the project author.
            token = self.author.github_access
            gis = github.api(token=token).get('/repos/'+self.repo+'/issues').json() + github.api(token=token).get('/repos/'+self.repo+'/issues', params={'state': 'closed'}).json()
            for gi in gis:
                i, created = issue.Issue.objects.get_or_create(github_id=gi['number'], project=self)
                if created:
                    self.issues.append(i)
                i.sync(data=gi)

    def linked(self):
        return bool(self.repo and self.author.linked())

    @classmethod
    def pre_delete(cls, sender, document, **kwargs):
        for issue in document.issues:
            issue.delete()

signals.pre_delete.connect(Project.pre_delete, sender=Project)
