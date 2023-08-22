from flask import Flask, request
from flask_restx import Resource, Namespace
from database.database import Database
from datetime import datetime, date

notification = Namespace('notification')

# 알림 category
NOTIFICATION_CATEGORY = {0: '정기 회의', 1: '디자인 파트 회의', 2: '아트 파트 회의', 3: '프로그래밍 파트 회의', 4: '청소', 5: '기타'}

# index 데이터를 문자열로 변경
def convert_to_string(dictionary, index):
    return dictionary.get(index, None)

# 문자열 데이터를 index로 변경
def convert_to_index(dictionary, string):
    for key, value in dictionary.items():
        if value == string:
            return key
    return None

@notification.route('/category/<int:category>')
class NotificationByCategoryAPI(Resource):
    # category에 따른 알림 목록 얻기
    def get(self, category):
        # DB에서 category값에 맞는 알림 목록 가져오기
        database = Database()
        sql = f"SELECT * FROM notification WHERE category = {category};"
        notification_list = database.execute_all(sql)

        if not notification_list: # 알림이 없을 때 처리
            database.close()
            return [], 200
        else:
            for idx, notification in enumerate(notification_list):
                # time, date, category를 문자열로 변경
                notification_list[idx]['time'] = str(notification['time'])
                notification_list[idx]['start_date'] = notification['start_date'].strftime('%Y-%m-%d')
                notification_list[idx]['end_date'] = notification['end_date'].strftime('%Y-%m-%d')
                notification_list[idx]['category'] = convert_to_string(NOTIFICATION_CATEGORY, notification['category'])

                # DB에서 알림 대상자 목록 가져오기
                sql = f"SELECT user_id FROM notification_member WHERE notification_id = {notification['id']};"
                member_list = database.execute(sql)
                notification_list[idx]['member_list'] = member_list
            
            database.close()
            return notification_list, 200
        
    def post(self, category):
        # Body 데이터 읽어오기
        notification = request.get_json()
        
        # category 설정
        notification['category'] = category

        database = Database()

        # 알림 정보를 DB에 추가
        sql = "INSERT INTO notification "\
            f"VALUES(NULL, {notification['category']}, '{notification['time']}', "\
            f"'{notification['start_date']}', '{notification['end_date']}', {notification['day']}, "\
            f"'{notification['cycle']}', '{notification['message']}', '{notification['memo']}');"
        database.execute(sql)

        # 추가한 알림 정보의 id값 가져오기
        id = database.cursor.lastrowid

        # 알림 대상자 정보를 DB에 추가
        sql = f"INSERT INTO notification_member VALUES ({id}, %s);"
        values = [tuple(member) for member in notification['member_list']]
        database.execute_many(sql, values)

        database.commit()
        database.close()

        return notification, 200

@notification.route('/modify/<int:notification_id>')
class NotificationEditAPI(Resource):
    def put(self, notification_id):
        # Body 데이터 읽어오기
        notification = request.get_json()

        # category를 index로 변환
        notification['category'] = convert_to_index(NOTIFICATION_CATEGORY, notification['category'])

        database = Database()

        # 수정된 알림 정보를 DB에 반영
        sql = "UPDATE notification SET "\
            f"category = {notification['category']}, time = '{notification['time']}', "\
            f"start_date = '{notification['start_date']}', end_date = '{notification['end_date']}', day = {notification['day']}, "\
            f"cycle = '{notification['cycle']}', message = '{notification['message']}', memo = '{notification['memo']}' "\
            f"WHERE id = {notification_id};"
        database.execute(sql)

        # 기존 알림 대상자 정보를 DB에서 삭제
        sql = f"DELETE FROM notification_member WHERE notification_id = {notification_id};"
        database.execute(sql)

        # 새로운 알림 대상자 정보를 DB에 추가
        sql = f"INSERT INTO notification_member VALUES ({notification_id}, %s);"
        values = [tuple(member) for member in notification['member_list']]
        database.execute_many(sql, values)

        database.commit()
        database.close()

        return {'message': '알림 정보를 수정했어요 :)'}, 200

    def delete(self, notification_id):
        database = Database()

        # 알림 대상자 정보를 DB에서 삭제
        sql = f"DELETE FROM notification_member WHERE notification_id = {notification_id};"
        database.execute(sql)

        # 알림 정보를 DB에서 삭제
        sql = f"DELETE FROM notification WHERE id = {notification_id};"
        database.execute(sql)

        database.commit()
        database.close()

        return {'message': '알림 정보를 삭제했어요 :)'}, 200