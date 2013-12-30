from app import app
from flask import redirect, url_for, flash, session, request
from rauth.service import OAuth2Service
import json

google = OAuth2Service(
    name='google',
    base_url='https://www.google.com/accounts/',
    authorize_url='https://accounts.google.com/o/oauth2/auth',
    access_token_url='https://accounts.google.com/o/oauth2/token',
    client_id=app.config['GOOGLE_CLIENT_ID'],
    client_secret=app.config['GOOGLE_CLIENT_SECRET']
)

@app.route('/login')
def google_login():
    """
    Passes client to Google to authenticate
    with their Google account.
    """
    redirect_uri = url_for('google_authorized', _external=True)
    scope = 'https://www.googleapis.com/auth/drive https://www.googleapis.com/auth/userinfo.profile'
    response_type = 'code'
    return redirect(google.get_authorize_url(redirect_uri=redirect_uri, scope=scope, response_type=response_type))

# After authentication.
@app.route(app.config['GOOGLE_REDIRECT_URI'])
def google_authorized():
    """
    Post-authentication redirect route.
    Adds access token to the session.
    """

    if not 'code' in request.args:
        flash(u'Whoops, you denied us access to your Google account')
        return redirect(url_for('google_login'))

    redirect_uri = url_for('google_authorized', _external=True)
    data = dict(code=request.args['code'], grant_type='authorization_code', redirect_uri=redirect_uri)
    session_ = google.get_auth_session(data=data, decoder=json.loads)

    # Store access token in session.
    session['google_access_token'] = session_.access_token, ''

    # Redirect
    return redirect('/')
