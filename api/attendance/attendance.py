from flask import Flask, request
from flask_restx import Resource, Namespace
from database.database import Database
from datetime import datetime, date
from utils.dto import AttendanceDTO

attendance = AttendanceDTO.api

# 출석 category
ATTENDANCE_CATEGORY = {0: '디자인', 1: '아트', 2: '프로그래밍', 3: '정기', 4: '기타'}

# 유저 출석 state
USER_ATTENDANCE_STATE = {0: '출석', 1: '지각', 2: '불참'}

# index 데이터를 문자열로 변경
def convert_to_string(dictionary, index):
    return dictionary.get(index, None)

# 문자열 데이터를 index로 변경
def convert_to_index(dictionary, string):
    for key, value in dictionary.items():
        if value == string:
            return key
    return None

@attendance.route('/<int:attendance_id>')
class AttendanceUserAPI(Resource):
    # user_id에 따른 출석 정보 얻기
    @attendance.expect(AttendanceDTO.query_user_id, validate=True)
    @attendance.response(200, 'OK', AttendanceDTO.response_data_with_code)
    @attendance.response(400, 'Bad Request', AttendanceDTO.response_message_with_code)
    def get(self, attendance_id):
        # 추후 토큰으로 대신할 예정
        user_id = request.args['user_id']

        # DB 예외처리
        try:
            database = Database()

            # DB에서 출석 ID에 맞는 출석 정보 불러오기
            sql = "SELECT a.id as attendance_id, a.category, a.date, a.first_auth_start_time, a.first_auth_end_time, "\
                "a.second_auth_start_time, a.second_auth_end_time, ua.state, ua.first_auth_time, ua.second_auth_time "\
                f"FROM attendance a LEFT JOIN user_attendance ua ON a.id = ua.attendance_id and ua.user_id = '{user_id}' "\
                f"WHERE a.id = {attendance_id};"
            attendance = database.execute_one(sql)

            if not attendance:
                return {'message': '출석 정보가 존재하지 않아요 :('}, 200

            # DB에서 최근 4번의 출석 기록 불러오기
            sql = "SELECT a.date, ua.state FROM user_attendance ua JOIN attendance a ON ua.attendance_id = a.id "\
                f"WHERE ua.user_id = '{user_id}' and a.category = {attendance['category']} ORDER BY a.date DESC LIMIT 4;"
            record_list = database.execute_all(sql)
        except:
            return {'message': '데이터베이스 오류가 발생했어요 :('}, 400
        finally:
            database.close()

        # date를 문자열로 변환 
        for idx, record in enumerate(record_list):
            record_list[idx]['date'] = record['date'].strftime('%Y-%m-%d')
        
        record_list.extend([None] * (4 - len(record_list)))

        # date, time, category, state를 문자열로 변환
        attendance['date'] = attendance['date'].strftime('%Y-%m-%d')
        attendance['first_auth_start_time'] = str(attendance['first_auth_start_time'])
        attendance['first_auth_end_time'] = str(attendance['first_auth_end_time'])
        attendance['second_auth_start_time'] = str(attendance['second_auth_start_time'])
        attendance['second_auth_end_time'] = str(attendance['second_auth_end_time'])        
        attendance['first_auth_time'] = str(attendance['first_auth_time'])
        attendance['second_auth_time'] = str(attendance['second_auth_time'])
        attendance['category'] = convert_to_string(ATTENDANCE_CATEGORY, attendance['category'])
        attendance['state'] = convert_to_string(USER_ATTENDANCE_STATE, attendance['state'])

        return {'attendance': attendance, 'record_list': record_list}, 200
    
    # 회원의 출석 인증 정보 수정
    @attendance.expect(AttendanceDTO.model_user_attendance, validate=True)
    @attendance.response(200, 'OK', AttendanceDTO.response_message_with_code)
    @attendance.response(400, 'Bad Request', AttendanceDTO.response_message_with_code)
    def put(self, attendance_id):
        # Body 데이터 읽어오기
        user_attendance = request.get_json()

        # 회원 출석 state를 index로 변경
        user_attendance['state'] = convert_to_index(USER_ATTENDANCE_STATE, user_attendance['state'])

        # DB 예외처리
        try:
            # 수정된 회원 출석 정보를 DB에 반영
            database = Database()

            sql = "INSERT INTO user_attendance (attendance_id, user_id, state, first_auth_time, second_auth_time) VALUES(%s, %s, %s, %s, %s) "\
                "ON DUPLICATE KEY UPDATE state = %s, first_auth_time = %s, second_auth_time = %s;"
            
            value = (attendance_id, user_attendance['user_id'], user_attendance['state'], user_attendance['first_auth_time'], user_attendance['second_auth_time'], 
                    user_attendance['state'], user_attendance['first_auth_time'], user_attendance['second_auth_time'])
            
            database.execute(sql, value)
            database.commit()
        except:
            return {'message': '데이터베이스 오류가 발생했어요 :('}, 400
        finally:
            database.close()

        return {'message': '회원의 출석 인증 정보를 수정했어요 :)'}, 200