import unittest
from mock import patch, MagicMock

from app import app
from app.models.issue import Issue
from app.models.user import User
from app.models.project import Project
from app.models.attachment import Attachment
from app.models.comment import Comment

class RequiresMocks(unittest.TestCase):
    def create_patch(self, name, **kwargs):
        """
        Helper for patching/mocking methods.

        Args:
            | name (str)       -- the 'module.package.method' to mock.
        """
        patcher = patch(name, autospec=True, **kwargs)
        thing = patcher.start()
        self.addCleanup(patcher.stop)
        return thing

class AppCase(RequiresMocks):
    def setup_app(self):
        self.app = app.test_client()

        # Mock the GitHub API
        self.mock_github = self.create_patch('app.routes.oauth.github.api')
        self.mock_github_api = MagicMock()
        self.mock_github.return_value = self.mock_github_api

        # Mock the Google API
        self.mock_google_user_info = self.create_patch('app.routes.oauth.google.user_info')
        self.mock_google_drive_api = self.create_patch('app.routes.oauth.google.drive_api')
        self.mock_google_drive_api.return_value = MagicMock()

    def teardown_dbs(self):
        Issue.drop_collection()
        User.drop_collection()
        Project.drop_collection()
        Attachment.drop_collection()
        Comment.drop_collection()

    def create_user(self):
        self.test_user = User(
                name='Numpy Ping',
                google_id='12345',
                picture='http://foo.com/image.png',
                email='foo@email.com'
        )
        self.test_user.save()

    def create_project(self):
        if not hasattr(self, 'test_user'):
            self.create_user()
        self.test_project = Project(
                name='Proj',
                repo='pub/bar',
                author=self.test_user
        )
        self.test_project.save()

    def create_issue(self):
        if not hasattr(self, 'test_project'):
            self.create_project()
        self.test_issue = Issue(
                title='Some important issue',
                project=self.test_project,
                author=self.test_user
        )
        self.test_issue.save()
