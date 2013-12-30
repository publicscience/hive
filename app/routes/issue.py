from app import app
from app.routes.oauth import current_user, requires_oauth
from flask import render_template, redirect, request, url_for, jsonify, flash
from flask.views import MethodView
from app.models import Issue, Comment, Event, Project
from app.routes.api import register_api
from flask.ext.mongoengine.wtf import model_form

class IssueAPI(MethodView):
    form = model_form(Issue, exclude=['created_at', 'author', 'comments', 'open', 'project'])
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
    def get(self, slug, id):
        project = Project.objects.get_or_404(slug=slug)

        # List view
        if id is None:
            issues = Issue.objects(project=project)
            return render_template('issue/list.html', issues=issues, project=project)
        # Detail view
        else:
            comment_form = self.comment_form(request.form)
            context = self.get_context(id)
            issue = context['issue']

            all_events = issue.events + issue.comments
            all_events.sort(key=lambda i:i.created_at)
            return render_template('issue/detail.html', issue=issue, events=all_events, form=comment_form, current_user_id=current_user().id, project=project)

    def post(self, slug):
        form = self.form(request.form)

        if form.validate():
            project = Project.objects.get_or_404(slug=slug)
            issue = Issue()
            form.populate_obj(issue)
            issue.labels = [label.strip() for label in request.form.get('labels').split(',')]
            issue.author = current_user()
            issue.project = project
            issue.save()
            return redirect(url_for('issue_api', slug=slug))

        return redirect(url_for('issue_api', slug=slug))

    def put(self, slug, id):
        context = self.get_context(id)
        issue = context['issue']
        form = self.form(request.form)

        if form.validate():
            form.populate_obj(issue)
            issue.save()
            return redirect(url_for('issue_api', slug=slug, id=issue.id))

        return redirect(url_for('issue_api', slug=slug, id=issue.id))


    def delete(self, slug, id):
        context = self.get_context(id)
        issue = context.get('issue')
        issue.delete()

        return jsonify({'success':True})

register_api(IssueAPI, 'issue_api', '/<string:slug>/issues/', id='id', id_type='string')

@app.route('/<string:slug>/issues/new')
@requires_oauth
def new_issue(slug):
    form = model_form(Issue, exclude=['created_at', 'author', 'comments', 'project'])
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

@app.route('/<string:slug>/issues/closed')
def closed_issues(slug):
    #issues = Issue.objects(open=False)
    project = Project.objects.get_or_404(slug=slug)
    issues = Issue.objects(open=False, project=project)
    return render_template('issue/list.html', issues=issues, project=project)

@app.route('/<string:slug>/issues/open')
def open_issues(slug):
    #issues = Issue.objects(open=True)
    project = Project.objects.get_or_404(slug=slug)
    issues = Issue.objects(open=True, project=project)
    return render_template('issue/list.html', issues=issues, project=project)

@app.route('/<string:slug>/issues/label/<string:label>')
def label_issues(slug, label):
    project = Project.objects.get_or_404(slug=slug)
    #issues = [issue for issue in project.issues if label in issue.labels]
    issues = Issue.objects(labels=label, project=project)
    return render_template('issue/list.html', issues=issues, project=project)


