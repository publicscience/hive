import json
from mock import MagicMock
from app import app
from . import AppCase
from app.models.issue import Issue
from app.models.user import User
from app.models.project import Project
from app.models.comment import Comment

class IssueTest(AppCase):
    def setUp(self):
        self.setup_app()
        self.create_user()
        self.create_project()

        self.mock_current_user = self.create_patch('app.models.user.current_user')
        self.mock_current_user.return_value = self.test_user

        self.issue = Issue(
                title='Some important issue',
                project=self.test_project,
                author=self.test_user
        )
        self.issue.save()

    def tearDown(self):
        self.teardown_dbs()

    def test_db_starting_state(self):
        # Expected to be 1 because we create an issue in the setUp method.
        self.assertEqual(Issue.objects.count(), 1)

    def test_close(self):
        with app.test_request_context():
            self.issue.close()
            self.assertFalse(self.issue.open)
            self.assertEqual(len(self.issue.events), 1)

    def test_close_linked(self):
        self.issue.github_id = 1
        self.issue.linked_url = MagicMock(return_value='foo')
        with app.test_request_context():
            self.issue.close()
            self.mock_github_api.patch.assert_called_with(
                    'foo',
                    data=json.dumps({'state':'closed'})
            )

    def test_reopen(self):
        with app.test_request_context():
            self.issue.reopen()
            self.assertTrue(self.issue.open)
            self.assertEqual(len(self.issue.events), 1)

    def test_reopen_linked(self):
        self.issue.github_id = 1
        self.issue.linked_url = MagicMock(return_value='foo')
        with app.test_request_context():
            self.issue.reopen()
            self.mock_github_api.patch.assert_called_with(
                    'foo',
                    data=json.dumps({'state':'open'})
            )

    def test_parse_references(self):
        issue_ = Issue(
                title='Referenced issue',
                project=self.test_project,
                author=self.test_user
        )
        issue_.save()

        self.issue.body = 'Some body text referencing this issue /%s/issues/%s' % (self.test_project.name, issue_.id)

        self.issue.parse_references(self.issue.body)

        # Reload the issue so changes are reflected.
        issue_.reload()

        self.assertEqual(len(self.issue.references), 1)
        self.assertEqual(len(issue_.events), 1)
        self.assertEqual(self.issue.references[0].title, 'Referenced issue')
        self.assertEqual(issue_.events[0].data, {
            'project_slug': self.test_project.slug,
            'referencer_id': self.issue.id,
            'referencer_title': self.issue.title
        })

    def test_parse_mentions(self):
        u = User(name='Numpy', google_id='1', email='foo@email.com')
        u.save()

        # Tests adds mentions
        self.issue.body = 'Some body text with a mention @[Numpy](user:%s)' % u.google_id
        self.issue.parse_mentions()

        u.reload()

        self.assertEqual(len(self.issue.mentions), 1)
        self.assertEqual(len(u.references), 1)

        # Tests removes mentions
        self.issue.body = 'Some body text without a mention'
        self.issue.parse_mentions()

        u.reload()

        self.assertEqual(len(self.issue.mentions), 0)
        self.assertEqual(len(u.references), 0)

        # Tests multiple mentions
        u_ = User(name='Lumpy', google_id='2', email='bar@email.com')
        u_.save()

        self.issue.body = 'Some body text with two mentions @[Numpy](user:%s) @[Lumpy](user:%s)' % (u.google_id, u_.google_id)
        self.issue.parse_mentions()

        u.reload()
        u_.reload()

        self.assertEqual(len(self.issue.mentions), 2)
        self.assertEqual(len(u.references), 1)
        self.assertEqual(len(u_.references), 1)

        self.issue.body = 'Some body text with two mentions @[Lumpy](user:%s)' % u_.google_id
        self.issue.parse_mentions()

        u.reload()
        u_.reload()

        self.assertEqual(len(self.issue.mentions), 1)
        self.assertEqual(len(u.references), 0)
        self.assertEqual(len(u_.references), 1)

    def test_push_to_github_updates_linked_issue(self):
        self.issue.github_id = 1
        self.issue.linked_url = MagicMock(return_value='foo')

        resp = MagicMock()
        resp.status_code = 200

        self.mock_github_api.patch.return_value = resp

        self.issue.push_to_github()

        self.mock_github_api.patch.assert_called_with('foo', data=json.dumps({
            'title': self.issue.title,
            'body': self.issue.body,
            'labels': self.issue.labels
        }))

    def test_push_to_github_creates_linked_issue(self):
        self.issue.body = 'Let us create a %github issue'
        self.issue.linked_url = MagicMock(return_value='foo')

        resp = MagicMock()
        resp.status_code = 201
        resp.json.return_value = {'number': 1}

        self.mock_github_api.post.return_value = resp

        self.issue.push_to_github()

        self.assertEqual(self.issue.github_id, 1)

    def test_pre_delete(self):
        c = Comment(body='foo', author=self.test_user)
        c.issue = self.issue
        c.save()

        self.test_user.references.append(self.issue)
        self.test_user.save()

        self.issue.mentions.append(self.test_user)
        self.issue.comments.append(c)
        self.issue.save()

        self.assertEqual(Issue.objects.count(), 1)
        self.assertEqual(Comment.objects.count(), 1)
        self.assertEqual(len(self.test_user.references), 1)

        self.issue.delete()

        self.assertEqual(Issue.objects.count(), 0)
        self.assertEqual(Comment.objects.count(), 0)
        self.assertEqual(len(self.test_user.references), 0)

