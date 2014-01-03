import unittest
from mock import patch, MagicMock

from app import app
from app.models.issue import Issue
from app.models.user import User
from app.models.project import Project

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

    def teardown_dbs(self):
        Issue.drop_collection()
        User.drop_collection()
        Project.drop_collection()
