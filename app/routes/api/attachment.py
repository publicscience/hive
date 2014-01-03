from app import app
from app.routes.oauth import requires_login
from flask import redirect, request, jsonify
from flask.views import MethodView
from app.models import Attachment

class AttachmentAPI(MethodView):

    @requires_login
    def delete(self, slug, id):
        attachment = Attachment.objects(id=id).first()
        attachment.delete()
        return jsonify({'success':True})

view_func = AttachmentAPI.as_view('attachment_api')
app.add_url_rule('/p/<string:slug>/attachments/<string:id>', view_func=view_func, methods=['DELETE'])

