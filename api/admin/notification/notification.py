from flask import Flask, request
from flask_restx import Resource, Namespace
from database.database import Database
from datetime import datetime, date

notification = Namespace('notification')

# 알림 category
NOTIFICATION_CATEGORY = {0: '정기 회의', 1: '디자인 파트 회의', 2: '아트 파트 회의', 3: '프로그래밍 파트 회의', 4: '청소', 5: '기타'}

# 알림 대상자 category
MEMBER_CATEGORY = {0: '활동 중인 회원 전체', 1: '활동 중인 정회원', 2: '활동 중인 수습회원', 3: '기타 선택'}

# 요일 category
DAY_CATEGORY = {0: '월요일', 1: '화요일', 2: '수요일', 3: '목요일', 4: '금요일', 5: '토요일', 6: '일요일'}

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
                # time, date, category, day를 문자열로 변경
                notification_list[idx]['time'] = str(notification['time'])
                notification_list[idx]['start_date'] = notification['start_date'].strftime('%Y-%m-%d')
                notification_list[idx]['end_date'] = notification['end_date'].strftime('%Y-%m-%d')
                notification_list[idx]['category'] = convert_to_string(NOTIFICATION_CATEGORY, notification['category'])
                notification_list[idx]['member_category'] = convert_to_string(MEMBER_CATEGORY, notification['member_category'])
                notification_list[idx]['day'] = convert_to_string(DAY_CATEGORY, notification['day'])

                # DB에서 알림 대상자 목록 가져오기
                sql = f"SELECT user_id FROM notification_member WHERE notification_id = {notification['id']};"
                member_list = database.execute(sql)
                notification_list[idx]['member_list'] = member_list
            
            database.close()
            return notification_list, 200
    
    # 알림 정보 추가
    def post(self, category):
        # Body 데이터 읽어오기
        notification = request.get_json()
        
        # category, day를 문자열로 변환
        notification['category'] = convert_to_index(NOTIFICATION_CATEGORY, notification['category'])
        notification['member_category'] = convert_to_index(MEMBER_CATEGORY, notification['member_category'])
        notification['day'] = convert_to_index(DAY_CATEGORY, notification['day'])
        database = Database()

        # 알림 정보를 DB에 추가
        sql = "INSERT INTO notification "\
            f"VALUES(NULL, {notification['category']}, {notification['member_category']}, '{notification['time']}', "\
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
    # 알림 정보 수정
    def put(self, notification_id):
        # Body 데이터 읽어오기
        notification = request.get_json()

        # category, day를 index로 변환
        notification['category'] = convert_to_index(NOTIFICATION_CATEGORY, notification['category'])
        notification['member_category'] = convert_to_index(MEMBER_CATEGORY, notification['member_category'])
        notification['day'] = convert_to_index(DAY_CATEGORY, notification['day'])

        database = Database()

        # 수정된 알림 정보를 DB에 반영
        sql = "UPDATE notification SET "\
            f"category = {notification['category']}, member_category = {notification['member_category']}, time = '{notification['time']}', "\
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

    # 알림 정보 삭제
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
    
@notification.route('/members')
class NotificationMemberAPI(Resource):
    # 회원 목록 얻기
    def get(self):
        # DB에서 회원 목록 불러오기
        database = Database()
        sql = "SELECT id, name, grade FROM users;"
        member_list = database.execute_all(sql)
        database.close()
        return member_list, 200

@notification.route('/payment-period')
class NotificationPaymentPeriodAPI(Resource):
    # 전체 월별 회비 기간 얻기
    def get(self):

        # 금월 및 작년 6월 날짜 문자열로 얻기
        current_month = date(datetime.today().year, datetime.today().month, 1).strftime('%Y-%m-%d')
        start_month = date(datetime.today().year - 1, 6, 1).strftime('%Y-%m-%d')

        # DB에서 월별 회비 납부 기간 불러오기
        database = Database()
        sql = f"SELECT date, start_date, end_date FROM monthly_payment_periods "\
            f"WHERE date between '{start_month}' and '{current_month}' "\
            f"ORDER BY date;"
        payment_period_list = database.execute_all(sql)
        database.close()

        if not payment_period_list: # 납부 기간이 없을 때 처리
            return {}, 200
        else:
            # 납부 기간 내역의 날짜 데이터들을 문자열로 변경
            for idx, payment_period in enumerate(payment_period_list):
                payment_period_list[idx]['date'] = payment_period['date'].strftime('%Y-%m-%d')
                payment_period_list[idx]['start_date'] = payment_period['start_date'].strftime('%Y-%m-%d')
                payment_period_list[idx]['end_date'] = payment_period['end_date'].strftime('%Y-%m-%d')
            
            return payment_period_list, 200