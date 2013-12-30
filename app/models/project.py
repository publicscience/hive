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
            'ordering': ['updated_at']
    }

    # Called prior to saving.
    def clean(self):
        self.slug = slugify(self.name)
        self.updated_at = datetime.utcnow()

    def open(self):
        return [issue for issue in self.issues if issue.open]

    def closed(self):
        return [issue for issue in self.issues if not issue.open]

    # Sync this project with its GitHub correlate (if it exists).
    # Syncs on behalf of the project author.
    def sync(self):
        if self.linked():
            token = self.author.github_access
            github_issues = github.api(token=token).get('/repos/'+self.repo+'/issues').json() + github.api(token=token).get('/repos/'+self.repo+'/issues', params={'state': 'closed'}).json()
            for gi in github_issues:
                i, created = issue.Issue.objects.get_or_create(github_id=gi['number'], project=self)
                if created:
                    self.issues.append(i)
                i.sync(data=gi)
            self.save()

    # Linked to GitHub or not.
    def linked(self):
        return bool(self.repo and self.author.linked())

    # Check for the repo on GitHub.
    def ping_repo(self):
        token = self.author.github_access
        resp = github.api(token=token).get('/repos/'+self.repo)
        return resp.status_code == 200

    @classmethod
    def pre_delete(cls, sender, document, **kwargs):
        for issue in document.issues:
            issue.delete()

signals.pre_delete.connect(Project.pre_delete, sender=Project)
