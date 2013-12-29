from app import app
from flask import redirect, url_for, flash, session
from flask_oauth import OAuth
from app.models import User
from app.routes.auth import requires_auth
import urllib2, json
from functools import wraps

# Setup OAuth(2).
oauth = OAuth()
google = oauth.remote_app('google',
        base_url='https://www.google.com/accounts/',
        authorize_url='https://accounts.google.com/o/oauth2/auth',
        request_token_url=None,
        request_token_params={
            'scope': 'https://www.googleapis.com/auth/drive https://www.googleapis.com/auth/userinfo.profile',
            'response_type': 'code'
        },
        access_token_url='https://accounts.google.com/o/oauth2/token',
        access_token_method='POST',
        access_token_params={
            'grant_type': 'authorization_code'
        },
        consumer_key=app.config['GOOGLE_CLIENT_ID'],
        consumer_secret=app.config['GOOGLE_CLIENT_SECRET']
)

@app.route('/login')
def login():
    """
    Passes client to Google to authenticate
    with their Google account.
    """
    callback = url_for('authorized', _external=True)
    return google.authorize(callback=callback)

@app.route('/logout')
def logout():
    """
    Destroy Google access token.
    """
    session.pop('access_token', None)
    session.pop('user_id', None)
    return redirect(url_for('index'))

@google.tokengetter
def get_access_token():
    """
    Required by flask-oauth.

    Returns:
        | (token, '') -- normally returns (token, secret), but Google
        only has token.
    """
    return session.get('access_token')

# After authentication.
@app.route(app.config['GOOGLE_REDIRECT_URI'])
@google.authorized_handler
def authorized(resp):
    """
    Post-authentication redirect route.
    Adds the access token to the session.

    Args:
        | resp (Response) -- response received from Google APIs.
    """

    # If no response,
    # i.e. authorization failed.
    if resp is None:
        flash(u'Whoops, you denied us access to your Google account')
        return redirect(url_for('login'))

    # Store access token in session.
    access_token = resp['access_token']
    session['access_token'] = access_token, ''

    # Redirect
    return redirect(url_for('index'))


def current_user():
    """
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
        response = _api_request('https://www.googleapis.com/oauth2/v1/userinfo?alt=json')
        g_user = json.loads(response)
        user, created = User.objects.get_or_create(google_id=g_user['id'])
        user.name = g_user['name']
        user.picture = g_user['picture']
        user.save()
        session['user_id'] = g_user['id']
    else:
        user = User.objects.get(google_id=session['user_id'])
    return user

def requires_oauth(f):
    """
    Decorator for routes requiring OAuth-entication.
    """
    @wraps(f)
    @requires_auth
    def decorated(*args, **kwargs):
        if session.get('access_token') is None:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def _api_request(url):
    """
    Makes a request to an API endpoint,
    redirects to the login screen if it fails.
    """

    try:
        headers = _build_auth_headers()
    except Exception as e:
        return redirect(url_for('login'))

    req = urllib2.Request(url, None, headers)

    try:
        response = _get_response(req)
    except Exception as e:
        return redirect(url_for('login'))

    return response

def _get_response(req):
    """
    Attempts to get a response
    for a given request.

    If there is an issue with getting the response,
    it is likely an authentication error.

    Args:
        | req (Request) -- urllib2 Request to send.

    Returns:
        | Response if one is received.
        | None if no response is received.
    """
    try:
        res = urllib2.urlopen(req)
        response = res.read()
        return response
    except urllib2.URLError as e:
        print('error %s' % e.code)
        if e.code == 401 or e.code == 403:
            # Unauthorized; bad token.
            session.pop('access_token', None)
        raise Exception('Authentication Error')


def _build_auth_headers(use_json=False):
    """
    Builds authentication headers to
    send as part of a request.

    Raises an exception if the user is
    not authenticated.
    """
    access_token = session.get('access_token')
    if access_token is None:
        raise Exception('Authentication Error')
    access_token = access_token[0]
    if use_json:
        headers = {'Content-Type': 'application/json; charset=UTF-8', 'Authorization': 'OAuth ' + access_token}
    else:
        headers = {'Authorization': 'OAuth ' + access_token}
    return headers
