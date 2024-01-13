from flask_restx import Resource
from flask_jwt_extended import (
    create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity, get_jwt
)
from flask_restx import Resource, Namespace
from flask import request, current_app
from utils.dto import AuthDTO
import time

auth = AuthDTO.api

@auth.route('/token/refresh')
@auth.response(401, 'Unauthorized')
class TokenAPI(Resource):
    def __init__(self, api=None, *args, **kwargs):
        super().__init__(api, args, kwargs)

    @jwt_required(refresh=True)
    @auth.doc(security='apiKey')
    def get(self):
        # refresh token으로 갱신
        user_id = get_jwt_identity()
        access_token = create_access_token(identity=user_id)
        refresh_token = create_refresh_token(identity=user_id)
        token = { 'access_token': access_token, 'refresh_token': refresh_token }
        return token, 200

@auth.route('/token/test')
class TokenTestAPI(Resource):
    @auth.expect(AuthDTO.query_auth_user_id, validate=True)
    def get(self):
        user_id = request.args['user_id']
        access_token = create_access_token(identity=user_id)
        refresh_token = create_refresh_token(identity=user_id)
        token = { 'access_token': access_token, 'refresh_token': refresh_token }
        return token, 200

@auth.route('/logout')
class LogoutAPI(Resource):
    # 로그아웃 기능
    @auth.response(200, 'OK', AuthDTO.response_logout_message)
    @auth.doc(security='apiKey')
    @jwt_required(verify_type=False)
    def delete(self):
        # jwt 얻어오기
        token = get_jwt()
        jti = token["jti"]
        ttype = token["type"]

        # memcache(jwt_blocklist)에 보관될 시간 계산
        token_expires = int(token['exp'] - time.time())

        # memcache(jwt_blocklist)에 보관 (= 토큰 파괴)
        mc = current_app.extensions['memcache_client']
        mc.set(jti, "", token_expires + 10) # 오차 고려하여 10초 추가 보관

        # 결과 메시지
        message = f"{ttype.capitalize()} 토큰이 성공적으로 제거되었어요 :)"

        return {'message': message}, 200