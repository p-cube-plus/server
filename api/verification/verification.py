from flask import Flask, request
from flask_restx import Resource, Namespace
from database.database import Database
import time, random, sms, json
from utils.dto import VerificationDTO

verification = VerificationDTO.api

storage = {}
last_request_time = None

def generate_code(phone_number):
    code = str(random.randint(0, 999999)).zfill(6)
    storage[phone_number] = code
    return code

def compare_code(phone_number, code):
    if phone_number not in storage:
        return False
    return storage[phone_number] == code

@verification.route('/request')
class VerificationRequestAPI(Resource):
    @verification.expect(VerificationDTO.model_verification_request, validate=True)
    def post(self):
        phone_number = request.get_json()['phone_number']

        code = generate_code(phone_number)
        message = f"[PCube+]\n인증번호는 {code}입니다."

        sms.send_msg(phone_number, message)

        return {'message': '인증 번호가 발송되었어요 :)'}, 200

@verification.route('/confirm')
class VerificationConfirmAPI(Resource):
    @verification.expect(VerificationDTO.model_verification_confirm, validate=True)
    def post(self):
        verification = request.get_json()

        phone_number = verification['phone_number']
        code = verification['verification_code']

        # 인증 여부 반환 (추후 확장을 고려하여 조건문으로 작성)
        if compare_code(phone_number, code):
            storage.pop(phone_number)
            return {'is_verified': True}, 200
        else:
            return {'is_verified': False}, 200