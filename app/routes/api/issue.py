from app import app
from app.routes.oauth import requires_login
from app.models.user import current_user
from flask import render_template, redirect, request, url_for, jsonify, flash
from flask.views import MethodView
from app.models import Issue, Comment, Event, Project
from . import register_api
from flask.ext.mongoengine.wtf import model_form

issue_form = model_form(Issue, exclude=['created_at', 'author', 'comments', 'project', 'open', 'github_id'])

class IssueAPI(MethodView):

    def get_context(self, slug=None, id=None):
        issue = Issue.objects.get_or_404(id=id) if id else None
        project = Project.objects.get_or_404(slug=slug) if slug else None
        form = issue_form(request.form)

        context = {
                'issue': issue,
                'project': project,
                'form': form
        }
        return context

    @requires_login
    def get(self, slug, id):
        ctx = self.get_context(slug=slug, id=id)
        project = ctx['project']

        # List view
        if id is None:
            issues = Issue.objects(project=project)
            return render_template('issue/list.html', issues=issues, project=project)
        # Detail view
        else:
            comment_form = model_form(Comment, exclude=['created_at', 'author'])
            form = comment_form(request.form)

            issue = ctx['issue']
            issue.sync()
            all_events = issue.all_events()

            return render_template('issue/detail.html', issue=issue, events=all_events, form=form, current_user=current_user(), project=project)

    @requires_login
    def post(self, slug):
        ctx = self.get_context(slug=slug)
        form = ctx['form']

        if form.validate():
            project = ctx['project']

            issue = Issue()
            issue.project = project
            _process_issue(issue, form, request)

            project.issues.append(issue)
            project.save()
            flash('We have finished assembling your issue.')
            return redirect(url_for('issue_api', slug=slug, id=issue.id, _method='GET'))

        flash('You have forgotten something. Without your guidance, we are lost.')
        return render_template('issue/new.html', form=form)

    @requires_login
    def put(self, slug, id):
        # CURRENTLY UNUSED.
        ctx = self.get_context(id=id)
        issue = ctx['issue']
        form = ctx['form']

        if form.validate():
            _process_issue(issue, form, request.form)
            return redirect(url_for('issue_api', slug=slug, id=issue.id))

        return redirect(url_for('issue_api', slug=slug, id=issue.id))

    @requires_login
    def delete(self, slug, id):
        ctx = self.get_context(id=id)
        issue = ctx['issue']
        issue.delete()
        return jsonify({'success':True})

register_api(IssueAPI, 'issue_api', '/<string:slug>/issues/', id='id', id_type='string')

@app.route('/<string:slug>/issues/new')
@requires_login
def new_issue(slug):
    project = Project.objects.get_or_404(slug=slug)
    return render_template('issue/new.html', form=issue_form(request.form), project=project)

# Not "proper" but lack of HTTP method support in browsers sucks.
# Emulate PUT by accepting POST at this endpoint.
@app.route('/<string:slug>/issues/<string:id>/edit', methods=['GET', 'POST'])
@requires_login
def edit_issue(slug, id):
    issue = Issue.objects.get_or_404(id=id)
    if request.method == 'GET':
        form = issue_form(request.form, obj=issue)
        return render_template('issue/edit.html', form=form, issue=issue, project=issue.project)
    else:
        form = issue_form(request.form)
        if form.validate():
            _process_issue(issue, form, request)
            flash('We have updated your issue.')
            return redirect(url_for('issue_api', slug=slug, id=id, _method='GET'))

        # To preserve labels. I assume there's a better way
        # but WTForms has been a fucking nightmare about this
        # since it won't let me override form.labels.data.
        labels = [label.strip() for label in request.form.get('labels').split(',') if label]
        issue.labels = labels

        flash('Something is wrong -- We need your guidance!')
        return render_template('issue/edit.html', form=form, issue=issue, project=issue.project)

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


# Convenience method for updating an issue.
def _process_issue(issue, form, request):
    try:
        form.populate_obj(issue)
        issue.process(request.form)
    except KeyError as e:
        flash('We weren\'t able to link with GitHub. Try authenticating.')
        return redirect(url_for('github_info'))
