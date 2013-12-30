from app import db
from gfm import markdown
from . import ago, parse_mentions
from app.routes.oauth import github
from . import comment, event, user
from datetime import datetime
import json

class Issue(db.Document):
    created_at = db.DateTimeField(default=datetime.utcnow(), required=True)
    updated_at = db.DateTimeField(default=datetime.utcnow(), required=True)
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
            'ordering': ['-updated_at']
    }

    def clean(self):
        self.updated_at = datetime.utcnow()

    def process(self, data):
        self.labels = [label.strip() for label in data.get('labels').split(',')]
        self.author = user.current_user()

        if '%github' in self.body:
            url = '/repos/'+self.project.repo+'/issues'
            resp = github.api().post(url, data=json.dumps({
                'title': self.title,
                'body': self.body,
                'labels': self.labels
            }))

    def linked_url(self, end=''):
        if self.linked():
            return '/repos/'+self.project.repo+'/issues/'+str(self.github_id)+end

    def sync(self, data=None):
        if self.linked():
            default_author = user.User.default()

            if data is None:
                data = github.api().get(self.linked_url()).json()

            open = True if data['state'] == 'open' else False
            labels = [label['name'] for label in data['labels']]
            author = user.User.objects(github_id=data['user']['id']).first()
            if not author:
                author = default_author

            updates = {
                'created_at': datetime.strptime(data['created_at'], '%Y-%m-%dT%H:%M:%SZ'),
                'updated_at': datetime.strptime(data['updated_at'], '%Y-%m-%dT%H:%M:%SZ'),
                'title': data['title'],
                'body': data['body'],
                'open': open,
                'labels': labels,
                'author': author
            }
            for k,v in updates.iteritems():
                setattr(self, k, v)


            # Get comments, and update them all.
            gcs = github.api().get(self.linked_url(end='/comments')).json()
            for gc in gcs:
                # Clean up redundant/outdated comment.
                c = next((c_ for c_ in self.comments if c_.github_id==gc['id']), 0)
                if c:
                    self.comments.remove(c)

                c = comment.Comment()

                c_author = user.User.objects(github_id=gc['user']['id']).first()
                if not c_author:
                    c_author = default_author

                c_updates = {
                        'github_id': gc['id'],
                        'created_at': datetime.strptime(gc['created_at'], '%Y-%m-%dT%H:%M:%SZ'),
                        'updated_at': datetime.strptime(gc['updated_at'], '%Y-%m-%dT%H:%M:%SZ'),
                        'body': gc['body'],
                        'author': c_author
                }
                for k,v in c_updates.iteritems():
                    setattr(c, k, v)
                self.comments.append(c)

            # Get events,and update them all.
            ges = github.api().get(self.linked_url(end='/events')).json()
            for ge in ges:
                # Clean up redundant/outdated event.
                e = next((e_ for e_ in self.events if e_.github_id==ge['id']), 0)
                if e:
                    self.events.remove(e)

                e = event.Event()

                e_author = user.User.objects(github_id=ge['actor']['id']).first()
                if not e_author:
                    e_author = default_author

                e_updates = {
                        'github_id': ge['id'],
                        'created_at': datetime.strptime(ge['created_at'], '%Y-%m-%dT%H:%M:%SZ'),
                        'type': ge['event'],
                        'author': e_author,
                        'commit_id': ge['commit_id']
                }
                for k,v in e_updates.iteritems():
                    setattr(e, k, v)
                self.events.append(e)
            self.save()

    def close(self):
        self.open = False
        if self.linked():
            github.api().patch(self.linked_url(), data=json.dumps({'state': 'closed'}))
        e = event.Event(type='closed', author=user.current_user())
        self.events.append(e)
        self.save()

    def reopen(self):
        self.open = True
        if self.linked():
            github.api().patch(self.linked_url(), data=json.dumps({'state': 'open'}))
        e = event.Event(type='reopened', author=user.current_user())
        self.events.append(e)
        self.save()

    def linked(self):
        """
        Linked to Github or not.
        """
        return bool(self.github_id)

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
