from app import app
from flask import redirect, url_for, flash, session
from . import oauth

github = oauth.remote_app('github',
        base_url='https://api.github.com/user',
        authorize_url='https://github.com/login/oauth/authorize',
        request_token_url=None,
        request_token_params={
            'scope': 'user'
        },
        access_token_url='https://github.com/login/oauth/access_token',
        access_token_method='POST',
        consumer_key=app.config['GITHUB_CLIENT_ID'],
        consumer_secret=app.config['GITHUB_CLIENT_SECRET']
)

@app.route('/github')
def github_login():
    """
    Authenticate with Github.
    """
    callback = url_for('github_authorized', _external=True)
    return github.authorize(callback=callback)

# After authentication.
@app.route(app.config['GITHUB_REDIRECT_URI'])
@github.authorized_handler
def github_authorized(resp):
    """
    Post-authentication redirect route.
    Adds access token to the session.
    """

    # No response = authorization failed.
    if resp is None:
        flash(u'Whoops, you denied us access to your Github account')
        return redirect(url_for('github_login'))

    # Store access token in session.
    access_token = resp['access_token']
    session['github_access_token'] = access_token, ''

    # Redirect
    return redirect('/')
