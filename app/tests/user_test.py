import json
from mock import MagicMock
from app import app
from app.models.user import User, current_user
from flask import session
from . import AppCase

class UserTest(AppCase):
    def setUp(self):
        self.setup_app()

    def tearDown(self):
        self.teardown_dbs()

    def test_empty_db(self):
        self.assertEqual(User.objects.count(), 0)

    def test_default_user(self):
        default = User.default()
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(default.name, 'A pal on Github')

    def test_creates_current_user(self):
        self.mock_google_user_info.return_value = {
                'id': '12345',
                'name': 'Numpy',
                'picture': 'http://foo.com/image.png',
                'email': 'foo@gmail.com'
        }

        with app.test_request_context():
            c_user = current_user()
            self.assertEqual(session['user_id'], '12345')
            self.assertEqual(User.objects.count(), 1)

    def test_default_user_image(self):
        self.mock_google_user_info.return_value = {
                'id': '12345',
                'name': 'Numpy',
                'email': 'foo@gmail.com'
        }
        with app.test_request_context():
            c_user = current_user()
            self.assertEqual(c_user.picture, 'http://localhost/assets/img/default_pic.png')

    def test_returns_current_user(self):
        u = User(name='Numpy', google_id='12345', email='foo@gmail.com')
        u.save()
        with app.test_request_context():
            session['user_id'] = '12345'
            c_user = current_user()
            self.assertEqual(c_user, u)

    def test_search_user(self):
        expected = {
            'type': 'user',
            'avatar': None,
            'name': 'Numpy',
            'id': '12345'
        }

        u = User(name=expected['name'], google_id=expected['id'], email='foo@gmail.com')
        u.save()

        resp = self.app.get('/users.json?query=Num')
        data = json.loads(resp.data)
        self.assertEqual(data['users'], [expected])
