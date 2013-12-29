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
    app.add_url_rule('%s<%s:%s>' % (url, id_type, id), view_func=view_func, methods=['GET', 'PUT', 'DELETE'])


class IssueAPI(MethodView):
    form = model_form(Issue, exclude=['created_at', 'author', 'comments'])

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
            context = self.get_context(id)
            return render_template('issue/detail.html', **context)

    def post(self):
        form = self.form(request.form)

        if form.validate():
            issue = Issue()
            form.populate_obj(issue)
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


class CommentAPI(MethodView):
    form = model_form(Comment, exclude=['created_at'])

    def get_context(self, id):
        comment = Comment.objects.get_or_404(id=id)
        form = self.form(request.form)

        context = {
                'comment': comment,
                'form': form
        }
        return context

    @requires_oauth
    def get(self, id):
        # List view
        if id is None:
            comments = Comment.objects.all()
            form = self.form(request.form)
            return render_template('comment/list.html', comments=comments, form=form)
        # Detail view
        else:
            context = self.get_context(id)
            return render_template('comment/detail.html', **context)

    def post(self):
        form = self.form(request.form)

        if form.validate():
            comment = Comment()
            form.populate_obj(comment)
            comment.save()
            return redirect(url_for('comment_api'))

        return redirect(url_for('comment_api'))

    def delete(self, id):
        context = self.get_context(id)
        comment = context.get('comment')
        comment.delete()

        return jsonify({'success':True})

register_api(CommentAPI, 'comment_api', '/comment/', id='id', id_type='string')
