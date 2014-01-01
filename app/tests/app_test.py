import unittest
from app import app

class AppTest(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()

    def test_static(self):
        r = self.app.get('/robots.txt')
        self.assertTrue(r.data)
        self.assertEquals(r.status_code, 200)
