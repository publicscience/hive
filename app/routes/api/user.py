from app import app
from flask import request, jsonify
from app.models import User

@app.route('/users.json')
def find_users():
    query = request.args.get('query', '')
    users = []
    if query:
        users = [{'id': user.google_id, 'name': user.name, 'avatar': user.picture, 'type': 'user'} for user in User.objects(name__icontains=query)]

    return jsonify({'users': users})
