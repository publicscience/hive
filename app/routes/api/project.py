from app import app
from app.routes.oauth import requires_login
from flask import render_template, redirect, request, url_for, jsonify, flash
from flask.views import MethodView
from app.models import Issue, Comment, User, Event, Project
from app.models.user import current_user
from . import register_api
from flask.ext.mongoengine.wtf import model_form
from datetime import datetime

class ProjectAPI(MethodView):
    form = model_form(Project, exclude=['created_at', 'users', 'issues', 'slug', 'author'])

    def get_context(self, slug):
        project = Project.objects.get_or_404(slug=slug)
        form = self.form(request.form)

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
            context = self.get_context(slug)
            project = context['project']
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
        form = self.form(request.form)

        if form.validate():
            project = Project()
            form.populate_obj(project)
            project.author = current_user()
            project.users = User.objects.all() # for now, all users are on the projects
            project.save()
            return redirect(url_for('project_api'))

        return redirect(url_for('project_api'))

    @requires_login
    def put(self, slug):
        context = self.get_context(slug)
        project = context['project']
        form = self.form(request.form)

        if form.validate():
            form.populate_obj(project)
            project.save()
            return redirect(url_for('project_api', slug=project.slug))

        return redirect(url_for('project_api', slug=project.slug))

    @requires_login
    def delete(self, slug):
        context = self.get_context(slug)
        project = context.get('project')
        project.delete()

        return jsonify({'success':True})

register_api(ProjectAPI, 'project_api', '/', id='slug', id_type='string')


@app.route('/new')
@requires_login
def new_project():
    form = model_form(Project, exclude=['created_at', 'users', 'issues', 'slug', 'author'])
    return render_template('project/new.html', form=form(request.form))
