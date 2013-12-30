from app import app
from app.routes.oauth import current_user, requires_login
from flask import render_template, redirect, request, url_for, jsonify, flash
from flask.views import MethodView
from app.models import Issue, Comment, User, Event, Project
from . import register_api
from flask.ext.mongoengine.wtf import model_form

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
            return render_template('project/list.html', projects=projects, current_user_id=current_user().id)
        # Detail view
        else:
            context = self.get_context(slug)
            project = context['project']
            issues = Issue.objects(project=project)
            return render_template('issue/list.html', issues=issues, project=project)

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

    def put(self, slug):
        context = self.get_context(slug)
        project = context['project']
        form = self.form(request.form)

        if form.validate():
            form.populate_obj(project)
            project.save()
            return redirect(url_for('project_api', slug=project.slug))

        return redirect(url_for('project_api', slug=project.slug))


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
