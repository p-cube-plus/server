from flask import Flask, request
from flask_restx import Resource, Namespace
from database.database import Database
from datetime import datetime, date
from utils.dto import AdminNotificationDTO
from flask_jwt_extended import jwt_required, get_jwt_identity
from utils.enum_tool import convert_to_index, convert_to_string, NotificationEnum

notification = AdminNotificationDTO.api

@notification.route('/category/<int:category>')
class NotificationByCategoryAPI(Resource):
    # category에 따른 알림 목록 얻기
    @notification.response(200, 'OK', AdminNotificationDTO.response_notification_list)
    @notification.response(400, 'Bad Request', AdminNotificationDTO.response_message)
    @notification.doc(security='apiKey')
    @jwt_required()
    def get(self, category):
        # DB 예외 처리
        try: 
            # DB에서 category값에 맞는 알림 목록 가져오기
            database = Database()
            sql = f"SELECT id, member_category, time, start_date, end_date, day, cycle, message, memo FROM notification WHERE category = {category};"
            notification_list = database.execute_all(sql)
        except:
            database.close()
            return {'message': '서버에 오류가 발생했어요 :(\n지속적으로 발생하면 문의주세요!'}, 400

        if not notification_list: # 알림이 없을 때 처리
            database.close()
            return {'notification_list': []}, 200
        else:
            for idx, notification in enumerate(notification_list):
                # time, date, category, day를 문자열로 변경
                notification_list[idx]['time'] = str(notification['time'])
                notification_list[idx]['start_date'] = notification['start_date'].strftime('%Y-%m-%d')
                notification_list[idx]['end_date'] = notification['end_date'].strftime('%Y-%m-%d')
                notification_list[idx]['member_category'] = convert_to_string(MEMBER_CATEGORY, notification['member_category'])
                notification_list[idx]['day'] = convert_to_string(DAY_CATEGORY, notification['day'])

                # DB에서 알림 대상자 목록 가져오기
                sql = f"SELECT user_id FROM notification_member WHERE notification_id = {notification['id']};"
                member_list = database.execute_all(sql)
                notification_list[idx]['member_list'] = [member['user_id'] for member in member_list]
            
            database.close()
            return {'notification_list': notification_list}, 200
    
    # 알림 정보 추가
    @notification.expect(AdminNotificationDTO.model_notification, validate=True)
    @notification.response(200, 'OK', AdminNotificationDTO.response_message)
    @notification.response(400, 'Bad Request', AdminNotificationDTO.response_message)
    @notification.doc(security='apiKey')
    @jwt_required()
    def post(self, category):
        # Body 데이터 읽어오기
        notification = request.get_json()
        
        # category, day를 index로 변환
        notification['member_category'] = convert_to_index(NotificationEnum.MEMBER_CATEGORY, notification['member_category'])
        notification['day'] = convert_to_index(NotificationEnum.DAY_CATEGORY, notification['day'])
        
        # DB 예외 처리
        try:
            database = Database()

            # 알림 정보를 DB에 추가
            sql = "INSERT INTO notification "\
                f"VALUES(NULL, {category}, {notification['member_category']}, '{notification['time']}', "\
                f"'{notification['start_date']}', '{notification['end_date']}', {notification['day']}, "\
                f"'{notification['cycle']}', '{notification['message']}', '{notification['memo']}');"
            database.execute(sql)

            # 추가한 알림 정보의 id값 가져오기
            id = database.cursor.lastrowid

            if notification['member_list']:
                # 알림 대상자 정보를 DB에 추가
                sql = f"INSERT INTO notification_member VALUES ({id}, %s);"
                values = [(member,) for member in notification['member_list']]
                database.execute_many(sql, values)

            database.commit()
        except:
            return {'message': '서버에 오류가 발생했어요 :(\n지속적으로 발생하면 문의주세요!'}, 400
        finally:
            database.close()

        return {'message': '알림 정보를 추가했어요 :)'}, 201

    # 알림 정보 수정
    @notification.expect(AdminNotificationDTO.model_notification, validate=True)
    @notification.response(200, 'OK', AdminNotificationDTO.response_message)
    @notification.response(400, 'Bad Request', AdminNotificationDTO.response_message)
    @notification.doc(security='apiKey')
    @jwt_required()
    def put(self, category):
        # Body 데이터 읽어오기
        notification = request.get_json()

        # category, day를 index로 변환
        notification['member_category'] = convert_to_index(NotificationEnum.MEMBER_CATEGORY, notification['member_category'])
        notification['day'] = convert_to_index(NotificationEnum.DAY_CATEGORY, notification['day'])

        print(notification)
        # DB 예외 처리
        try:
            database = Database()

            # 수정된 알림 정보를 DB에 반영
            sql = "UPDATE notification SET "\
                f"category = {category}, member_category = {notification['member_category']}, time = '{notification['time']}', "\
                f"start_date = '{notification['start_date']}', end_date = '{notification['end_date']}', day = {notification['day']}, "\
                f"cycle = '{notification['cycle']}', message = '{notification['message']}', memo = '{notification['memo']}' "\
                f"WHERE id = {notification['id']};"
            database.execute(sql)

            # 기존 알림 대상자 정보를 DB에서 삭제
            sql = f"DELETE FROM notification_member WHERE notification_id = {notification['id']};"
            database.execute(sql)
            
            if notification['member_list']:
                # 새로운 알림 대상자 정보를 DB에 추가
                sql = f"INSERT INTO notification_member VALUES ({notification['id']}, %s);"
                values = [(member,) for member in notification['member_list']]
                database.execute_many(sql, values)

            database.commit()
        except:
            return {'message': '서버에 오류가 발생했어요 :(\n지속적으로 발생하면 문의주세요!'}, 400
        finally:
            database.close()

        return {'message': '알림 정보를 수정했어요 :)'}, 200

    # 알림 정보 삭제
    @notification.expect(AdminNotificationDTO.query_notification_id, validate=True)
    @notification.response(200, 'OK', AdminNotificationDTO.response_message)
    @notification.response(400, 'Bad Request', AdminNotificationDTO.response_message)
    @notification.doc(security='apiKey')
    @jwt_required()
    def delete(self, category):
        notification_id = request.args['notification_id']

        # DB 예외 처리
        try:
            database = Database()

            # 알림 대상자 정보를 DB에서 삭제
            sql = f"DELETE FROM notification_member WHERE notification_id = {notification_id};"
            database.execute(sql)

            # 알림 정보를 DB에서 삭제
            sql = f"DELETE FROM notification WHERE id = {notification_id};"
            database.execute(sql)

            database.commit()
        except:
            return {'message': '서버에 오류가 발생했어요 :(\n지속적으로 발생하면 문의주세요!'}, 400
        finally:
            database.close()

        return {'message': '알림 정보를 삭제했어요 :)'}, 200
    
@notification.route('/users')
class NotificationUserListAPI(Resource):
    # 회원 목록 얻기
    @notification.response(200, 'OK', AdminNotificationDTO.response_user_list)
    @notification.response(400, 'Bad Request', AdminNotificationDTO.response_message)
    @notification.doc(security='apiKey')
    @jwt_required()
    def get(self):
        # DB 예외 처리
        try:
            # DB에서 회원 목록 불러오기
            database = Database()
            sql = "SELECT id, name, grade FROM users;"
            user_list = database.execute_all(sql)
        except:
            return {'message': '서버에 오류가 발생했어요 :(\n지속적으로 발생하면 문의주세요!'}, 400
        finally:
            database.close()
        return {'user_list': user_list}, 200

@notification.route('/payment-period')
class NotificationPaymentPeriodAPI(Resource):
    # 전체 월별 회비 기간 얻기
    @notification.response(200, 'OK', AdminNotificationDTO.response_payment_period_list)
    @notification.response(400, 'Bad Request', AdminNotificationDTO.response_message)
    @notification.doc(security='apiKey')
    @jwt_required()
    def get(self):

        # 금월 및 작년 6월 날짜 문자열로 얻기
        current_month = date(datetime.today().year, datetime.today().month, 1).strftime('%Y-%m-%d')
        start_month = date(datetime.today().year - 1, 6, 1).strftime('%Y-%m-%d')

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
            return {'payment_period_list': []}, 200
        else:
            # 납부 기간 내역의 날짜 데이터들을 문자열로 변경
            for idx, payment_period in enumerate(payment_period_list):
                payment_period_list[idx]['date'] = payment_period['date'].strftime('%Y-%m-%d')
                payment_period_list[idx]['start_date'] = payment_period['start_date'].strftime('%Y-%m-%d')
                payment_period_list[idx]['end_date'] = payment_period['end_date'].strftime('%Y-%m-%d')
            
            return {'payment_period_list': payment_period_list}, 200