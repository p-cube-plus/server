from flask import Flask, request
from flask_restx import Resource, Namespace
from database.database import Database
from datetime import datetime, date
from utils.dto import AccountingDTO
from flask_jwt_extended import jwt_required, get_jwt_identity
from utils.enum_tool import AccountingEnum

accounting = AccountingDTO.api

@accounting.route('')
class AccountingUserAPI(Resource):
    # 회원의 월별 회비 납부 내역 얻기
    @accounting.response(200, 'OK', AccountingDTO.model_payment_info)
    @accounting.response(400, 'Bad Request', AccountingDTO.accounting_response_message)
    @accounting.doc(security='apiKey')
    @jwt_required()
    def get(self):
        user_id = get_jwt_identity()

        # 금월 및 작년 6월 날짜 구한 뒤 문자열로 변환 ('YYYY-MM-01' 형식)
        current_month = date(datetime.today().year, datetime.today().month, 1)
        start_month = date(current_month.year - 1, 6, 1)
        current_month.strftime('%Y-%m-%d')
        start_month.strftime('%Y-%m-%d')

        # DB 예외처리
        try:
            database = Database()

            # DB에서 user_id값에 맞는 월별 회비 납부 내역 불러오기 (작년 6월부터 현재 달까지)
            sql = f"SELECT date, amount, category FROM membership_fees "\
                f"WHERE user_id = '{user_id}' "\
                f"and date between '{start_month}' and '{current_month}' "\
                f"ORDER BY date;"
            monthly_payment_list = database.execute_all(sql)

            # 금월 회비 납부 기간 불러오기
            sql = f"SELECT start_date, end_date FROM monthly_payment_periods "\
                f"WHERE date = '{current_month}';"
            payment_period = database.execute_one(sql)
            
            # 계좌 내의 총 금액 불러오기
            sql = f"SELECT value FROM data_map WHERE category = 'account_balance';"
            total_amount = int(database.execute_one(sql)['value'])
        except:
            return {'message': '서버에 오류가 발생했어요 :(\n지속적으로 발생하면 문의주세요!'}, 400
        finally:
            database.close()

        # 금월 회비 납부 금액 얻기
        payment_amount = None
        if monthly_payment_list and monthly_payment_list[-1]['date'] == current_month:
            payment_amount = monthly_payment_list[-1]['amount']

        # 납부 기간 문자열로 변환
        if payment_period:
            payment_period['start_date'] = payment_period['start_date'].strftime('%Y-%m-%d')
            payment_period['end_date'] = payment_period['end_date'].strftime('%Y-%m-%d')

        payment_data = {'monthly_payment_list': monthly_payment_list, 'payment_period': payment_period, 'payment_amount': payment_amount, 'total_amount': total_amount}

        if not monthly_payment_list: # 납부 내역이 없을 때의 처리
            return payment_data, 200
        else:
            for idx, monthly_payment in enumerate(monthly_payment_list):
                # date 및 category를 문자열로 변환
                monthly_payment_list[idx]['date'] = monthly_payment['date'].strftime('%Y-%m-%d')
                monthly_payment_list[idx]['category'] = AccountingEnum.PaymentState(monthly_payment['category'])

            return payment_data, 200
    
@accounting.route('/list')
class AccountingListAPI(Resource):
    # 회비 내역 목록 얻기
    @accounting.response(200, 'OK', AccountingDTO.model_accounting_info)
    @accounting.response(400, 'Bad Request', AccountingDTO.accounting_response_message)
    @accounting.doc(security='apiKey')
    @jwt_required()
    def get(self):
        # DB 예외처리
        try:
            database = Database()
            # DB에서 전체 회비 내역 목록 불러오기
            sql = "SELECT * FROM accountings;"
            accounting_list = database.execute_all(sql)

            # 계좌 내의 총 금액 불러오기
            sql = f"SELECT value FROM data_map WHERE category = 'account_balance';"
            total_amount = int(database.execute_one(sql)['value'])
        except:
            return {'message': '서버에 오류가 발생했어요 :(\n지속적으로 발생하면 문의주세요!'}, 400
        finally:
            database.close()

        result_data = {'accounting_list': accounting_list, 'total_amount': total_amount}

        if not accounting_list: # 회비 내역이 없을 때 처리
            return result_data, 200
        else:
            for idx, accounting in enumerate(accounting_list):
                # date, payment_method를 문자열로 변환
                accounting_list[idx]['date'] = accounting['date'].strftime('%Y-%m-%d')
                accounting_list[idx]['payment_method'] = AccountingEnum.PaymentMethod(accounting['payment_method'])
            return result_data, 200