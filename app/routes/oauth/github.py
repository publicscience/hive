from app import app
from flask import redirect, url_for, flash, session, render_template, request
from rauth.service import OAuth2Service

github = OAuth2Service(
    name='github',
    base_url='https://api.github.com/user',
    authorize_url='https://github.com/login/oauth/authorize',
    access_token_url='https://github.com/login/oauth/access_token',
    client_id=app.config['GITHUB_CLIENT_ID'],
    client_secret=app.config['GITHUB_CLIENT_SECRET']
)

@app.route('/github_login')
def github_login():
    """
    Authenticate with Github.
    """
    redirect_uri = url_for('github_authorized', _external=True)
    return redirect(github.get_authorize_url(redirect_uri=redirect_uri, scope='user,repo'))

@app.route('/github')
def github_info():
    """
    Provide some info about linking
    a Github account.
    """
    return render_template('github.html')

# After authentication.
@app.route(app.config['GITHUB_REDIRECT_URI'])
def github_authorized():
    """
    Post-authentication redirect route.
    Adds access token to the session.
    """

    if not 'code' in request.args:
        flash(u'Whoops, you denied us access to your Github account')
        return redirect(url_for('github_login'))

    redirect_uri = url_for('github_authorized', _external=True)
    data = dict(code=request.args['code'], redirect_uri=redirect_uri, scope='user,repo')
    session_ = github.get_auth_session(data=data)

    # Store access token in session.
    session['github_access_token'] = session_.access_token

    from app.models.user import current_user
    current_user = current_user()
    current_user.github_id = session_.get('/user').json()['id']
    current_user.github_access = session_.access_token
    current_user.save()

    # Redirect
    return redirect('/')

def api(token=None):
    if token is None:
        token = session['github_access_token']
    return github.get_session(token=token)
