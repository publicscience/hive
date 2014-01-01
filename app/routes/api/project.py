from app import app
from app.routes.oauth import requires_login
from flask import render_template, redirect, request, url_for, jsonify, flash
from flask.views import MethodView
from app.models import Issue, Comment, User, Event, Project
from app.models.user import current_user
from . import register_api
from flask.ext.mongoengine.wtf import model_form
from datetime import datetime

project_form = model_form(Project, exclude=['created_at', 'users', 'issues', 'slug', 'author'])

class ProjectAPI(MethodView):
    def get_context(self, slug=None):
        project = Project.objects.get_or_404(slug=slug) if slug else None
        form = project_form(request.form)

        context = {
                'project': project,
                'form': form
        }
        return context

    @requires_login
    def get(self, slug):
        # List view
        if slug is None:
            projects = Project.objects.all()
            return render_template('project/list.html', projects=projects, current_user=current_user())
        # Detail view
        else:
            ctx = self.get_context(slug=slug)
            project = ctx['project']
            try:
                project.sync()
            except KeyError as e:
                if current_user().linked():
                    return redirect(url_for('github_login'))
                else:
                    return redirect(url_for('github_info'))
            issues = Issue.objects(project=project, open=True)

            return render_template('issue/list.html', issues=issues, project=project)

    @requires_login
    def post(self):
        ctx = self.get_context()
        form = ctx['form']

        if form.validate():
            project = Project()
            form.populate_obj(project)
            project.author = current_user()
            project.users = User.objects.all() # for now, all users are on the projects

            # Check that repo exists and that the user can access it.
            if project.repo:
                if not project.author.github_access:
                    return redirect(url_for('github_login'))
                if not project.ping_repo():
                    flash('The repo <b>%s</b> doesn\'t seem to exist!' % project.repo)
                    form.repo.errors = ['Can\'t access this repo.']
                    return render_template('project/new.html', form=form)

            project.save()
            flash('The <b>%s</b> project was successfully summoned.' % project.name)
            return redirect(url_for('project_api', slug=project.slug, _method='GET'))

        flash('You have forgotten something. Without your guidance, we are lost.')
        return render_template('project/new.html', form=form)

    @requires_login
    def put(self, slug):
        # CURRENTLY UNUSED.
        ctx = self.get_context(slug=slug)
        project = ctx['project']
        form = ctx['form']

        if form.validate():
            form.populate_obj(project)
            project.save()
            return redirect(url_for('project_api', slug=project.slug))

        return redirect(url_for('project_api', slug=project.slug))

    @requires_login
    def delete(self, slug):
        ctx = self.get_context(slug=slug)
        project = ctx['project']
        project.delete()

        return jsonify({'success':True})

register_api(ProjectAPI, 'project_api', '/p/', id='slug', id_type='string')


@app.route('/new')
@requires_login
def new_project():
    return render_template('project/new.html', form=project_form(request.form))
