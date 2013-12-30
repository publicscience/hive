from app import app
from app.routes.oauth import requires_login
from app.models.user import current_user
from flask import render_template, redirect, request, url_for, jsonify, flash
from flask.views import MethodView
from app.models import Issue, Comment, Event, Project
from . import register_api
from flask.ext.mongoengine.wtf import model_form

class IssueAPI(MethodView):
    form = model_form(Issue, exclude=['created_at', 'author', 'comments', 'open', 'project', 'github_id'])
    comment_form = model_form(Comment, exclude=['created_at', 'author'])

    def get_context(self, id):
        issue = Issue.objects.get_or_404(id=id)
        form = self.form(request.form)

        context = {
                'issue': issue,
                'form': form
        }
        return context

    @requires_login
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
            issue.sync()

            all_events = issue.all_events()
            return render_template('issue/detail.html', issue=issue, events=all_events, form=comment_form, current_user=current_user(), project=project)

    @requires_login
    def post(self, slug):
        form = self.form(request.form)

        if form.validate():
            project = Project.objects.get_or_404(slug=slug)
            issue = Issue()
            form.populate_obj(issue)
            issue.project = project
            issue.process(request.form)
            project.issues.append(issue)
            project.save()
            return redirect(url_for('issue_api', slug=slug))

        return redirect(url_for('issue_api', slug=slug))

    @requires_login
    def put(self, slug, id):
        context = self.get_context(id)
        issue = context['issue']
        form = self.form(request.form)

        if form.validate():
            form.populate_obj(issue)
            issue.save()
            return redirect(url_for('issue_api', slug=slug, id=issue.id))

        return redirect(url_for('issue_api', slug=slug, id=issue.id))


    @requires_login
    def delete(self, slug, id):
        context = self.get_context(id)
        issue = context.get('issue')
        issue.delete()
        return jsonify({'success':True})

register_api(IssueAPI, 'issue_api', '/<string:slug>/issues/', id='id', id_type='string')

@app.route('/<string:slug>/issues/new')
@requires_login
def new_issue(slug):
    form = model_form(Issue, exclude=['created_at', 'author', 'comments', 'project', 'open', 'github_id'])
    return render_template('issue/new.html', form=form(request.form))

# Not "proper" but lack of HTTP method support in browsers sucks.
@app.route('/<string:slug>/issues/<string:id>/edit', methods=['GET', 'POST'])
@requires_login
def edit_issue(slug, id):
    issue = Issue.objects.get_or_404(id=id)
    form = model_form(Issue, exclude=['created_at', 'author', 'comments', 'project', 'open', 'github_id'])
    if request.method == 'GET':
        return render_template('issue/edit.html', form=form(request.form, obj=issue), issue=issue, project=issue.project)
    else:
        form_ = form(request.form)
        if form_.validate():
            form_.populate_obj(issue)
            issue.process(request.form)
        return redirect(url_for('edit_issue', slug=slug, id=id, _method='GET'))

@app.route('/issues/<string:id>/close', methods=['PUT'])
@requires_login
def close_issue(id):
    issue = Issue.objects.get_or_404(id=id)
    issue.close()
    return jsonify({'success':True})

@app.route('/issues/<string:id>/open', methods=['PUT'])
@requires_login
def open_issue(id):
    issue = Issue.objects.get_or_404(id=id)
    issue.reopen()
    return jsonify({'success':True})

@app.route('/<string:slug>/closed')
@requires_login
def closed_issues(slug):
    project = Project.objects.get_or_404(slug=slug)
    issues = Issue.objects(open=False, project=project)
    return render_template('issue/list.html', issues=issues, project=project)

@app.route('/<string:slug>/open')
@requires_login
def open_issues(slug):
    project = Project.objects.get_or_404(slug=slug)
    issues = Issue.objects(open=True, project=project)
    return render_template('issue/list.html', issues=issues, project=project)

@app.route('/<string:slug>/label/<string:label>')
@requires_login
def label_issues(slug, label):
    project = Project.objects.get_or_404(slug=slug)
    issues = Issue.objects(labels=label, project=project)
    return render_template('issue/list.html', issues=issues, project=project)


