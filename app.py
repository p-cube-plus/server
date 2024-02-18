from flask import Flask, session, request
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
from api.notification.notification import notification
from api.admin.admin import admin
from flask_jwt_extended import JWTManager
from utils import fcm
import memcache
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

app.secret_key = config['APP']['SECRET_KEY']

app.config['JWT_SECRET_KEY'] = config['JWT']['JWT_SECRET_KEY']
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = datetime.timedelta(minutes=int(config['JWT']['JWT_ACCESS_TOKEN_EXPIRES']))
app.config['JWT_REFRESH_TOKEN_EXPIRES'] = datetime.timedelta(days=int(config['JWT']['JWT_REFRESH_TOKEN_EXPIRES']))

mc = memcache.Client([config['memcached']['sockaddr']])

app.config['SESSION_TYPE'] = config['session']['session_type']
app.config['SESSION_PERMANENT'] = bool(config['session']['session_permanent'])
app.config['SESSION_USE_SIGNER'] = bool(config['session']['session_use_signer'])
app.config['SESSION_MEMCACHED'] = mc

app.permanent_session_lifetime = datetime.timedelta(minutes=int(config['session']['session_lifetime']))

@jwt.token_in_blocklist_loader
def check_if_token_is_revoked(jwt_header, jwt_payload):
    jti = jwt_payload["jti"]
    token = mc.get(jti)
    return token is not None

app.extensions['jwt_manager'] = jwt
app.extensions['memcache_client'] = mc

# request 마다 실행
@app.before_request
def before_request():
    # 유저 App 버전 얻기
    app_version = request.headers.get('app_version')

    # 헤더에 앱 버전 정보가 존재하지 않을 시
    if app_version is None:
        return {'message': "앱 버전 정보가 누락되었어요 :("}, 400
    
    # 서버 버전과 가용 여부 불러오기
    server_version = config['server']['version']
    available = bool(config['server']['available'])

    # 앱을 업데이트 해야 하는 경우
    if app_version != server_version:
        return {'message': "앱을 업데이트 해주세요. :)"}, 503
    
    # 서버를 이용할 수 없는 경우
    if not available:
        return {'message': "서버 점검 중이에요. :("}, 503
    
api.add_namespace(auth, '/auth')
api.add_namespace(oauth, '/oauth')
api.add_namespace(user, '/user')
api.add_namespace(product, '/product')
api.add_namespace(project, '/project')
api.add_namespace(seminar, '/seminar')
api.add_namespace(warning, '/warning')
api.add_namespace(accounting, '/accounting')
api.add_namespace(home, '/home')
api.add_namespace(attendance, '/attendance')
api.add_namespace(notification, '/notification')

app.register_blueprint(admin)

fcm.load_messages()

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
