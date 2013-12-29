from app import app
from flask import render_template, redirect, request, url_for, jsonify, flash
from flask.views import MethodView
from flask.ext.mongoengine.wtf import model_form
from app.models import Issue, Comment, User, Event
from app.routes.oauth import current_user, requires_oauth


def register_api(view, endpoint, url, id='id', id_type='int'):
    """
    Covenience function for building APIs.
    """
    view_func = view.as_view(endpoint)
    app.add_url_rule(url, defaults={id: None}, view_func=view_func, methods=['GET'])
    app.add_url_rule(url, view_func=view_func, methods=['POST'])
    app.add_url_rule('%s<%s:%s>/' % (url, id_type, id), view_func=view_func, methods=['GET', 'PUT', 'DELETE'])


class IssueAPI(MethodView):
    form = model_form(Issue, exclude=['created_at', 'author', 'comments', 'open'])
    comment_form = model_form(Comment, exclude=['created_at', 'author'])

    def get_context(self, id):
        issue = Issue.objects.get_or_404(id=id)
        form = self.form(request.form)

        context = {
                'issue': issue,
                'form': form
        }
        return context

    @requires_oauth
    def get(self, id):
        # List view
        if id is None:
            issues = Issue.objects.all()
            form = self.form(request.form)
            return render_template('issue/list.html', issues=issues, form=form)
        # Detail view
        else:
            comment_form = self.comment_form(request.form)
            context = self.get_context(id)
            issue = context['issue']

            all_events = issue.events + issue.comments
            all_events.sort(key=lambda i:i.created_at)
            return render_template('issue/detail.html', issue=issue, events=all_events, form=comment_form, current_user_id=current_user().id)

    def post(self):
        form = self.form(request.form)

        if form.validate():
            issue = Issue()
            form.populate_obj(issue)
            issue.labels = [label.strip() for label in request.form.get('labels').split(',')]
            issue.author = current_user()
            issue.save()
            return redirect(url_for('issue_api'))

        return redirect(url_for('issue_api'))

    def put(self, id):
        context = self.get_context(id)
        issue = context['issue']
        form = self.form(request.form)

        if form.validate():
            form.populate_obj(issue)
            issue.save()
            return redirect(url_for('issue_api', id=issue.id))

        return redirect(url_for('issue_api', id=issue.id))


    def delete(self, id):
        context = self.get_context(id)
        issue = context.get('issue')
        issue.delete()

        return jsonify({'success':True})

register_api(IssueAPI, 'issue_api', '/issues/', id='id', id_type='string')

@app.route('/issues/new')
@requires_oauth
def new_issue():
    form = model_form(Issue, exclude=['created_at', 'author', 'comments'])
    return render_template('issue/new.html', form=form(request.form))

@app.route('/issues/<string:id>/close', methods=['PUT'])
def close_issue(id):
    issue = Issue.objects.get_or_404(id=id)
    issue.open = False
    event = Event(type='closed', author=current_user())
    issue.events.append(event)
    issue.save()
    return jsonify({'success':True})

@app.route('/issues/<string:id>/open', methods=['PUT'])
def open_issue(id):
    issue = Issue.objects.get_or_404(id=id)
    issue.open = True
    event = Event(type='opened', author=current_user())
    issue.events.append(event)
    issue.save()
    return jsonify({'success':True})

@app.route('/issues/closed')
def closed_issues():
    issues = Issue.objects(open=False)
    return render_template('issue/list.html', issues=issues)

@app.route('/issues/open')
def open_issues():
    issues = Issue.objects(open=True)
    return render_template('issue/list.html', issues=issues)

@app.route('/issues/label/<string:label>')
def label_issues(label):
    issues = Issue.objects(labels=label)
    return render_template('issue/list.html', issues=issues)

@app.route('/users.json')
def find_users():
    query = request.args.get('query', '')
    users = []
    if query:
        users = [{'id': user.google_id, 'name': user.name, 'avatar': user.picture, 'type': 'user'} for user in User.objects(name__icontains=query)]

    return jsonify({'users': users})


class CommentAPI(MethodView):
    form = model_form(Comment, exclude=['created_at', 'id'])

    @requires_oauth
    def post(self, issue_id):
        form = self.form(request.form)
        issue = Issue.objects.get_or_404(id=issue_id)

        if form.validate():
            comment = Comment()
            form.populate_obj(comment)
            comment.author = current_user()
            issue.comments.append(comment)
            issue.save()
            return redirect(url_for('issue_api', id=issue.id, _method='GET'))

        return redirect(url_for('issue_api', id=issue.id, _method='GET'))

    @requires_oauth
    def delete(self, issue_id, id):
        Issue.objects(id=issue_id).update_one(pull__comments__id=id)
        return jsonify({'success':True})

view_func = CommentAPI.as_view('comment_api')
app.add_url_rule('/issues/<string:issue_id>/comments', view_func=view_func, methods=['POST'])
app.add_url_rule('/issues/<string:issue_id>/comments/<string:id>', view_func=view_func, methods=['PUT', 'DELETE'])
