from flask import Flask, request
from flask_restx import Resource, Namespace
from database.database import Database
from datetime import datetime, date
from utils.dto import AdminNotificationDTO
from flask_jwt_extended import jwt_required, get_jwt_identity
from utils.enum_tool import NotificationEnum
from utils.aes_cipher import AESCipher
from utils import fcm
from utils.api_access_level_tool import api_access_level

notification = AdminNotificationDTO.api

@notification.route('')
class NotificationByCategoryAPI(Resource):
    @notification.expect(AdminNotificationDTO.query_notification_category, validate=True)
    @notification.response(200, 'OK', [AdminNotificationDTO.model_notification])
    @notification.response(400, 'Bad Request', AdminNotificationDTO.response_message)
    @notification.doc(security='apiKey')
    @api_access_level(2)
    def get(self):
        category = NotificationEnum.Category(request.args['category'])

        try:
            database = Database()
            sql = "SELECT id, category, member_category, date, day, time, location, schedule, message, memo FROM notification WHERE category = %s;"
            values = (category,)
            notification_list = database.execute_all(sql, values)

            if not notification_list:
                return [], 200
            else:
                for idx, notification in enumerate(notification_list):
                    if notification['date']:
                        notification_list[idx]['date'] = notification['date'].strftime('%Y-%m-%d')
                    notification_list[idx]['schedule'] = notification['schedule'].strftime('%Y-%m-%dT%H:%M:%S')
                    notification_list[idx]['day'] = NotificationEnum.DayCategory(notification['day'])
                    notification_list[idx]['time'] = str(notification['time'])
                    notification_list[idx]['category'] = NotificationEnum.Category(notification['category'])
                    notification_list[idx]['member_category'] = NotificationEnum.MemberCategory(notification['member_category'])

                    if notification_list[idx]['member_category'] == '기타 선택':
                        sql = "SELECT user_id FROM notification_member WHERE notification_id = %s;"
                        values = (notification['id'],)
                        member_list = database.execute_all(sql, values)
                        notification_list[idx]['member_list'] = [member['user_id'] for member in member_list]
                
                return notification_list, 200
        except Exception as e:
            return {'message': '서버에 오류가 발생했어요 :(\n지속적으로 발생하면 문의주세요!', 'error': str(e)}, 400
        finally:
            database.close()
    
    @notification.expect(AdminNotificationDTO.model_notification_without_id, validate=True)
    @notification.response(201, 'Created', AdminNotificationDTO.response_message)
    @notification.response(400, 'Bad Request', AdminNotificationDTO.response_message)
    @notification.doc(security='apiKey')
    @api_access_level(2)
    def post(self):
        notification = request.get_json()
        
        notification['category'] = NotificationEnum.Category(notification['category'])
        notification['member_category'] = NotificationEnum.MemberCategory(notification['member_category'])
        notification['day'] = NotificationEnum.DayCategory(notification['day'])
        
        category = notification['category']

        if category in NotificationEnum.FcmTopic:
            notification['message'] = f"{NotificationEnum.Category(notification['category'])} "\
                f"{'파트' if category != 3 else ''} 회의가 {notification['schedule']}에 시작됩니다."

        try:
            database = Database()

            sql = "INSERT INTO notification (category, member_category, date, day, time, location, schedule, message, memo) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);"
            values = (notification['category'], notification['member_category'], notification['date'], notification['day'], notification['time'], \
                      notification['location'], notification['schedule'], notification['message'], notification['memo'])
            database.execute(sql, values)
            id = database.cursor.lastrowid

            if category == 3:
                sql = "SELECT id FROM users WHERE rest_type = -1;"
                notification['member_list'] = [user['id'] for user in database.execute_all(sql)]
            elif category <= 2:
                sql = "SELECT id FROM users WHERE rest_type = -1 AND part_index = %s;"
                values = (category,)
                notification['member_list'] = [user['id'] for user in database.execute_all(sql, values)]
            
            sql = "INSERT INTO notification_member (notification_id, user_id, read_flag, del_flag) VALUES (%s, %s, 0, 0);"
            values = [(id, member) for member in notification['member_list']]
            database.execute_many(sql, values)

            database.commit()

            if category in NotificationEnum.FcmTopic:
                title = "회의 알림"
                body = notification['message']
                topic = NotificationEnum.FcmTopic(category)
                fcm.schedule_message(str(id), title, body, notification['time'], date=notification['date'], day=notification['day'], topic=topic, targets=notification['member_list'])
            else:
                pass
        except Exception as e:
            return {'message': '서버에 오류가 발생했어요 :(\n지속적으로 발생하면 문의주세요!', 'error': str(e)}, 400
        finally:
            database.close()

        return {'message': '알림 정보를 추가했어요 :)'}, 201

    @notification.expect(AdminNotificationDTO.model_notification, validate=True)
    @notification.response(200, 'OK', AdminNotificationDTO.response_message)
    @notification.response(400, 'Bad Request', AdminNotificationDTO.response_message)
    @notification.doc(security='apiKey')
    @api_access_level(2)
    def put(self):
        notification = request.get_json()

        notification['category'] = NotificationEnum.Category(notification['category'])
        notification['member_category'] = NotificationEnum.MemberCategory(notification['member_category'])
        notification['day'] = NotificationEnum.DayCategory(notification['day'])

        category = notification['category']

        if category in NotificationEnum.FcmTopic:
            notification['message'] = f"{NotificationEnum.Category(category)} "\
                f"{'파트' if category != 3 else ''} 회의가 {notification['schedule']}에 시작됩니다."

        try:
            database = Database()

            sql = "UPDATE notification SET category = %s, member_category = %s, date = %s, day = %s, time = %s, location = %s, schedule = %s, message = %s, memo = %s WHERE id = %s;"
            values = (notification['category'], notification['member_category'], notification['date'], notification['day'], notification['time'], \
                      notification['location'], notification['schedule'], notification['message'], notification['memo'], notification['id'])
            database.execute(sql, values)

            sql = "DELETE FROM notification_member WHERE notification_id = %s;"
            values = (notification['id'],)
            database.execute(sql, values)
            
            if category == 3:
                sql = "SELECT id FROM users WHERE rest_type = -1;"
                notification['member_list'] = [user['id'] for user in database.execute_all(sql)]
            elif category <= 2:
                sql = "SELECT id FROM users WHERE rest_type = -1 AND part_index = %s;"
                values = (category,)
                notification['member_list'] = [user['id'] for user in database.execute_all(sql, values)]

            sql = "INSERT INTO notification_member (notification_id, user_id, read_flag, del_flag) VALUES (%s, %s, 0, 0);"
            values = [(notification['id'], member) for member in notification['member_list']]
            database.execute_many(sql, values)

            database.commit()

            if category in NotificationEnum.FcmTopic:
                title = "회의 알림"
                body = notification['message']
                topic = NotificationEnum.FcmTopic(category)
                fcm.schedule_message(str(notification['id']), title, body, notification['time'], date=notification['date'], day=notification['day'], topic=topic, targets=notification['member_list'])
            else:
                pass
        except Exception as e:
            return {'message': '서버에 오류가 발생했어요 :(\n지속적으로 발생하면 문의주세요!', 'error': str(e)}, 400
        finally:
            database.close()

        return {'message': '알림 정보를 수정했어요 :)'}, 200

    @notification.expect(AdminNotificationDTO.query_notification_id, validate=True)
    @notification.response(200, 'OK', AdminNotificationDTO.response_message)
    @notification.response(400, 'Bad Request', AdminNotificationDTO.response_message)
    @notification.doc(security='apiKey')
    @api_access_level(2)
    def delete(self):
        id = request.args['id']

        try:
            database = Database()

            sql = "DELETE FROM notification_member WHERE notification_id = %s;"
            values = (id,)
            database.execute(sql, values)

            sql = "DELETE FROM notification WHERE id = %s;"
            database.execute(sql, values)

            database.commit()

            fcm.remove_message(str(id))
        except Exception as e:
            return {'message': '서버에 오류가 발생했어요 :(\n지속적으로 발생하면 문의주세요!', 'error': str(e)}, 400
        finally:
            database.close()

        return {'message': '알림 정보를 삭제했어요 :)'}, 200
    
@notification.route('/users')
class NotificationUserListAPI(Resource):
    @notification.response(200, 'OK', [AdminNotificationDTO.model_admin_notification_user])
    @notification.response(400, 'Bad Request', AdminNotificationDTO.response_message)
    @notification.doc(security='apiKey')
    @api_access_level(2)
    def get(self):
        try:
            database = Database()
            sql = "SELECT id, name, grade FROM users;"
            user_list = database.execute_all(sql)

            cript = AESCipher()
            for idx, user in enumerate(user_list):
                user_list[idx]['name'] = cript.decrypt(user['name'])
        except Exception as e:
            return {'message': '서버에 오류가 발생했어요 :(\n지속적으로 발생하면 문의주세요!', 'error': str(e)}, 400
        finally:
            database.close()
        return user_list, 200

@notification.route('/payment-period')
class NotificationPaymentPeriodAPI(Resource):
    @notification.response(200, 'OK', [AdminNotificationDTO.model_admin_notification_payment_period])
    @notification.response(400, 'Bad Request', AdminNotificationDTO.response_message)
    @notification.doc(security='apiKey')
    @api_access_level(2)
    def get(self):
        current_month = date(datetime.today().year, datetime.today().month, 1).strftime('%Y-%m-%d')
        start_month = date(datetime.today().year - 1, 6, 1).strftime('%Y-%m-%d')

        try:
            database = Database()
            sql = "SELECT date, start_date, end_date FROM monthly_payment_periods WHERE date between %s AND %s ORDER BY date;"
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
