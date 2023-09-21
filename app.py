from flask import Flask
from flask_restx import Api
from api.auth.auth import auth
from api.auth.oauth import oauth
from api.user.user import user
from api.product.product import product
from api.project.project import project
from api.seminar.seminar import seminar
from api.warning.warning import warning
from api.accounting.accounting import accounting
from api.home.home import home
from api.attendance.attendance import attendance
from api.admin.admin import admin
from api.feedback.feedback import feedback
from api.equipment.equipment import equipment
from flask_jwt_extended import JWTManager
import configparser
import datetime

config = configparser.ConfigParser()
config.read_file(open('config/config.ini'))

app = Flask(__name__)
authorizations = {
    'apiKey': {
        'type': 'apiKey',
        'in': 'header',
        'name': 'Authorization'
    }
}
api = Api(app, authorizations=authorizations)

jwt = JWTManager(app)
app.config['JWT_SECRET_KEY'] = config['JWT']['JWT_SECRET_KEY']
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = datetime.timedelta(minutes=int(config['JWT']['JWT_ACCESS_TOKEN_EXPIRES']))
app.config['JWT_REFRESH_TOKEN_EXPIRES'] = datetime.timedelta(days=int(config['JWT']['JWT_REFRESH_TOKEN_EXPIRES']))

api.add_namespace(auth, '/auth')
api.add_namespace(oauth, '/oauth')
api.add_namespace(user, '/user')
api.add_namespace(product, '/product')
api.add_namespace(project, '/project')
api.add_namespace(seminar, '/seminar')
api.add_namespace(warning, '/warning')
api.add_namespace(accounting, '/accounting')
api.add_namespace(home, '/home')
api.add_namespace(feedback,'/feedback')
api.add_namespace(equipment,'/equipment')

api.add_namespace(attendance, '/attendance')

app.register_blueprint(admin)


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
