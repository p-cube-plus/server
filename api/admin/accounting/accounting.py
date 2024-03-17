from flask import Flask, request
from flask_restx import Resource, Namespace
from database.database import Database
from datetime import datetime, date
from utils.dto import AdminAccountingDTO
from flask_jwt_extended import jwt_required, get_jwt_identity
from utils.enum_tool import AccountingEnum, UserEnum
from utils.aes_cipher import AESCipher


accounting = AdminAccountingDTO.api

# 작년 6월의 시작일을 문자열로 반환
def get_start_month():
    start_month = date(datetime.today().year - 1, 6, 1)
    return start_month.strftime('%Y-%m-%d')

# 금월의 시작일을 문자열로 반환
def get_current_month():
    current_month = date(datetime.today().year, datetime.today().month, 1)
    return current_month.strftime('%Y-%m-%d')
    
@accounting.route('')
class MembershipFeeCheckAPI(Resource):
    # 월별 회비 납부 내역 얻기
    @accounting.response(200, 'OK', [AdminAccountingDTO.model_monthly_payment])
    @accounting.response(400, 'Bad Request', AdminAccountingDTO.response_message)
    @accounting.doc(security='apiKey')
    @jwt_required()
    def get(self):
        # 금월 및 작년 6월 날짜 문자열로 얻기
        current_month = get_current_month()
        start_month = get_start_month()
        
        # DB 예외 처리
        try:
            database = Database()

            # DB에서 월별 회비 납부 기간 불러오기
            sql = f"SELECT date, start_date, end_date FROM monthly_payment_periods "\
                f"WHERE date between '{start_month}' and '{current_month}' "\
                f"ORDER BY date;"
            payment_period_list = database.execute_all(sql)

            # DB에서 기간에 맞는 회비 납부 내역 불러오기
            sql = f"SELECT date, name, level, grade, amount, category FROM membership_fees mf "\
                f"JOIN users u ON mf.user_id = u.id "\
                f"WHERE date between '{start_month}' and '{current_month}' "\
                f"ORDER BY date;"
            user_payment_list = database.execute_all(sql)

            # 회원 이름 복호화
            crypt = AESCipher()
            for idx, user_payment in enumerate(user_payment_list):
                user_payment_list[idx]['name'] = crypt.decrypt(user_payment['name'])
        except:
            return {'message': '서버에 오류가 발생했어요 :(\n지속적으로 발생하면 문의주세요!'}, 400
        finally:
            database.close()

        # 납부 기간 내역의 날짜 데이터들을 문자열로 변경
        for idx, payment_period in enumerate(payment_period_list):
            payment_period_list[idx]['date'] = payment_period['date'].strftime('%Y-%m-%d')
            payment_period_list[idx]['start_date'] = payment_period['start_date'].strftime('%Y-%m-%d')
            payment_period_list[idx]['end_date'] = payment_period['end_date'].strftime('%Y-%m-%d')

        # 회비 납부 내역의 날짜 및 index 데이터들을 문자열로 변경 
        for idx, user_payment in enumerate(user_payment_list):
            user_payment_list[idx]['date'] = user_payment['date'].strftime('%Y-%m-%d')
            user_payment_list[idx]['category'] = AccountingEnum.PaymentState(user_payment['category'])
            user_payment_list[idx]['level'] = UserEnum.Level(user_payment['level'])

        # 월별 회비 납부 내역 만들기
        monthly_payment_list = []

        for payment_period in payment_period_list:
            monthly_payment = {}
            # 회비 납부 기간 추가
            monthly_payment.update(payment_period)

            # 회비 납부 내역 추가
            monthly_payment.update({'user_payment_list': []})

            for user_payment in user_payment_list:
                if user_payment['date'] == monthly_payment['date']:
                    monthly_payment['user_payment_list'].append(user_payment)

            monthly_payment_list.append(monthly_payment)

        if not monthly_payment_list: # 월별 회비 납부 내역이 없을 때의 처리
            return [], 200
        else:
            return monthly_payment_list, 200

@accounting.route('/period')
class MembershipFeePeriodAPI(Resource):
    # 전체 월별 회비 기간 얻기
    @accounting.response(200, 'OK', [AdminAccountingDTO.model_payment_period])
    @accounting.response(400, 'Bad Request', AdminAccountingDTO.response_message)
    @accounting.doc(security='apiKey')
    @jwt_required()
    def get(self):
        # 금월 및 작년 6월 날짜 문자열로 얻기
        current_month = get_current_month()
        start_month = get_start_month()

        # DB 예외 처리
        try:
            # DB에서 월별 회비 납부 기간 불러오기
            database = Database()
            sql = f"SELECT date, start_date, end_date FROM monthly_payment_periods "\
                f"WHERE date between '{start_month}' and '{current_month}' "\
                f"ORDER BY date;"
            payment_period_list = database.execute_all(sql)
        except:
            return {'message': '서버에 오류가 발생했어요 :(\n지속적으로 발생하면 문의주세요!'}, 400
        finally:
            database.close()

        if not payment_period_list: # 납부 기간이 없을 때 처리
            return [], 200
        else:
            # 납부 기간 내역의 날짜 데이터들을 문자열로 변경
            for idx, payment_period in enumerate(payment_period_list):
                payment_period_list[idx]['date'] = payment_period['date'].strftime('%Y-%m-%d')
                payment_period_list[idx]['start_date'] = payment_period['start_date'].strftime('%Y-%m-%d')
                payment_period_list[idx]['end_date'] = payment_period['end_date'].strftime('%Y-%m-%d')
            
            return payment_period_list, 200
    
    # 특정 달 회비 기간 생성하기
    @accounting.expect(AdminAccountingDTO.model_payment_period, required=True)
    @accounting.response(201, 'Created', AdminAccountingDTO.response_message)
    @accounting.response(400, 'Bad Request', AdminAccountingDTO.response_message)
    @accounting.doc(security='apiKey')
    @jwt_required()
    def post(self):
        # Body 데이터 읽어오기
        payment_period = request.get_json()

        # DB 예외 처리
        try:
            # 회비 기간 정보를 DB에 추가
            database = Database()
            sql = f"INSERT INTO monthly_payment_periods "\
                f"VALUES('{payment_period['date']}', '{payment_period['start_date']}', '{payment_period['end_date']}');"
            database.execute(sql)
            database.commit()
        except:
            return {'message': '서버에 오류가 발생했어요 :(\n지속적으로 발생하면 문의주세요!'}, 400
        finally:
            database.close()

        return {'message': '회비 기간을 설정했어요 :)'}, 201

    # 특정 달 회비 기간 수정하기
    @accounting.expect(AdminAccountingDTO.model_payment_period, required=True)
    @accounting.response(200, 'OK', AdminAccountingDTO.response_message)
    @accounting.response(400, 'Bad Request', AdminAccountingDTO.response_message)
    @accounting.doc(security='apiKey')
    @jwt_required()
    def put(self):
        # Body 데이터 읽어오기
        payment_period = request.get_json()

        # DB 예외 처리
        try:
            # DB의 회비 기간 정보를 수정
            database = Database()
            sql = f"UPDATE monthly_payment_periods SET "\
                f"start_date = '{payment_period['start_date']}', end_date = '{payment_period['end_date']}' "\
                f"WHERE date = '{payment_period['date']}';"
            database.execute(sql)
            database.commit()
        except:
            return {'message': '서버에 오류가 발생했어요 :(\n지속적으로 발생하면 문의주세요!'}, 400
        finally:
            database.close()

        return {'message': '회비 기간을 수정했어요 :)'}, 200
    
    # 특정 달 회비 기간 삭제하기
    @accounting.expect(AdminAccountingDTO.query_admin_account_date, required=True)
    @accounting.response(200, 'OK', AdminAccountingDTO.response_message)
    @accounting.response(400, 'Bad Request', AdminAccountingDTO.response_message)
    @accounting.doc(security='apiKey')
    @jwt_required()
    def delete(self):
        # Query parameter 읽어오기
        payment_date = request.args['date']

        # DB 예외 처리
        try:
            # DB의 회비 기간 정보를 삭제
            database = Database()
            sql = f"DELETE FROM monthly_payment_periods WHERE date = '{payment_date}';"
            database.execute(sql)
            database.commit()
        except:
            return {'message': '서버에 오류가 발생했어요 :(\n지속적으로 발생하면 문의주세요!'}, 400
        finally:
            database.close()

        return {'message': '회비 기간을 삭제했어요 :)'}, 200