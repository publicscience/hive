from app import app
from app.routes.oauth import requires_login, github
from app.models.user import current_user
from flask import redirect, request, url_for, jsonify, flash
from flask.views import MethodView
from app.models import Issue, Comment
from flask.ext.mongoengine.wtf import model_form
import json, os
from werkzeug import secure_filename

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in app.config['ALLOWED_EXTENSIONS']

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
            comment.process()

            # Handle newly uploaded files.
            for k, file in request.files.iteritems():
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(filepath)
                    attachment = issue.project.upload_file(filepath)
                    comment.attachments.append(attachment)
                    attachment.parent = comment
                    attachment.save()

            if issue.linked():
                # Create comment on GitHub
                try:
                    url = '/repos/' + issue.project.repo + '/issues/' + str(issue.github_id) + '/comments'
                    resp = github.api().post(url, data=json.dumps({'body':comment.body}))
                    comment.github_id = resp.json()['id']
                except KeyError as e:
                    return redirect(url_for('github_login', _method='GET'))

            issue.parse_references(comment.body)

            issue.comments.append(comment)
            issue.save()
            return redirect(url_for('issue_api', slug=slug, id=issue.id, _method='GET'))

        return redirect(url_for('issue_api', slug=slug, id=issue.id, _method='GET'))

    @requires_login
    def delete(self, slug, issue_id, id):
        issue = Issue.objects(id=issue_id).first()
        issue.delete_comment(id)
        return jsonify({'success':True})

view_func = CommentAPI.as_view('comment_api')
app.add_url_rule('/p/<string:slug>/issues/<string:issue_id>/comments', view_func=view_func, methods=['POST'])
app.add_url_rule('/p/<string:slug>/issues/<string:issue_id>/comments/<string:id>', view_func=view_func, methods=['PUT', 'DELETE'])

