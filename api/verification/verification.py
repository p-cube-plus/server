from flask import Flask, request
from flask_restx import Resource, Namespace
from database.database import Database
import time, random, sms

verification = Namespace('verification', description='회원 휴대폰 인증')

storage = {}

def generate_code(phone_number):
    code = str(random.randint(0, 999999)).zfill(6)
    storage[phone_number] = {'code': code, 'time': time.time()}
    return code

def compare_code(phone_number, code):
    if phone_number not in storage:
        return False
    return storage[phone_number]['code'] == code

verification.route("/request")
class VerificationRequestAPI(Resource):
    def post(self):
        phone_number = request.get_json()['phone_number']

        code = generate_code()
        message = f"인증번호: {code}\n 타인 유출로 인한 피해 주의"

        sms.send(phone_number, message)

        return {'message': '인증 번호가 발송되었어요 :)'}, 200

verification.route('/confirm')
class VerificationConfirmAPI(Resource):
    def post(self):
        phone_number = request.get_json()['phone_number']
        code = request.get_json()['verification_code']

        # 인증 여부 반환 (추후 확장을 고려하여 조건문으로 작성)
        if compare_code(phone_number, code):
            return {'is_verified': True}, 200
        else:
            return {'is_verified': False}, 200