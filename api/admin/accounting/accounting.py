from flask import Flask, request
from flask_restx import Resource, Namespace
from database.database import Database
from datetime import datetime, date
from utils.dto import AdminAccountingDTO
from flask_jwt_extended import jwt_required, get_jwt_identity
from utils.enum_tool import AccountingEnum, UserEnum
from utils.aes_cipher import AESCipher
from utils.api_access_level_tool import api_access_level

accounting = AdminAccountingDTO.api

def get_start_month():
    start_month = date(datetime.today().year - 1, 6, 1)
    return start_month.strftime('%Y-%m-%d')

def get_current_month():
    current_month = date(datetime.today().year, datetime.today().month, 1)
    return current_month.strftime('%Y-%m-%d')
    
@accounting.route('')
class MembershipFeeCheckAPI(Resource):
    @accounting.response(200, 'OK', [AdminAccountingDTO.model_monthly_payment])
    @accounting.response(400, 'Bad Request', AdminAccountingDTO.response_message)
    @accounting.doc(security='apiKey')
    @api_access_level(2)
    def get(self):
        current_month = get_current_month()
        start_month = get_start_month()
        
        try:
            database = Database()

            sql = "SELECT date, start_date, end_date FROM monthly_payment_periods WHERE date BETWEEN %s AND %s ORDER BY date;"
            values = (start_month, current_month)
            payment_period_list = database.execute_all(sql, values)

            sql = "SELECT date, name, level, grade, amount, category FROM membership_fees mf JOIN users u ON mf.user_id = u.id WHERE date BETWEEN %s AND %s ORDER BY date;"
            values = (start_month, current_month)
            user_payment_list = database.execute_all(sql, values)

            crypt = AESCipher()
            for idx, user_payment in enumerate(user_payment_list):
                user_payment_list[idx]['name'] = crypt.decrypt(user_payment['name'])
        except Exception as e:
            return {'message': '서버에 오류가 발생했어요 :(\n지속적으로 발생하면 문의주세요!', 'error': str(e)}, 400
        finally:
            database.close()

        for idx, payment_period in enumerate(payment_period_list):
            payment_period_list[idx]['date'] = payment_period['date'].strftime('%Y-%m-%d')
            payment_period_list[idx]['start_date'] = payment_period['start_date'].strftime('%Y-%m-%d')
            payment_period_list[idx]['end_date'] = payment_period['end_date'].strftime('%Y-%m-%d')

        for idx, user_payment in enumerate(user_payment_list):
            user_payment_list[idx]['date'] = user_payment['date'].strftime('%Y-%m-%d')
            user_payment_list[idx]['category'] = AccountingEnum.PaymentState(user_payment['category'])
            user_payment_list[idx]['level'] = UserEnum.Level(user_payment['level'])

        monthly_payment_list = []

        for payment_period in payment_period_list:
            monthly_payment = {}
            monthly_payment.update(payment_period)
            monthly_payment.update({'user_payment_list': []})

            for user_payment in user_payment_list:
                if user_payment['date'] == monthly_payment['date']:
                    monthly_payment['user_payment_list'].append(user_payment)

            monthly_payment_list.append(monthly_payment)

        if not monthly_payment_list:
            return [], 200
        else:
            return monthly_payment_list, 200

@accounting.route('/period')
class MembershipFeePeriodAPI(Resource):
    @accounting.response(200, 'OK', [AdminAccountingDTO.model_payment_period])
    @accounting.response(400, 'Bad Request', AdminAccountingDTO.response_message)
    @accounting.doc(security='apiKey')
    @api_access_level(2)
    def get(self):
        current_month = get_current_month()
        start_month = get_start_month()

        try:
            database = Database()
            sql = "SELECT date, start_date, end_date FROM monthly_payment_periods WHERE date BETWEEN %s AND %s ORDER BY date;"
            values = (start_month, current_month)
            payment_period_list = database.execute_all(sql, values)
        except Exception as e:
            return {'message': '서버에 오류가 발생했어요 :(\n지속적으로 발생하면 문의주세요!', 'error': str(e)}, 400
        finally:
            database.close()

        if not payment_period_list:
            return [], 200
        else:
            for idx, payment_period in enumerate(payment_period_list):
                payment_period_list[idx]['date'] = payment_period['date'].strftime('%Y-%m-%d')
                payment_period_list[idx]['start_date'] = payment_period['start_date'].strftime('%Y-%m-%d')
                payment_period_list[idx]['end_date'] = payment_period['end_date'].strftime('%Y-%m-%d')
            
            return payment_period_list, 200
    
    @accounting.expect(AdminAccountingDTO.model_payment_period, required=True)
    @accounting.response(201, 'Created', AdminAccountingDTO.response_message)
    @accounting.response(400, 'Bad Request', AdminAccountingDTO.response_message)
    @accounting.doc(security='apiKey')
    @api_access_level(2)
    def post(self):
        payment_period = request.get_json()

        try:
            database = Database()
            sql = "INSERT INTO monthly_payment_periods (date, start_date, end_date) VALUES (%s, %s, %s);"
            values = (payment_period['date'], payment_period['start_date'], payment_period['end_date'])
            database.execute(sql, values)
            database.commit()
        except Exception as e:
            return {'message': '서버에 오류가 발생했어요 :(\n지속적으로 발생하면 문의주세요!', 'error': str(e)}, 400
        finally:
            database.close()

        return {'message': '회비 기간을 설정했어요 :)'}, 201

    @accounting.expect(AdminAccountingDTO.model_payment_period, required=True)
    @accounting.response(200, 'OK', AdminAccountingDTO.response_message)
    @accounting.response(400, 'Bad Request', AdminAccountingDTO.response_message)
    @accounting.doc(security='apiKey')
    @api_access_level(2)
    def put(self):
        payment_period = request.get_json()

        try:
            database = Database()
            sql = "UPDATE monthly_payment_periods SET start_date = %s, end_date = %s WHERE date = %s;"
            values = (payment_period['start_date'], payment_period['end_date'], payment_period['date'])
            database.execute(sql, values)
            database.commit()
        except Exception as e:
            return {'message': '서버에 오류가 발생했어요 :(\n지속적으로 발생하면 문의주세요!', 'error': str(e)}, 400
        finally:
            database.close()

        return {'message': '회비 기간을 수정했어요 :)'}, 200
    
    @accounting.expect(AdminAccountingDTO.query_admin_account_date, required=True)
    @accounting.response(200, 'OK', AdminAccountingDTO.response_message)
    @accounting.response(400, 'Bad Request', AdminAccountingDTO.response_message)
    @accounting.doc(security='apiKey')
    @api_access_level(2)
    def delete(self):
        payment_date = request.args['date']

        try:
            database = Database()
            sql = "DELETE FROM monthly_payment_periods WHERE date = %s;"
            values = (payment_date,)
            database.execute(sql, values)
            database.commit()
        except Exception as e:
            return {'message': '서버에 오류가 발생했어요 :(\n지속적으로 발생하면 문의주세요!', 'error': str(e)}, 400
        finally:
            database.close()

        return {'message': '회비 기간을 삭제했어요 :)'}, 200
