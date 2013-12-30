from app import app
from flask import redirect, url_for, flash, session
from . import oauth

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
def google_login():
    """
    Passes client to Google to authenticate
    with their Google account.
    """
    callback = url_for('google_authorized', _external=True)
    return google.authorize(callback=callback)

@google.tokengetter
def get_access_token():
    """
    Required by flask-oauth.

    Returns:
        | (token, '') -- normally returns (token, secret), but Google
        only has token.
    """
    return session.get('google_access_token')

# After authentication.
@app.route(app.config['GOOGLE_REDIRECT_URI'])
@google.authorized_handler
def google_authorized(resp):
    """
    Post-authentication redirect route.
    Adds access token to the session.
    """

    # No response = authorization failed.
    if resp is None:
        flash(u'Whoops, you denied us access to your Google account')
        return redirect(url_for('google_login'))

    # Store access token in session.
    access_token = resp['access_token']
    session['google_access_token'] = access_token, ''

    # Redirect
    return redirect('/')
