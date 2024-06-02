from flask import Flask, request
from flask_restx import Resource, Namespace
from database.database import Database
from datetime import datetime, date
from utils.dto import AccountingDTO
from flask_jwt_extended import jwt_required, get_jwt_identity
from utils.enum_tool import AccountingEnum
from utils.api_access_level_tool import api_access_level

accounting = AccountingDTO.api

@accounting.route('')
class AccountingUserAPI(Resource):
    @accounting.response(200, 'OK', AccountingDTO.model_payment_info)
    @accounting.response(400, 'Bad Request', AccountingDTO.accounting_response_message)
    @accounting.doc(security='apiKey')
    @api_access_level(1)
    @jwt_required()
    def get(self):
        user_id = get_jwt_identity()

        current_month = date(datetime.today().year, datetime.today().month, 1).strftime('%Y-%m-%d')
        start_month = date(datetime.today().year - 1, 6, 1).strftime('%Y-%m-%d')

        try:
            database = Database()

            sql = "SELECT date, amount, category FROM membership_fees WHERE user_id = %s AND date BETWEEN %s AND %s ORDER BY date;"
            values = (user_id, start_month, current_month)
            monthly_payment_list = database.execute_all(sql, values)

            sql = "SELECT start_date, end_date FROM monthly_payment_periods WHERE date = %s;"
            values = (current_month,)
            payment_period = database.execute_one(sql, values)
            
            sql = "SELECT value FROM data_map WHERE category = 'account_balance';"
            total_amount = int(database.execute_one(sql)['value'])
        except Exception as e:
            return {'message': '서버에 오류가 발생했어요 :(\n지속적으로 발생하면 문의주세요!', 'error': str(e)}, 400
        finally:
            database.close()

        payment_amount = None
        if monthly_payment_list and monthly_payment_list[-1]['date'].strftime('%Y-%m-%d') == current_month:
            payment_amount = monthly_payment_list[-1]['amount']

        if payment_period:
            payment_period['start_date'] = payment_period['start_date'].strftime('%Y-%m-%d')
            payment_period['end_date'] = payment_period['end_date'].strftime('%Y-%m-%d')

        payment_data = {
            'monthly_payment_list': monthly_payment_list,
            'payment_period': payment_period,
            'payment_amount': payment_amount,
            'total_amount': total_amount
        }

        if not monthly_payment_list:
            return payment_data, 200
        else:
            for idx, monthly_payment in enumerate(monthly_payment_list):
                monthly_payment_list[idx]['date'] = monthly_payment['date'].strftime('%Y-%m-%d')
                monthly_payment_list[idx]['category'] = AccountingEnum.PaymentState(monthly_payment['category'])

            return payment_data, 200
    
@accounting.route('/list')
class AccountingListAPI(Resource):
    @accounting.response(200, 'OK', AccountingDTO.model_accounting_info)
    @accounting.response(400, 'Bad Request', AccountingDTO.accounting_response_message)
    @accounting.doc(security='apiKey')
    @api_access_level(1)
    def get(self):
        try:
            database = Database()
            sql = "SELECT * FROM accountings;"
            accounting_list = database.execute_all(sql)

            sql = "SELECT value FROM data_map WHERE category = 'account_balance';"
            total_amount = int(database.execute_one(sql)['value'])
        except Exception as e:
            return {'message': '서버에 오류가 발생했어요 :(\n지속적으로 발생하면 문의주세요!', 'error': str(e)}, 400
        finally:
            database.close()

        result_data = {'accounting_list': accounting_list, 'total_amount': total_amount}

        if not accounting_list:
            return result_data, 200
        else:
            for idx, accounting in enumerate(accounting_list):
                accounting_list[idx]['date'] = accounting['date'].strftime('%Y-%m-%d')
                accounting_list[idx]['payment_method'] = AccountingEnum.PaymentMethod(accounting['payment_method'])
            return result_data, 200
