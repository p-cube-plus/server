from flask import Flask, request
from flask_restx import Resource, Namespace
from database.database import Database
from utils.dto import AdminAttendanceDTO
from flask_jwt_extended import jwt_required, get_jwt_identity
from utils.enum_tool import convert_to_string, convert_to_index, AttendanceEnum, UserEnum
from utils.aes_cipher import AESCipher

attendance = AdminAttendanceDTO.api

@attendance.route("/category/<int:category>")
class AttendanceInfoAPI(Resource):
    # category, date에 따른 출석 정보 얻기
    @attendance.expect(AdminAttendanceDTO.query_date, validate=True)
    @attendance.response(200, 'OK', AdminAttendanceDTO.response_attendance)
    @attendance.response(400, 'Bad Request', AdminAttendanceDTO.response_message)
    @attendance.doc(security='apiKey')
    @jwt_required()
    def get(self, category):
        # Query Parameter 데이터 읽어오기
        date = request.args['date']

        # DB 예외 처리
        try:
            # DB에서 category, date값에 맞는 출석 정보 가져오기
            database = Database()
            sql = f"SELECT * FROM attendance WHERE category = {category} and date = '{date}';"
            attendance = database.execute_one(sql)
        except:
            return {'message': '서버에 오류가 발생했어요 :(\n지속적으로 발생하면 문의주세요!'}, 400
        finally:
            database.close()

        # 출석 정보가 존재할 때 처리
        if attendance:
            # date, time을 문자열로 변환
            attendance['date'] = attendance['date'].strftime('%Y-%m-%d')
            attendance['first_auth_start_time'] = str(attendance['first_auth_start_time'])
            attendance['first_auth_end_time'] = str(attendance['first_auth_end_time'])
            attendance['second_auth_start_time'] = str(attendance['second_auth_start_time'])
            attendance['second_auth_end_time'] = str(attendance['second_auth_end_time'])

        return attendance, 200
    
    # 출석 정보 수정
    @attendance.expect(AdminAttendanceDTO.model_attendance, validate=True)
    @attendance.response(200, 'OK', AdminAttendanceDTO.response_message)
    @attendance.response(400, 'Bad Request', AdminAttendanceDTO.response_message)
    @attendance.doc(security='apiKey')
    @jwt_required()
    def put(self, category):
        # Body 데이터 읽어오기
        attendance = request.get_json()

        # DB 예외처리
        try:
            # 수정된 출석 정보를 DB에 반영
            database = Database()
            sql = "UPDATE attendance SET "\
                f"category = {category}, date = '{attendance['date']}', "\
                f"first_auth_start_time = '{attendance['first_auth_start_time']}', first_auth_end_time = '{attendance['first_auth_end_time']}', "\
                f"second_auth_start_time = '{attendance['second_auth_start_time']}', second_auth_end_time = '{attendance['second_auth_end_time']}' "\
                f"WHERE id = {attendance['id']}"
            database.execute(sql)
            database.commit()
        except:
            return {'message': '서버에 오류가 발생했어요 :(\n지속적으로 발생하면 문의주세요!'}, 400
        finally:
            database.close()

        return {'message': '출석 정보를 수정했어요 :)'}, 200
 
@attendance.route('/users')
class AttendanceUserListAPI(Resource):
    # 회원 목록 얻기
    @attendance.expect(AdminAttendanceDTO.query_attendance_id, validate=True)
    @attendance.response(200, 'OK', [AdminAttendanceDTO.model_admin_attendance_user])
    @attendance.response(400, 'Bad Request', AdminAttendanceDTO.response_message)
    @attendance.doc(security='apiKey')
    @jwt_required()
    def get(self):
        # Query Parameter 데이터 읽어오기
        attendance_id = request.args['attendance_id']

        # DB 예외 처리
        try:
            # DB에서 회원 목록 불러오기
            database = Database()
            sql = "SELECT u.id, u.name, u.grade, u.part_index, u.rest_type, ua.first_auth_time, ua.second_auth_time, ua.state FROM users u LEFT JOIN user_attendance ua "\
                f"ON u.id = ua.user_id WHERE ua.attendance_id = {attendance_id};"
            user_list = database.execute_all(sql)

            # 회원 이름 복호화
            cript = AESCipher()
            for idx, user in enumerate(user_list):
                user_list[idx]['name'] = cript.decrypt(user['name'])
        except:
            return {'message': '서버에 오류가 발생했어요 :(\n지속적으로 발생하면 문의주세요!'}, 400
        finally:
            database.close()

        if not user_list: # 회원이 존재하지 않을 경우 처리
            return [], 200
        else:
            # index 및 time을 문자열로 변환
            for idx, user in enumerate(user_list):
                user_list[idx]['part_index'] = convert_to_string(UserEnum.PART, user['part_index'])
                user_list[idx]['part'] = user.pop('part_index')
                user_list[idx]['rest_type'] = convert_to_string(UserEnum.REST_TYPE, user['rest_type'])
                user_list[idx]['state'] = convert_to_string(AttendanceEnum.CATEGORY, user['state'])
                user_list[idx]['first_auth_time'] = str(user['first_auth_time'])
                user_list[idx]['second_auth_time'] = str(user['second_auth_time'])
            return user_list, 200
    
@attendance.route('/user/<int:attendance_id>')
class AttendanceUserAPI(Resource):
    # 회원 출석 정보 얻기
    @attendance.expect(AdminAttendanceDTO.query_user_id, validate=True)
    @attendance.response(200, 'OK', AdminAttendanceDTO.model_user_attendance)
    @attendance.response(400, 'Bad Request', AdminAttendanceDTO.response_message)
    @attendance.doc(security='apiKey')
    @jwt_required()
    def get(self, attendance_id):
        # Query Parameter 데이터 읽어오기
        user_id = request.args['user_id']

        # DB 예외처리
        try:
            # DB에서 회원 출석 정보 불러오기
            database = Database()
            sql = f"SELECT * FROM user_attendance WHERE attendance_id = {attendance_id} and user_id = '{user_id}';"
            user_attendance = database.execute_one(sql)
        except:
            return {'message': '서버에 오류가 발생했어요 :(\n지속적으로 발생하면 문의주세요!'}, 400
        finally:
            database.close()

        # 회원 출석 정보가 존재할 시 처리
        if user_attendance:
            # 회원 출석 state, 출석 인증 시간을 문자열로 변경
            user_attendance['state'] = convert_to_string(AttendanceEnum.USER_ATTENDANCE_STATE, user_attendance['state'])
            user_attendance['first_auth_time'] = str(user_attendance['first_auth_time'])
            user_attendance['second_auth_time'] = str(user_attendance['second_auth_time'])
        
        return user_attendance, 200

    @attendance.expect(AdminAttendanceDTO.model_user_attendance, validate=True)
    @attendance.response(200, 'OK', AdminAttendanceDTO.response_message)
    @attendance.response(400, 'Bad Request', AdminAttendanceDTO.response_message)
    @attendance.doc(security='apiKey')
    @jwt_required()
    def put(self, attendance_id):
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
            value = (attendance_id, user_attendance['user_id'], user_attendance['state'], user_attendance['first_auth_time'], user_attendance['second_auth_time'], 
                    user_attendance['state'], user_attendance['first_auth_time'], user_attendance['second_auth_time'])
            database.execute(sql, value)
            database.commit()
        except:
            return {'message': '서버에 오류가 발생했어요 :(\n지속적으로 발생하면 문의주세요!'}, 400
        finally:
            database.close()

        return {'message': '유저 출석 정보를 수정했어요 :)'}, 200
