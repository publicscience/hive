from app import db
from datetime import datetime
from app.util import ago
from app.routes.oauth import google
from mongoengine import signals

class Attachment(db.Document):
    created_at = db.DateTimeField(default=datetime.utcnow, required=True)
    file_id = db.StringField(required=True)
    project = db.ReferenceField('Project', required=True)
    parent = db.GenericReferenceField()

    def ago(self):
        return ago(time=self.created_at)

    # Returns Google Drive URL for this attachment.
    def url(self):
        drive = google.drive_api(creds=self.project.author.google_creds)
        file = drive.files().get(fileId=self.file_id).execute()
        return {
            'full': file.get('webContentLink'),
            'thumb': file.get('thumbnailLink')
        }

    @classmethod
    def pre_delete(cls, sender, document, **kwargs):
        drive = google.drive_api(creds=document.project.author.google_creds)

        document.project.attachments.remove(document)
        document.project.save()

        document.parent.attachments.remove(document)
        document.parent.save()

        drive.files().delete(fileId=document.file_id).execute()

signals.pre_delete.connect(Attachment.pre_delete, sender=Attachment)
