from flask import Flask, request
from flask_restx import Resource, Namespace
from database.database import Database
import datetime
from utils.dto import AttendanceDTO
from flask_jwt_extended import jwt_required, get_jwt_identity
from utils.enum_tool import convert_to_string, convert_to_index, AttendanceEnum

# 월별 n주차 계산
def get_week_of_month(date):
    first_day = datetime.date(date.year, date.month, 1)

    last_day = datetime.date(date.year, date.month + 1, 1) - datetime.timedelta(days=1)

    is_first_day_before_thursday = first_day.weekday() <= 3

    if is_same_week(date, first_day):
        if is_first_day_before_thursday:
            week_of_month = 1
        else:
            last_day_of_previous_month = datetime.date(date.year, date.month, 1) - datetime.timedelta(days=1)
            week_of_month = get_week_of_month(last_day_of_previous_month)
    else:
        if is_same_week(date, last_day):
            is_last_day_before_thursday = last_day.weekday() >= 3
            if is_last_day_before_thursday:
                week_of_month = week_of_month_for_simple(date) + (0 if is_first_day_before_thursday else -1)
            else:
                week_of_month = 1
        else:
            week_of_month = week_of_month_for_simple(date) + (0 if is_first_day_before_thursday else -1)

    return week_of_month

def is_same_week(date1, date2):
    return date1.isocalendar()[1] == date2.isocalendar()[1]

def week_of_month_for_simple(date):
    return (date.day - 1) // 7 + 1
    

attendance = AttendanceDTO.api

@attendance.route('/<int:attendance_id>')
class AttendanceUserAPI(Resource):
    # user_id에 따른 출석 정보 얻기
    @attendance.expect(AttendanceDTO.query_prev_attendance_count, validate=True)
    @attendance.response(200, 'OK', AttendanceDTO.response_data)
    @attendance.response(400, 'Bad Request', AttendanceDTO.response_message)
    @attendance.doc(security='apiKey')
    @jwt_required()
    def get(self, attendance_id):
        user_id = get_jwt_identity()

        # query parameter 읽어오기
        prev_attendance_count = int(request.args['prev_attendance_count'])

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
                f"WHERE ua.user_id = '{user_id}' AND a.category = {attendance['category']} AND a.date <= '{attendance['date']}' ORDER BY a.date DESC LIMIT {prev_attendance_count};"
            record_list = database.execute_all(sql)

        except:
            return {'message': '서버에 오류가 발생했어요 :(\n지속적으로 발생하면 문의주세요!'}, 400
        finally:
            database.close()

        # date를 문자열로 변환 
        for idx, record in enumerate(record_list):
            record_list[idx]['date'] = record['date'].strftime('%Y-%m-%d')

        print(record_list)
        
        record_list.extend([None] * (prev_attendance_count - len(record_list)))

        # date, time, category, state를 문자열로 변환
        attendance['date'] = attendance['date'].strftime('%Y-%m-%d')
        attendance['first_auth_start_time'] = str(attendance['first_auth_start_time'])
        attendance['first_auth_end_time'] = str(attendance['first_auth_end_time'])
        attendance['second_auth_start_time'] = str(attendance['second_auth_start_time'])
        attendance['second_auth_end_time'] = str(attendance['second_auth_end_time'])        
        attendance['first_auth_time'] = str(attendance['first_auth_time'])
        attendance['second_auth_time'] = str(attendance['second_auth_time'])
        attendance['category'] = convert_to_string(AttendanceEnum.CATEGORY, attendance['category'])
        attendance['state'] = convert_to_string(AttendanceEnum.USER_ATTENDANCE_STATE, attendance['state'])

        return {'attendance': attendance, 'record_list': record_list}, 200
    
    # 회원의 출석 인증 정보 수정
    @attendance.expect(AttendanceDTO.model_user_attendance, validate=True)
    @attendance.response(200, 'OK', AttendanceDTO.response_message)
    @attendance.response(400, 'Bad Request', AttendanceDTO.response_message)
    @attendance.doc(security='apiKey')
    @jwt_required()
    def put(self, attendance_id):
        user_id = get_jwt_identity()

        # Body 데이터 읽어오기
        user_attendance = request.get_json()

        # 회원 출석 state를 index로 변경
        user_attendance['state'] = convert_to_index(AttendanceEnum.USER_ATTENDANCE_STATE, user_attendance['state'])

        # DB 예외처리
        try:
            # 수정된 회원 출석 정보를 DB에 반영
            database = Database()

            sql = "INSERT INTO user_attendance (attendance_id, user_id, state, first_auth_time, second_auth_time) VALUES(%s, %s, %s, %s, %s) "\
                "ON DUPLICATE KEY UPDATE state = %s, first_auth_time = %s, second_auth_time = %s;"
            
            value = (attendance_id, user_id, user_attendance['state'], user_attendance['first_auth_time'], user_attendance['second_auth_time'], 
                    user_attendance['state'], user_attendance['first_auth_time'], user_attendance['second_auth_time'])
            
            database.execute(sql, value)
            database.commit()
        except:
            return {'message': '서버에 오류가 발생했어요 :(\n지속적으로 발생하면 문의주세요!'}, 400
        finally:
            database.close()

        return {'message': '회원의 출석 인증 정보를 수정했어요 :)'}, 200
    
@attendance.route('/detail')
class AttendanceDetailAPI(Resource):

    # 회원의 회의별 출석 기록 얻기
    @attendance.response(200, 'OK', [AttendanceDTO.model_record_list_by_category])
    @attendance.response(400, 'Bad Request', AttendanceDTO.response_message)
    @attendance.doc(security='apiKey')
    @jwt_required()
    def get(self):
        user_id = get_jwt_identity()
        
        # DB 예외처리
        try:
            # DB에서 출석 기록 불러오기
            database = Database()
            sql = f"SELECT a.category, a.date, ua.state FROM user_attendance ua JOIN attendance a ON ua.attendance_id = a.id AND "\
                f"ua.user_id = '{user_id}' ORDER BY a.category ASC, a.date DESC;"
            attendance_list = database.execute_all(sql)
        except:
            return {'message': '서버에 오류가 발생했어요 :(\n지속적으로 발생하면 문의주세요!'}, 400
        finally:
            database.close()

        # 회의별로 분류
        record_dictionary = {}

        for idx, attendance in enumerate(attendance_list):
            week_of_month = get_week_of_month(attendance['date'])

            attendance_list[idx]['date'] = attendance['date'].strftime('%Y-%m-%d')
            attendance_list[idx]['category'] = convert_to_string(AttendanceEnum.CATEGORY, attendance['category'])
            attendance_list[idx]['state'] = convert_to_string(AttendanceEnum.USER_ATTENDANCE_STATE, attendance['state'])

            if attendance['category'] not in record_dictionary:
                record_dictionary[attendance['category']] = []
            
            record_dictionary[attendance['category']].append({
                'date': attendance['date'],
                'week_of_month': week_of_month,
                'state': attendance['state']
            })

        # 형식 변환
        record_list = [{"category": key, "record_list": value} for key, value in record_dictionary.items()]

        return record_list, 200