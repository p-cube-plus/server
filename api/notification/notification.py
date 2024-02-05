from flask import Flask, request
from flask_restx import Resource, Namespace
from database.database import Database
from utils.dto import NotificationDTO
from flask_jwt_extended import jwt_required, get_jwt_identity

notification = NotificationDTO.api

@notification.route('/list')
class NotificationAPI(Resource):

    # 회원 알림 목록 얻기
    @notification.response(200, 'OK', [NotificationDTO.model_user_notification])
    @notification.response(400, 'Bad Request', NotificationDTO.response_notification_message)
    @notification.doc(security='apiKey')
    @jwt_required()
    def get(self):
        user_id = get_jwt_identity()

        # DB 예외처리
        try: 
            database = Database()
            sql = f"SELECT n.id, n.date, n.day, n.time, n.location, n.schedule, n.message, nm.is_read "\
                f"FROM notification AS n JOIN notification_member AS nm ON n.id = nm.notification_id "\
                f"AND nm.user_id = '{user_id}' AND nm.is_sent = 1 "\
                f"ORDER BY n.date DESC;"
            notifications = database.execute_all(sql)
        except:
            return {'message': '서버에 오류가 발생했어요 :(\n지속적으로 발생하면 문의주세요!'}, 400
        finally:
            database.close()

        for idx, notification in enumerate(notifications):
            notifications[idx]['date'] = notification['date'].strftime('%Y-%m-%d')
            notifications[idx]['time'] = str(notification['time'])
            notifications[idx]['is_read'] = bool(notification['is_read'])

        return notifications, 200
    
    # 회원 알림 정보 수정
    @notification.expect(NotificationDTO.model_notification_status, validate=True)
    @notification.response(200, 'OK', NotificationDTO.response_notification_message)
    @notification.response(400, 'Bad Request', NotificationDTO.response_notification_message)
    @notification.doc(security='apiKey')
    @jwt_required()
    def put(self):
        notification_status = request.get_json()
        
        # DB 예외처리
        try:
            database = Database()
            sql = f"UPDATE notification_member SET is_read = {int(notification_status['is_read'])} WHERE notification_id = {notification_status['id']};"
            database.execute(sql)
            database.commit()
        except:
            return {'message': '서버에 오류가 발생했어요 :(\n지속적으로 발생하면 문의주세요!'}, 400
        finally:
            database.close()

        return {'message': '회원 알림 상태 정보를 수정했어요 :)'}, 200
    
    # 회원 알림 정보 삭제
    @notification.expect(NotificationDTO.model_user_notification_id, validate=True)
    @notification.response(200, 'OK', NotificationDTO.response_notification_message)
    @notification.response(400, 'Bad Request', NotificationDTO.response_notification_message)
    @notification.doc(security='apiKey')
    @jwt_required()
    def delete(self):
        notification_id = request.get_json()['id']

        # DB 예외처리
        try:
            database = Database()
            sql = f"DELETE FROM notification_member WHERE notification_id = {notification_id};"
            database.execute(sql)
            database.commit()
            database.close()
        except:
            return {'message': '서버에 오류가 발생했어요 :(\n지속적으로 발생하면 문의주세요!'}, 400
        finally:
            database.close()

        return {'message': '회원 알림 상태 정보를 삭제했어요 :)'}, 200