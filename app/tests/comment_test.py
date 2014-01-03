from . import AppCase
from app.models.comment import Comment

class CommentTest(AppCase):
    def setUp(self):
        self.setup_app()
        self.create_user()
        self.create_issue()

        self.comment = Comment(
                body='foo bar',
                issue=self.test_issue,
                author=self.test_user
        )
        self.comment.save()

    def tearDown(self):
        self.teardown_dbs()

    def test_pre_delete(self):
        self.test_user.references.append(self.comment)
        self.test_user.save()

        self.test_issue.comments.append(self.comment)
        self.test_issue.save()

        self.comment.mentions.append(self.test_user)
        self.comment.save()

        self.assertEqual(Comment.objects.count(), 1)
        self.assertEqual(len(self.test_user.references), 1)
        self.assertEqual(len(self.test_issue.comments), 1)

        self.comment.delete()

        self.assertEqual(Comment.objects.count(), 0)
        self.assertEqual(len(self.test_user.references), 0)
        self.assertEqual(len(self.test_issue.comments), 0)
