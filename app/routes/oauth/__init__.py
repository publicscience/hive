from app import app
from flask import redirect, url_for, session
from app.routes.auth import requires_auth
from functools import wraps

@app.route('/logout')
def logout():
    """
    Destroy access tokens/session data.
    """
    session.pop('google_creds', None)
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
        if session.get('google_creds') is None:
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

from . import google, github
