import configparser
import requests
import hashlib
import re
from flask import Flask, request, session
from flask_restx import Resource, Namespace
from flask_jwt_extended import (
    create_access_token, create_refresh_token
)
from database.database import Database
import random, sms
from utils.dto import OAuthDTO

config = configparser.ConfigParser()
config.read('config/config.ini', encoding='utf-8')

client_id = config['naver_login']['client_id']
client_secret = config['naver_login']['client_secret']

oauth = OAuthDTO.api

# 인증번호 생성
def generate_code():
    code = str(random.randint(0, 999999)).zfill(6)
    return code

# 인증번호 확인
def compare_code(code):
    if not 'code' in session:
        return False
    return session['code'] == code

@oauth.route("/naver/login")
class NaverLogin(Resource):
    def get(self):
        # 네이버 토큰 검증
        naver_token = request.args.get('refresh_token')
        params = {
            'client_id': client_id,
            'client_secret': client_secret,
            'refresh_token': naver_token,
            'grant_type': 'refresh_token',
            'service_provider': 'NAVER'
        }
        naver_request = requests.post(
            "https://nid.naver.com/oauth2.0/token", params=params)
        naver_data = naver_request.json()
        if 'access_token' not in naver_data.keys():
            return { 'message': '네이버 로그인에 실패했어요 :(' }, 401
        
        # 필요한 데이터 검증
        naver_identifier = request.args.get('identifier')
        if naver_identifier is None or naver_identifier == '':
            return { 'message': '네이버 로그인에 실패했어요 :(' }, 401
        name = request.args.get('name')
        if name is None or name == '':
            return { 'message': '네이버 로그인에 실패했어요 :(' }, 401
        phone_number = request.args.get('phone_number')
        if phone_number is None or phone_number == '':
            return { 'message': '네이버 로그인에 실패했어요 :(' }, 401
        phone_number = re.sub(r'\D', '', phone_number)
        phone_number = re.sub(r'(\d{3})(\d{4})(\d{4})', r'\1-\2-\3', phone_number)

        # 데이터로 유저 정보 조회
        user_id = hashlib.sha256(name.encode('utf-8') + phone_number.encode('utf-8')).hexdigest()
        database = Database()
        sql = f"SELECT is_signed FROM users WHERE id = '{user_id}';"
        is_signed = database.execute_one(sql)
        if is_signed is None:
            database.close()
            return { 'message': '판도라큐브 회원 정보가 없어요 :(' }, 401
        
        # 토큰 생성
        access_token = create_access_token(identity=user_id)
        refresh_token = create_refresh_token(identity=user_id)
        token = { 'access_token': access_token, 'refresh_token': refresh_token }
        
        # 판도라큐브 회원인 경우에 대한 처리
        is_signed = is_signed['is_signed']
        if is_signed:
            # 이미 PCube+에 가입한 경우에는 로그인으로 처리
            database.close()
            return token, 200
        
        # 처음 가입하는 경우
        sql = f"INSERT INTO identifier VALUES('{naver_identifier}', '{user_id}', 0);"
        database.execute(sql)
        sql = f"UPDATE users SET is_signed = 1 WHERE id = '{user_id}';"
        database.execute(sql)
        database.commit()
        database.close()
        
        return token, 200

@oauth.route("/naver/leave")
class NaverLoginLeave(Resource):
    def post(self):
        headers = request.headers
        if headers.get('Authorization') is None:
            return {'message': 'Unauthorized'}, 401

        access_token = headers.get('Authorization')
        params = {
            'client_id': client_id,
            'client_secret': client_secret,
            'access_token': access_token,
            'grant_type': 'delete',
            'service_provider': 'NAVER'
        }

        leave_request = requests.post(
            "https://nid.naver.com/oauth2.0/token", params=params)
        leave_data = leave_request.json()

        return leave_data

@oauth.route('/code/request')
class OauthCodeRequestAPI(Resource):
    # 인증번호 발송
    @oauth.expect(OAuthDTO.model_oauth_code_request, validate=True)
    @oauth.response(200, 'OK', OAuthDTO.response_oauth_sms_validation)
    def post(self):
        # Body 데이터 읽어오기
        code_request = request.get_json()

        # 전화번호
        phone_number = code_request['phone_number']

        # 인증번호 생성 및 세션에 저장
        code = generate_code()
        session['code'] = code
        session.modified = True

        # SMS 발송
        message = f"[PCube+]\n인증번호는 {code}입니다."
        result = sms.send_msg(phone_number, message)

        # SMS API 호출 성공 여부에 따른 결과 반환        
        if result.status_code == 200:
            return {'is_success': True}, 200
        else:
            return {'is_success': False}, 200

@oauth.route('/code/confirm')
class OauthCodeConfirmAPI(Resource):
    # 인증번호 확인
    @oauth.expect(OAuthDTO.model_oauth_code_confirm, validate=True)
    @oauth.response(200, 'OK', OAuthDTO.response_oauth_code_result)
    def post(self):
        # Body 데이터 읽어오기
        code_confirm = request.get_json()

        # 인증번호
        code = code_confirm['code']

        # 인증 성공 여부에 따른 결과 반환
        if compare_code(code):
            session.pop('code')
            session.modified = True
            return {'is_verified': True}, 200
        else:
            return {'is_verified': False}, 200
        
@oauth.route('/user')
class OauthUserCheckAPI(Resource):
    # 회원 여부 확인
    @oauth.expect(OAuthDTO.model_oauth_user, validate=True)
    @oauth.response(200, 'OK', OAuthDTO.response_oauth_user)
    @oauth.response(400, 'Bad Request', OAuthDTO.response_oauth_message)
    def post(self):
        # Body 데이터 읽어오기
        user_info = request.get_json()

        # 휴대폰 번호 ###-####-#### 형태로 변경
        user_info['phone_number'] = re.sub(r'\D', '', user_info['phone_number'])
        user_info['phone_number'] = re.sub(r'(\d{3})(\d{4})(\d{4})', r'\1-\2-\3', user_info['phone_number'])

        # 이름 + 전화번호로 id 얻기
        id = hashlib.sha256(str(user_info['name'] + user_info['phone_number']).encode('utf-8')).hexdigest()

        # DB 예외 처리
        try:
            # DB의 유저 테이블에 id가 존재하는지 확인
            database = Database()
            sql = f"SELECT id FROM users WHERE id = '{id}';"
            user = database.execute_one(sql)
        except:
            return {'message': '서버에 오류가 발생했어요 :(\n지속적으로 발생하면 문의주세요!'}, 400
        finally:
            database.close()

        # 회원 여부에 따른 결과 반환
        if user:
            return {'is_member': True}, 200
        else:
            return {'is_member': False}, 200