from app import db
from gfm import markdown
from app.util import ago, parse_markup, parse_mentions, parse_issues
from app.routes.oauth import github
from . import event, user, comment
from datetime import datetime
import json
from mongoengine import signals
from flask import url_for

class Issue(db.Document):
    created_at = db.DateTimeField(default=datetime.utcnow(), required=True)
    updated_at = db.DateTimeField(default=datetime.utcnow(), required=True)
    title = db.StringField(max_length=255, required=True, default='New Issue')
    body = db.StringField(verbose_name='Issue', default='')
    author = db.ReferenceField('User')
    comments = db.ListField(db.EmbeddedDocumentField(comment.Comment))
    events = db.ListField(db.EmbeddedDocumentField(event.Event))
    labels = db.ListField(db.StringField(max_length=50))
    open = db.BooleanField(default=True)
    project = db.ReferenceField('Project')
    github_id = db.IntField()
    mentions = db.ListField(db.ReferenceField('User'))
    references = db.ListField(db.ReferenceField('self'))

    meta = {
            'allow_inheritance': True,
            'indexes': ['-created_at', 'author'],
            'ordering': ['updated_at']
    }

    # Called prior to saving.
    def clean(self):
        self.updated_at = datetime.utcnow()

    # Handle some additional processing.
    def process(self, data):
        self.labels = [label.strip() for label in data.get('labels').split(',') if label]
        self.author = user.current_user()

        self.save()

        # Creates/updates a corresponding GitHub issue if conditions are met.
        self.push_to_github()

        # Parses and saves mentions on the issue and mentioned users.
        # This has to happen after saving so the issue has an ID.
        self.parse_mentions()

        # Process references to other issues.
        # This has to happen after saving so the issue has an ID.
        self.parse_references(self.body)

    def push_to_github(self):
        # Update corresponding GitHub issue.
        if self.github_id:
            url = self.linked_url()
            resp = github.api().patch(url, data=json.dumps({
                'title': self.title,
                'body': self.body,
                'labels': self.labels
            }))
            if resp.status_code != 200:
                raise Exception()

        # Create issue on GitHub if flag is present.
        elif '%github' in self.body:
            url = '/repos/'+self.project.repo+'/issues'
            resp = github.api().post(url, data=json.dumps({
                'title': self.title,
                'body': self.body,
                'labels': self.labels
            }))
            if resp.status_code != 201:
                raise Exception()

            self.github_id = resp.json()['number']

    def parse_mentions(self):
        # Parse out mentions and find authors.
        current_mentioned_ids = set([e.google_id for e in self.mentions])
        mentioned_ids = set([(match.group('id')) for match in parse_mentions(self.body)])
        new_mentions = mentioned_ids - current_mentioned_ids
        old_mentions = current_mentioned_ids - mentioned_ids

        # Add in new mentions.
        for id in new_mentions:
            u = user.User.objects(google_id=id).first()
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

    def parse_references(self, text):
        # Process references to other issues.
        referenced_issue_ids = parse_issues(text)
        for id in referenced_issue_ids:
            i = Issue.objects(id=id).first()
            # If this is a newly referenced issue,
            # create an event in the referenced issue.
            if i and i not in self.references:
                data = {
                        'project_slug': self.project.slug,
                        'referencer_id': self.id,
                        'referencer_title': self.title
                }
                self.references.append(i)
                e = event.Event(type='referenced', data=data)
                i.events.append(e)
                i.save()
        self.save()

    @classmethod
    def pre_delete(cls, sender, document, **kwargs):
        # Have to manually clean up references to this issue.
        for u in document.mentions:
            u.references = [r for r in u.references if r != self]

    # Corresponding GitHub endpoint for this issue.
    def linked_url(self, end=''):
        if self.linked():
            return '/repos/'+self.project.repo+'/issues/'+str(self.github_id)+end

    # Sync this issue with its GitHub correlate (if it exists).
    # Syncing is on behalf of the issue's project's author.
    # Optionally pass in data to update with.
    def sync(self, data=None):
        if self.linked() and self.project.linked():

            self._sync_data(data=data)
            self._sync_comments()
            self._sync_events()
            self.save()

    def _sync_data(self, data=None):
        # Syncs issue data with its GitHub correlate (if it exists).
        # Optionally pass in data to update with.
        default_author = user.User.default()
        token = self.project.author.github_access

        if data is None:
            data = github.api(token=token).get(self.linked_url()).json()

        # Process data and apply it to the issue.
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

    def _sync_comments(self):
        # Get comments, and update them all.
        default_author = user.User.default()
        token = self.project.author.github_access
        gcs = github.api(token=token).get(self.linked_url(end='/comments')).json()
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

    def _sync_events(self):
        # Get events,and update them all.
        default_author = user.User.default()
        token = self.project.author.github_access
        ges = github.api(token=token).get(self.linked_url(end='/events')).json()
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

    # Close the issue.
    def close(self):
        self.open = False
        if self.linked():
            github.api().patch(self.linked_url(), data=json.dumps({'state': 'closed'}))
        e = event.Event(type='closed', author=user.current_user())
        self.events.append(e)
        self.save()

    # Reopen the issue.
    def reopen(self):
        self.open = True
        if self.linked():
            github.api().patch(self.linked_url(), data=json.dumps({'state': 'open'}))
        e = event.Event(type='reopened', author=user.current_user())
        self.events.append(e)
        self.save()

    # Linked to Github or not.
    def linked(self):
        return bool(self.github_id)

    # All events, i.e. events and comments.
    def all_events(self):
        all_events = self.events + self.comments
        all_events.sort(key=lambda i:i.created_at)
        return all_events

    def ago(self):
        return ago(time=self.created_at)

    # GitHub flavorted Markdown & mention parsing.
    def parsed(self):
        parsed = self.body
        parsed = parse_markup(parsed)
        return markdown(parsed)

    # Most recent closed event.
    def last_closed_event(self):
        return next((e for e in reversed(self.events) if e.type=='closed'), None)

    # Most recent (re)opened event.
    def last_opened_event(self):
        return next((e for e in reversed(self.events) if e.type=='opened'), None)

    def find_comment(self, id):
        return next(c_ for c_ in self.comments if str(c_.id)==id)

    def delete_comment(self, id):
        c = self.find_comment(id)
        c.destroy()
        self.comments.remove(c)
        self.save()

signals.pre_delete.connect(Issue.pre_delete, sender=Issue)
