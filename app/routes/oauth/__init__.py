from app import app
from flask import redirect, url_for, session
from flask_oauth import OAuth, OAuthException
from app.routes.auth import requires_auth
from app.models import User
from functools import wraps

# Setup OAuth(2).
oauth = OAuth()

from . import google, github

@app.route('/logout')
def logout():
    """
    Destroy access tokens/session data.
    """
    session.pop('google_access_token', None)
    session.pop('user_id', None)
    session.pop('github_access_token', None)
    return redirect('/')

def requires_login(f):
    """
    Decorator for routes requiring Google OAuth-entication.
    """
    @wraps(f)
    @requires_auth
    def decorated(*args, **kwargs):
        if session.get('google_access_token') is None:
            return redirect(url_for('google_login'))
        return f(*args, **kwargs)
    return decorated

def requires_github(f):
    @wraps(f)
    @requires_login
    def decorated(*args, **kwargs):
        if session.get('github_access_token') is None:
            return redirect(url_for('github_login'))
        return f(*args, **kwargs)
    return decorated

def current_user():
    """
    Return current session's user,
    or fetch user data from Google.

    Response looks like:
    {
     "id": "1111111111",
     "name": "Francis Tseng",
     "given_name": "Francis",
     "family_name": "Tseng",
     "link": "https://plus.google.com/...",
     "picture": "https://lh6.googleusercontent.com/...",
     "gender": "male",
     "locale": "en"
    }
    """

    if not session.get('user_id', False):
        # Get and store user info in session.
        headers = {'Authorization': 'OAuth '+session.get('google_access_token')[0]}
        response = google.google.get('https://www.googleapis.com/oauth2/v1/userinfo?', headers=headers)
        g_user = response.data
        user, created = User.objects.get_or_create(google_id=g_user['id'])
        user.name = g_user['name']
        user.picture = g_user['picture']
        user.save()
        session['user_id'] = g_user['id']
    else:
        user = User.objects.get(google_id=session['user_id'])
    return user
