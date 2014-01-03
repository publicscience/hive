import unittest
from app import util

class UtilTest(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_parse_issues(self):
        text = 'hey there http://hive.publicscience.co/p/something/issues/52c250f205aaef33ae1051c7/ foo'
        ids = util.parse_issues(text)
        self.assertEqual(ids, ['52c250f205aaef33ae1051c7'])

    def test_parse_issues_localhost(self):
        text = 'hey there http://localhost:5000/p/something/issues/52c250f205aaef33ae1051c7/ foo'
        ids = util.parse_issues(text)
        self.assertEqual(ids, ['52c250f205aaef33ae1051c7'])

    def test_parse_issues_multiple(self):
        text = 'hey there http://hive.publicscience.co/p/something/issues/52c250f205aaef33ae1051c7/ foo http://hive.publicscience.co/something/issues/52c350bd05aaef1c313dc2fe/'
        ids = util.parse_issues(text)
        self.assertEqual(ids, ['52c250f205aaef33ae1051c7', '52c350bd05aaef1c313dc2fe'])

    def test_parse_issues_optional_full_url(self):
        text = 'hey there /something/issues/52c250f205aaef33ae1051c7/ foo'
        ids = util.parse_issues(text)
        self.assertEqual(ids, ['52c250f205aaef33ae1051c7'])

    def test_parse_mentions(self):
        text = 'hey there @[Francis Tseng](user:123456) foo'
        for m in util.parse_mentions(text):
            self.assertEqual(m.group('mention'), 'Francis Tseng')
            self.assertEqual(m.group('type'), 'user')
            self.assertEqual(m.group('id'), '123456')

    def test_parse_mentions_multiple(self):
        text = 'hey there @[Francis Tseng](user:123456) foo @[Kira SK](user:7890)'
        mentions = [m for m in util.parse_mentions(text)]
        self.assertEqual(mentions[0].group('mention'), 'Francis Tseng')
        self.assertEqual(mentions[0].group('type'), 'user')
        self.assertEqual(mentions[0].group('id'), '123456')
        self.assertEqual(mentions[1].group('mention'), 'Kira SK')
        self.assertEqual(mentions[1].group('type'), 'user')
        self.assertEqual(mentions[1].group('id'), '7890')
