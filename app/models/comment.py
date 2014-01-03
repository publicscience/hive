from app import db
from app.routes.oauth import github
import json
from flask import url_for
from app.models.note import Note
from mongoengine import signals

class Comment(Note):
    body = db.StringField(required=True)
    github_id = db.IntField()
    issue = db.ReferenceField('Issue', required=True)

    def process(self, files):
        self.save()
        self.parse_mentions()

        # Create comment on GitHub if its issue is linked.
        if self.issue.linked():
            if self.github_id:
                # UPDATE GITHUB COMMENT
                pass
            else:
                url = '/repos/' + self.issue.project.repo + '/issues/' + str(issue.github_id) + '/comments'
                resp = github.api().post(url, data=json.dumps({'body':self.body}))
                self.github_id = resp.json()['id']
        self.save()

        # Parse and create references to other issues.
        self.issue.parse_references(self.body)

        self.issue.project.process_attachments(files, self)

        if self not in self.issue.comments:
            self.issue.comments.append(self)
        self.issue.save()

    @classmethod
    def pre_delete(cls, sender, document, **kwargs):
        # Have to manually clean up references to this comment.
        for u in document.mentions:
            u.references = [r for r in u.references if r != document]
            u.save()
        document.issue.delete_comment(document.id)

signals.pre_delete.connect(Comment.pre_delete, sender=Comment)
