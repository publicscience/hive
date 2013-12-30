from app import app
from app.routes.oauth import current_user, requires_login, OAuthException
from app.routes.oauth.github import github
from flask import render_template, redirect, request, url_for, jsonify, flash
from flask.views import MethodView
from app.models import Issue, Comment, User, Event, Project
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
            return render_template('project/list.html', projects=projects, current_user_id=current_user().id)
        # Detail view
        else:
            context = self.get_context(slug)
            project = context['project']
            issues = Issue.objects(project=project)
            if project.repo:
                try:
                    gis = github.get('/repos/'+project.repo+'/issues').data
                    for gi in gis:
                        issue, created = Issue.objects.get_or_create(github_id=gi['number'], project=project)
                        if created:
                            project.issues.append(issue)

                        open = True if gi['state'] == 'open' else False
                        labels = [label['name'] for label in gi['labels']]
                        author = User.objects(github_id=gi['user']['id']).first()
                        default_author = User.objects(github_id=0).first()
                        if not author:
                            author = default_author

                        # Get comments, and update them all.
                        gcs = github.get('/repos/'+project.repo+'/issues/'+str(gi['number'])+'/comments').data
                        for gc in gcs:
                            comment = next((c for c in issue.comments if c.github_id==gc['id']), 0)
                            if comment:
                                issue.comments.remove(comment)
                            comment = Comment()
                            c_author = User.objects(github_id=gc['user']['id']).first()
                            if not c_author:
                                c_author = default_author
                            c_updates = {
                                    'github_id': gc['id'],
                                    'created_at': datetime.strptime(gc['created_at'], '%Y-%m-%dT%H:%M:%SZ'),
                                    'body': gc['body'],
                                    'author': c_author
                            }
                            for k,v in c_updates.iteritems():
                                setattr(comment, k, v)
                            issue.comments.append(comment)

                        updates = {
                            'created_at': datetime.strptime(gi['created_at'], '%Y-%m-%dT%H:%M:%SZ'),
                            'title': gi['title'],
                            'body': gi['body'],
                            'open': open,
                            'labels': labels,
                            'author': author
                        }
                        for k,v in updates.iteritems():
                            setattr(issue, k, v)
                        issue.save()
                except OAuthException as e:
                    if current_user().github_id:
                        return redirect(url_for('github_login'))
                    else:
                        return redirect(url_for('github_info'))

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
