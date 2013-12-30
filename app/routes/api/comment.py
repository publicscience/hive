from app import app
from app.routes.oauth import requires_login, github
from app.models.user import current_user
from flask import redirect, request, url_for, jsonify, flash
from flask.views import MethodView
from app.models import Issue, Comment
from flask.ext.mongoengine.wtf import model_form
import json

class CommentAPI(MethodView):
    form = model_form(Comment, exclude=['created_at', 'id'])

    @requires_login
    def post(self, slug, issue_id):
        form = self.form(request.form)
        issue = Issue.objects.get_or_404(id=issue_id)

        if form.validate():
            comment = Comment()
            form.populate_obj(comment)
            comment.author = current_user()
            if issue.github_id:
                url = '/repos/' + issue.project.repo + '/issues/' + str(issue.github_id) + '/comments'
                resp = github.api().post(url, data=json.dumps({'body':comment.body}))
                comment.github_id = resp.json()['id']

            issue.comments.append(comment)
            issue.save()
            return redirect(url_for('issue_api', slug=slug, id=issue.id, _method='GET'))

        return redirect(url_for('issue_api', slug=slug, id=issue.id, _method='GET'))

    @requires_login
    def delete(self, slug, issue_id, id):
        Issue.objects(id=issue_id).update_one(pull__comments__id=id)
        return jsonify({'success':True})

view_func = CommentAPI.as_view('comment_api')
app.add_url_rule('/<string:slug>/issues/<string:issue_id>/comments', view_func=view_func, methods=['POST'])
app.add_url_rule('/<string:slug>/issues/<string:issue_id>/comments/<string:id>', view_func=view_func, methods=['PUT', 'DELETE'])

