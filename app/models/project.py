from app import db, app
from slugify import slugify
from mongoengine import signals
from app.routes.oauth import github, google
from app.models.user import current_user
from datetime import datetime
from . import issue
from apiclient.http import MediaFileUpload
from app.models.attachment import Attachment
from werkzeug import secure_filename
import os

class Project(db.Document):
    created_at = db.DateTimeField(default=datetime.utcnow, required=True)
    updated_at = db.DateTimeField(default=datetime.utcnow, required=True)
    name = db.StringField(max_length=255, required=True, unique=True)
    repo = db.StringField(max_length=255)
    slug = db.StringField(max_length=255)
    issues = db.ListField(db.ReferenceField('Issue'))
    author = db.ReferenceField('User', default=current_user, required=True)

    # Google Drive Folder id
    folder_id = db.StringField()

    attachments = db.ListField(db.ReferenceField('Attachment'))

    # Not being used yet but later there may be need for this.
    users = db.ListField(db.ReferenceField('User'))

    meta = {
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

    def process_attachments(self, files, parent):
        for k, file in files.iteritems():
            filename = file.filename
            if file and \
                    '.' in filename and \
                    filename.split('.', 1)[1] in app.config['ALLOWED_EXTENSIONS']:
                filename = secure_filename(filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)

                file_id = self.upload_file(filepath)
                attachment = Attachment(file_id=file_id)
                attachment.project = self
                attachment.parent = parent
                attachment.save()

                self.attachments.append(attachment)
                self.save()

                parent.attachments.append(attachment)
                parent.save()

    # Create a Google Drive folder for this project.
    def create_folder(self):
        body = {
            'title': self.name,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        drive = google.drive_api(creds=self.author.google_creds)
        resp = drive.files().insert(body=body).execute()
        folder_id = resp['id']

        # Add permissions for all of this project's users.
        for user in self.users:
            if user is not self.author:
                permission = {
                    'value': user.email,
                    'type': 'user',
                    'role': 'writer'
                }
                drive.permissions().insert(
                        fileId=folder_id,
                        sendNotificationEmails=False,
                        body=permission
                ).execute()

        self.folder_id = folder_id
        self.save()

    # Delete this project's Google Drive folder,
    # if it's empty.
    def delete_folder(self):
        drive = google.drive_api(creds=self.author.google_creds)
        children = drive.children().list(folderId=self.folder_id).execute()

        # Only delete the folder if it is empty.
        if len(children.get('items', [])) == 0:
            drive.files().delete(fileId=self.folder_id).execute()

    def upload_file(self, filename):
        drive = google.drive_api(creds=self.author.google_creds)
        media_body = MediaFileUpload(filename, resumable=True)
        body = {
                'title': filename.split('/')[-1],
                'parents': [{'id': self.folder_id}]
        }
        file = drive.files().insert(body=body, media_body=media_body).execute()
        return file['id']

    def folder_url(self):
        #drive = google.drive_api(creds=self.author.google_creds)
        #folder = drive.files().get(fileId=self.folder_id).execute()
        #return folder.get('alternateLink')
        return 'https://drive.google.com/#folders/%s' % self.folder_id

    @classmethod
    def pre_delete(cls, sender, document, **kwargs):
        for issue in document.issues:
            issue.delete()
        document.delete_folder()

signals.pre_delete.connect(Project.pre_delete, sender=Project)
