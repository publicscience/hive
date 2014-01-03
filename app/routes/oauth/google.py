from app import app
from flask import redirect, url_for, flash, session, request
from oauth2client.client import OAuth2WebServerFlow, Credentials
from apiclient.discovery import build
import json, httplib2

flow = OAuth2WebServerFlow(
    client_id=app.config['GOOGLE_CLIENT_ID'],
    client_secret=app.config['GOOGLE_CLIENT_SECRET'],
    scope='https://www.googleapis.com/auth/drive https://www.googleapis.com/auth/userinfo.profile https://www.googleapis.com/auth/userinfo.email'
)

@app.route('/login')
def google_login():
    """
    Passes client to Google to authenticate
    with their Google account.
    """
    flow.redirect_uri=url_for('google_authorized', _external=True)
    return redirect(flow.step1_get_authorize_url())

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

    credentials = flow.step2_exchange(request.args['code'])

    # Store access token in session.
    session['google_creds'] = credentials.to_json()

    from app.models.user import current_user
    user = current_user()
    user.google_creds = credentials.to_json()
    user.save()

    # Redirect
    return redirect('/')

def user_info(creds=None):
    if creds is None:
        creds = session['google_creds']
    creds = Credentials.new_from_json(creds)
    user_info_service = build('oauth2', 'v2', http=creds.authorize(httplib2.Http()))
    user_info = user_info_service.userinfo().get().execute()
    if user_info and user_info.get('id'):
        return user_info

def drive_api(creds=None):
    if creds is None:
        creds = session['google_creds']
    creds = Credentials.new_from_json(creds)
    return build('drive', 'v2', http=creds.authorize(httplib2.Http()))

def delete_file(file):
    pass

def create_document(name):
    pass

def delete_document(name):
    pass

