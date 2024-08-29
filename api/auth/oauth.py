import configparser
import requests
import hashlib
import re
import uuid
from flask import Flask, request, session, current_app
from flask_restx import Resource, Namespace
from flask_jwt_extended import create_access_token, create_refresh_token
from database.database import Database
import random, sms
from utils.dto import OAuthDTO
from utils.enum_tool import NotificationEnum
from utils import fcm

config = configparser.ConfigParser()
config.read('config/config.ini', encoding='utf-8')

client_id = config['naver_login']['client_id']
client_secret = config['naver_login']['client_secret']

oauth = OAuthDTO.api

def generate_code():
    return str(random.randint(0, 999999)).zfill(6)

@oauth.route("/naver/login")
class NaverLogin(Resource):
    def get(self):
        naver_token = request.args.get('refresh_token')
        params = {
            'client_id': client_id,
            'client_secret': client_secret,
            'refresh_token': naver_token,
            'grant_type': 'refresh_token',
            'service_provider': 'NAVER'
        }
        naver_request = requests.post("https://nid.naver.com/oauth2.0/token", params=params)
        naver_data = naver_request.json()
        if 'access_token' not in naver_data:
            return {'message': '네이버 로그인에 실패했어요 :('}, 401
        
        naver_identifier = request.args.get('identifier')
        if not naver_identifier:
            return {'message': '네이버 로그인에 실패했어요 :('}, 401
        name = request.args.get('name')
        if not name:
            return {'message': '네이버 로그인에 실패했어요 :('}, 401
        phone_number = request.args.get('phone_number')
        if not phone_number:
            return {'message': '네이버 로그인에 실패했어요 :('}, 401
        phone_number = re.sub(r'\D', '', phone_number)
        phone_number = re.sub(r'(\d{3})(\d{4})(\d{4})', r'\1-\2-\3', phone_number)

        user_id = hashlib.sha256(name.encode('utf-8') + phone_number.encode('utf-8')).hexdigest()
        
        try:
            database = Database()
            sql = "SELECT is_signed FROM users WHERE id = %s;"
            values = (user_id,)
            is_signed = database.execute_one(sql, values)
            if is_signed is None:
                return {'message': '판도라큐브 회원 정보가 없어요 :('}, 401
            
            access_token = create_access_token(identity=user_id)
            refresh_token = create_refresh_token(identity=user_id)
            token = {'access_token': access_token, 'refresh_token': refresh_token}
            
            is_signed = is_signed['is_signed']
            if is_signed:
                return token, 200
            
            sql = "INSERT INTO identifier (identifier, user_id, is_signed) VALUES (%s, %s, %s);"
            values = (naver_identifier, user_id, 0)
            database.execute(sql, values)
            sql = "UPDATE users SET is_signed = 1 WHERE id = %s;"
            values = (user_id,)
            database.execute(sql, values)
            database.commit()
        except Exception as e:
            return {'message': '서버에 오류가 발생했어요 :(\n지속적으로 발생하면 문의주세요!', 'error': str(e)}, 400
        finally:
            database.close()
        
        return token, 200

@oauth.route("/naver/leave")
class NaverLoginLeave(Resource):
    def post(self):
        headers = request.headers
        access_token = headers.get('Authorization')
        if not access_token:
            return {'message': 'Unauthorized'}, 401

        params = {
            'client_id': client_id,
            'client_secret': client_secret,
            'access_token': access_token,
            'grant_type': 'delete',
            'service_provider': 'NAVER'
        }

        leave_request = requests.post("https://nid.naver.com/oauth2.0/token", params=params)
        leave_data = leave_request.json()

        return leave_data

@oauth.route('/code/request')
class OauthCodeRequestAPI(Resource):
    @oauth.expect(OAuthDTO.model_oauth_code_request, validate=True)
    @oauth.response(200, 'OK', OAuthDTO.response_oauth_sms_validation)
    def post(self):
        # 전화번호 얻어오기
        code_request = request.get_json()
        phone_number = code_request['phone_number']

        # 인증번호 생성
        code = generate_code()

        # SMS 메시지 발송
        message = f"[PCube+]\n인증번호는 {code}입니다."
        result = sms.send_msg(phone_number.replace("-", ""), message)

        if result.status_code == 200: # SMS 메시지 발송 성공 시
            # 식별자 생성
            identifier = str(uuid.uuid4())

            # (식별자, 인증번호) 정보를 memcached에 5분간 저장
            mc = current_app.extensions['memcache_client']
            mc.set(identifier, code, 60 * 5)

            return {'is_success': True, 'identifier': identifier}, 200
        else:
            return {'is_success': False, 'identifier': None}, 200

@oauth.route('/code/confirm')
class OauthCodeConfirmAPI(Resource):
    @oauth.expect(OAuthDTO.model_oauth_code_confirm, validate=True)
    @oauth.response(200, 'OK', OAuthDTO.response_oauth_code_result)
    def post(self):
        # 식별자, 인증번호 얻어오기
        code_confirm = request.get_json()
        identifier = code_confirm['identifier']
        input_code = code_confirm['code']

        # 저장된 인증번호 불러오기
        mc = current_app.extensions['memcache_client']
        stored_code = mc.get(identifier)

        # 인증번호 비교
        if stored_code and stored_code == input_code:
            mc.delete(identifier)
            return {'is_verified': True}, 200
        else:
            return {'is_verified': False}, 200
        
@oauth.route('/user')
class OauthUserCheckAPI(Resource):
    @oauth.expect(OAuthDTO.model_oauth_user, validate=True)
    @oauth.response(200, 'OK', OAuthDTO.response_oauth_user)
    @oauth.response(400, 'Bad Request', OAuthDTO.response_oauth_message)
    def post(self):
        user_info = request.get_json()
        user_id = hashlib.sha256(str(user_info['name'] + user_info['phone_number']).encode('utf-8')).hexdigest()

        try:
            database = Database()
            sql = "SELECT id, part_index FROM users WHERE id = %s;"
            values = (user_id,)
            user = database.execute_one(sql, values)

            if user:
                sql = "UPDATE users SET fcm_token = %s WHERE id = %s;"
                values = (user_info['fcm_token'], user_id)
                database.execute(sql, values)
                database.commit()

                fcm.subscribe([user_info['fcm_token']], NotificationEnum.FcmTopic(user['part_index']))
                fcm.subscribe([user_info['fcm_token']], 'global')
        except Exception as e:
            return {'message': '서버에 오류가 발생했어요 :(\n지속적으로 발생하면 문의주세요!', 'error': str(e)}, 400
        finally:
            database.close()

        access_token = create_access_token(identity=user_id) if user else None
        refresh_token = create_refresh_token(identity=user_id) if user else None

        return {'is_member': user is not None, 'access_token': access_token, 'refresh_token': refresh_token}, 200
