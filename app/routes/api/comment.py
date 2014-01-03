from app import app
from app.routes.oauth import requires_login
from flask import redirect, request, url_for, jsonify, flash, render_template
from flask.views import MethodView
from app.models import Issue, Comment
from app.models.user import current_user
from flask.ext.mongoengine.wtf import model_form

class CommentAPI(MethodView):
    form = model_form(Comment, exclude=['created_at', 'updated_at', 'author', 'mentions', 'attachments', 'issue'])

    @requires_login
    def post(self, slug, issue_id):
        form = self.form(request.form)
        issue = Issue.objects.get_or_404(id=issue_id)

        if form.validate():
            comment = Comment(issue=issue)
            form.populate_obj(comment)

            try:
                comment.process(request.files)
            except KeyError as e:
                return redirect(url_for('github_login', _method='GET'))

            return redirect(url_for('issue_api', slug=slug, id=issue.id, _method='GET'))

        return redirect(url_for('issue_api', slug=slug, id=issue.id, _method='GET'))

    @requires_login
    def put(self, slug, issue_id, id):
        comment = Comment.objects(id=id).first()
        form = self.form(request.form)
        form.populate_obj(comment)
        comment.process(request.files)
        return jsonify({'success':True, 'html':render_template('comment.html', current_user=current_user(), comment=comment)})

    @requires_login
    def delete(self, slug, issue_id, id):
        Comment.objects(id=id).first().delete()
        return jsonify({'success':True})

view_func = CommentAPI.as_view('comment_api')
app.add_url_rule('/p/<string:slug>/issues/<string:issue_id>/comments', view_func=view_func, methods=['POST'])
app.add_url_rule('/p/<string:slug>/issues/<string:issue_id>/comments/<string:id>', view_func=view_func, methods=['PUT', 'DELETE'])
