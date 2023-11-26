from flask import Flask, request
from flask_restx import Resource, Namespace
from database.database import Database
import sms

verification = Namespace('verification', description='회원 휴대폰 인증')

verification.route("")
class UserVerificationAPI(Resource):
    def get(self):
        pass
    def post(self):
        pass