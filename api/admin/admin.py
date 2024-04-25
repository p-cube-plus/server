from flask import Blueprint
from flask_restx import Api
from api.admin.accounting.accounting import accounting
from api.admin.notification.notification import notification
from api.admin.attendance.attendance import attendance
from api.admin.role.role import role

admin = Blueprint('admin', __name__, url_prefix='/admin')

authorizations = {
    'apiKey': {
        'type': 'apiKey',
        'in': 'header',
        'name': 'Authorization'
    }
}
api = Api(admin, authorizations=authorizations)

api.add_namespace(accounting, '/accounting')
api.add_namespace(notification, '/notification')
api.add_namespace(attendance, '/attendance')
api.add_namespace(role, '/role')