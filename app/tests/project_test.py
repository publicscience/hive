from mock import MagicMock
from . import AppCase
from app.models.project import Project
from app.models.issue import Issue

class ProjectTest(AppCase):
    def setUp(self):
        self.setup_app()
        self.create_user()
        self.create_issue()

        self.project = Project(
                name='foo bar',
                repo='foo/bar',
                author=self.test_user
        )
        self.project.issues.append(self.test_issue)
        self.project.save()

        self.test_issue.project = self.project
        self.test_issue.save()

    def tearDown(self):
        self.teardown_dbs()

    def test_process_attachments(self):
        file = MagicMock()
        file.filename = 'foo.jpg'
        files = {'file0': file }
        self.project.upload_file = MagicMock(return_value='12345')

        self.project.process_attachments(files, self.test_issue)

        attachment = self.project.attachments[0]
        self.assertEqual(attachment.file_id, '12345')
        self.assertEqual(attachment.project, self.project)
        self.assertEqual(attachment.parent, self.test_issue)

    def test_process_attachments_disallowed_extension(self):
        file = MagicMock()
        file.filename = 'foo.sh'
        files = {'file0': file }

        self.project.process_attachments(files, self.test_issue)

        self.assertEqual(len(self.project.attachments), 0)


    def test_pre_delete(self):
        self.assertEqual(Issue.objects.count(), 1)

        self.project.delete()

        self.assertEqual(Issue.objects.count(), 0)
