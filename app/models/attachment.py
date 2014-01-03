from app import db
from datetime import datetime
from app.util import ago
from app.routes.oauth import google

class Attachment(db.Document):
    created_at = db.DateTimeField(default=datetime.utcnow(), required=True)
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

    def destroy(self):
        drive = google.drive_api(creds=self.project.author.google_creds)
        self.project.attachments.remove(self)
        self.parent.attachments.remove(self)
        drive.files().delete(fileId=self.file_id).execute()
        self.delete()
