from app import app
from flask import render_template, redirect, request, url_for, jsonify, flash
from flask.views import MethodView
from app.models import Issue, Comment, User, Event, Project
from app.routes.oauth import current_user, requires_oauth

def register_api(view, endpoint, url, id='id', id_type='int'):
    """
    Covenience function for building APIs.
    """
    view_func = view.as_view(endpoint)
    app.add_url_rule(url, defaults={id: None}, view_func=view_func, methods=['GET'])
    app.add_url_rule(url, view_func=view_func, methods=['POST'])
    app.add_url_rule('%s<%s:%s>/' % (url, id_type, id), view_func=view_func, methods=['GET', 'PUT', 'DELETE'])


@app.route('/users.json')
def find_users():
    query = request.args.get('query', '')
    users = []
    if query:
        users = [{'id': user.google_id, 'name': user.name, 'avatar': user.picture, 'type': 'user'} for user in User.objects(name__icontains=query)]

    return jsonify({'users': users})
