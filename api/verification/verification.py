from flask import Flask, request, session
from flask_restx import Resource, Namespace
from database.database import Database
import time, random, sms, json
from utils.dto import VerificationDTO
from utils.aes_cipher import AESCipher

verification = VerificationDTO.api

# 인증번호 생성
def generate_code(phone_number):
    code = str(random.randint(0, 999999)).zfill(6)
    return code

# 인증번호 확인
def compare_code(phone_number, code):
    if not phone_number in session:
        return False
    return session[phone_number] == code

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
        code = generate_code(phone_number)
        session[phone_number] = code

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

        # 전화번호 및 인증번호
        phone_number = verification['phone_number']
        code = verification['verification_code']

        # 인증 성공 여부에 따른 결과 반환
        if compare_code(phone_number, code):
            session.pop(phone_number)
            return {'is_verified': True}, 200
        else:
            return {'is_verified': False}, 200
        
@verification.route('/name')
class VerificationNameCheckAPI(Resource):
    # 회원 여부 확인
    @verification.expect(VerificationDTO.model_verification_name, validate=True)
    @verification.response(200, 'OK', VerificationDTO.response_verification_name)
    @verification.response(400, 'Bad Request', VerificationDTO.response_verification_message)
    def post(self):
        # Body 데이터 읽어오기
        verification = request.get_json()

        # 이름 암호화
        crypt = AESCipher()
        name = crypt.encrypt(verification['name'])

        # DB 예외 처리
        try:
            # DB에서 이름에 따른 데이터 얻어오기
            database = Database()
            sql = f"SELECT id FROM users WHERE name = '{name}';"
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