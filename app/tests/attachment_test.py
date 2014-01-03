from . import AppCase
from app.models.attachment import Attachment

class AttachmentTest(AppCase):
    def setUp(self):
        self.setup_app()
        self.create_project()
        self.create_issue()

        self.attachment = Attachment(
                file_id='12345',
                project=self.test_project,
                parent=self.test_issue
        )
        self.attachment.save()

    def tearDown(self):
        self.teardown_dbs()

    def test_pre_delete(self):
        self.test_project.attachments.append(self.attachment)
        self.test_project.save()

        self.test_issue.attachments.append(self.attachment)
        self.test_issue.save()

        self.assertEqual(Attachment.objects.count(), 1)
        self.assertEqual(len(self.test_issue.attachments), 1)
        self.assertEqual(len(self.test_project.attachments), 1)

        self.attachment.delete()

        self.assertEqual(Attachment.objects.count(), 0)
        self.assertEqual(len(self.test_issue.attachments), 0)
        self.assertEqual(len(self.test_project.attachments), 0)
