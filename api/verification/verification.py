from flask import Flask, request, session, current_app
from flask_restx import Resource, Namespace
from database.database import Database
import random, sms
from utils.dto import VerificationDTO
import hashlib

verification = VerificationDTO.api

# 인증번호 생성
def generate_code():
    code = str(random.randint(0, 999999)).zfill(6)
    return code

# 인증번호 확인
def compare_code(code):
    if not 'code' in session:
        return False
    return session['code'] == code

@verification.route('/request')
class VerificationRequestAPI(Resource):
    # 인증번호 발송
    @verification.expect(VerificationDTO.model_verification_request, validate=True)
    @verification.response(200, 'OK', VerificationDTO.response_verification_sms_validation)
    def post(self):
        # Body 데이터 읽어오기
        verification = request.get_json()

        # 전화번호
        phone_number = verification['phone_number']

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

@verification.route('/confirm')
class VerificationConfirmAPI(Resource):
    # 인증번호 확인
    @verification.expect(VerificationDTO.model_verification_confirm, validate=True)
    @verification.response(200, 'OK', VerificationDTO.response_verification_result)
    def post(self):
        # Body 데이터 읽어오기
        verification = request.get_json()

        # 인증번호
        code = verification['code']

        # 인증 성공 여부에 따른 결과 반환
        if compare_code(code):
            session.pop('code')
            session.modified = True
            return {'is_verified': True}, 200
        else:
            return {'is_verified': False}, 200
        
@verification.route('/user')
class VerificationNameCheckAPI(Resource):
    # 회원 여부 확인
    @verification.expect(VerificationDTO.model_verification_user, validate=True)
    @verification.response(200, 'OK', VerificationDTO.response_verification_name)
    @verification.response(400, 'Bad Request', VerificationDTO.response_verification_message)
    def post(self):
        # Body 데이터 읽어오기
        verification = request.get_json()

        # 이름 + 전화번호로 id 얻기
        id = hashlib.sha256(str(verification['name'] + verification['phone_number']).encode('utf-8')).hexdigest()

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