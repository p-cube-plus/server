from flask import Flask, request
from flask_restx import Resource, Namespace
from database.database import Database
from utils.dto import AdminAttendanceDTO
from flask_jwt_extended import jwt_required, get_jwt_identity
from utils.enum_tool import AttendanceEnum, UserEnum
from utils.aes_cipher import AESCipher
from utils.api_access_level_tool import api_access_level

attendance = AdminAttendanceDTO.api

@attendance.route('/all')
class AttendanceListAPI(Resource):
    @attendance.response(200, 'OK', [AdminAttendanceDTO.model_attendance_info])
    @attendance.response(400, 'Bad Request', AdminAttendanceDTO.response_message)
    @attendance.doc(security='apiKey')
    @api_access_level(2)
    def get(self):
        # DB 예외 처리
        try:
            # DB에서 전체 attendance 목록을 날짜 순으로 가져오기
            database = Database()
            sql = "SELECT id, category, date, first_auth_start_time, first_auth_end_time, "\
                  "second_auth_start_time, second_auth_end_time FROM attendance ORDER BY date;"
            attendance_list = database.execute_all(sql)
        except Exception as e:
            return {'message': '서버에 오류가 발생했어요 :(\n지속적으로 발생하면 문의주세요!', 'error': str(e)}, 400
        finally:
            database.close()

        # 데이터를 적절히 문자열로 변환
        for attendance in attendance_list:
            attendance['category'] = AttendanceEnum.Category(attendance['category'])
            attendance['date'] = attendance['date'].strftime('%Y-%m-%d')
            attendance['first_auth_start_time'] = str(attendance['first_auth_start_time'])
            attendance['first_auth_end_time'] = str(attendance['first_auth_end_time'])
            attendance['second_auth_start_time'] = str(attendance['second_auth_start_time'])
            attendance['second_auth_end_time'] = str(attendance['second_auth_end_time'])

        return attendance_list, 200


@attendance.route("")
class AttendanceInfoAPI(Resource):
    # category, date에 따른 출석 정보 얻기
    @attendance.expect(AdminAttendanceDTO.query_date_and_category, validate=True)
    @attendance.response(200, 'OK', AdminAttendanceDTO.model_attendance)
    @attendance.response(400, 'Bad Request', AdminAttendanceDTO.response_message)   
    @attendance.doc(security='apiKey')
    @api_access_level(2)
    def get(self):
        # Query Parameter 데이터 읽어오기
        category = AttendanceEnum.Category(request.args['category'])
        date = request.args['date']

        # DB 예외 처리
        try:
            # DB에서 category, date값에 맞는 출석 정보 가져오기
            database = Database()
            sql = "SELECT id, first_auth_start_time, first_auth_end_time, "\
                  "second_auth_start_time, second_auth_end_time FROM attendance "\
                  "WHERE category = %s and date = %s;"
            attendance = database.execute_one(sql, (category, date))
        except Exception as e:
            return {'message': '서버에 오류가 발생했어요 :(\n지속적으로 발생하면 문의주세요!', 'error': str(e)}, 400
        finally:
            database.close()

        # 출석 정보가 존재할 때 처리
        if attendance:
            # time을 문자열로 변환
            attendance['first_auth_start_time'] = str(attendance['first_auth_start_time'])
            attendance['first_auth_end_time'] = str(attendance['first_auth_end_time'])
            attendance['second_auth_start_time'] = str(attendance['second_auth_start_time'])
            attendance['second_auth_end_time'] = str(attendance['second_auth_end_time'])

        return attendance, 200
    
    # 출석 정보 추가
    @attendance.expect(AdminAttendanceDTO.model_attendance_without_id, validate=True)
    @attendance.response(200, 'OK', AdminAttendanceDTO.response_message)
    @attendance.response(400, 'Bad Request', AdminAttendanceDTO.response_message)
    @attendance.doc(security='apiKey')
    @api_access_level(2)
    def post(self):
        # Body 데이터 읽어오기
        attendance = request.get_json()

        # category를 index로 변환
        attendance['category'] = AttendanceEnum.Category(attendance['category'])

        # DB 예외 처리
        try:
            # 출석 정보 DB에 추가
            database = Database()
            sql = "INSERT INTO attendance VALUES(NULL, %s, %s, %s, %s, %s, %s)"
            values = (
                attendance['category'],
                attendance['date'],
                attendance['first_auth_start_time'],
                attendance['first_auth_end_time'],
                attendance['second_auth_start_time'],
                attendance['second_auth_end_time']
            )
            database.execute(sql, values)
            database.commit()
        except Exception as e:
            return {'message': '서버에 오류가 발생했어요 :(\n지속적으로 발생하면 문의주세요!', 'error': str(e)}, 400
        finally:
            database.close()

        return {'message': '출석 정보를 추가했어요 :)'}, 200

    # 출석 정보 수정
    @attendance.expect(AdminAttendanceDTO.model_attendance, validate=True)
    @attendance.response(200, 'OK', AdminAttendanceDTO.response_message)
    @attendance.response(400, 'Bad Request', AdminAttendanceDTO.response_message)
    @attendance.doc(security='apiKey')
    @api_access_level(2)
    def put(self):
        # Body 데이터 읽어오기
        attendance = request.get_json()

        # DB 예외처리
        try:
            # 수정된 출석 정보를 DB에 반영
            database = Database()
            sql = "UPDATE attendance SET "\
                "date = %s, "\
                "first_auth_start_time = %s, first_auth_end_time = %s, "\
                "second_auth_start_time = %s, second_auth_end_time = %s "\
                "WHERE id = %s"
            values = (
                attendance['date'],
                attendance['first_auth_start_time'],
                attendance['first_auth_end_time'],
                attendance['second_auth_start_time'],
                attendance['second_auth_end_time'],
                attendance['id']
            )
            database.execute(sql, values)
            database.commit()
        except Exception as e:
            return {'message': '서버에 오류가 발생했어요 :(\n지속적으로 발생하면 문의주세요!', 'error': str(e)}, 400
        finally:
            database.close()

        return {'message': '출석 정보를 수정했어요 :)'}, 200

    
    # 출석 정보 삭제
    @attendance.expect(AdminAttendanceDTO.query_raw_attendance_id, validate=True)
    @attendance.response(200, 'OK', AdminAttendanceDTO.response_message)
    @attendance.response(400, 'Bad Request', AdminAttendanceDTO.response_message)
    @attendance.doc(security='apiKey')
    @api_access_level(2)
    def delete(self):
        id = request.args['id']
        # DB 예외처리
        try:
            database = Database()

            # 회원 출석 정보 삭제
            sql = "DELETE FROM user_attendance WHERE attendance_id = %s;"
            database.execute(sql, (id,))

            # 출석 정보 삭제
            sql = "DELETE FROM attendance WHERE id = %s;"
            database.execute(sql, (id,))

            database.commit()
        except Exception as e:
            return {'message': '서버에 오류가 발생했어요 :(\n지속적으로 발생하면 문의주세요!', 'error': str(e)}, 400
        finally:
            database.close()

        return {'message': '출석 정보를 삭제했어요 :)'}, 200
 
@attendance.route('/user/all')
class AttendanceUserListAPI(Resource):
    # 회원 목록 얻기
    @attendance.expect(AdminAttendanceDTO.query_attendance_id, validate=True)
    @attendance.response(200, 'OK', [AdminAttendanceDTO.model_admin_attendance_user])
    @attendance.response(400, 'Bad Request', AdminAttendanceDTO.response_message)
    @attendance.doc(security='apiKey')
    @api_access_level(2)
    def get(self):
        # Query Parameter 데이터 읽어오기
        attendance_id = request.args['attendance_id']

        # DB 예외 처리
        try:
            # DB에서 회원 목록 불러오기
            database = Database()
            sql = "SELECT u.id, u.name, u.grade, u.part_index, u.rest_type, ua.first_auth_time, ua.second_auth_time, ua.state FROM users u LEFT JOIN user_attendance ua "\
                  "ON u.id = ua.user_id WHERE ua.attendance_id = %s;"
            user_list = database.execute_all(sql, (attendance_id,))

            # 회원 이름 복호화
            cript = AESCipher()
            for idx, user in enumerate(user_list):
                user_list[idx]['name'] = cript.decrypt(user['name'])
        except Exception as e:
            return {'message': '서버에 오류가 발생했어요 :(\n지속적으로 발생하면 문의주세요!', 'error': str(e)}, 400
        finally:
            database.close()

        if not user_list: # 회원이 존재하지 않을 경우 처리
            return [], 200
        else:
            # index 및 time을 문자열로 변환
            for idx, user in enumerate(user_list):
                user_list[idx]['part_index'] = UserEnum.Part(user['part_index'])
                user_list[idx]['part'] = user.pop('part_index')
                user_list[idx]['rest_type'] = UserEnum.RestType(user['rest_type'])
                user_list[idx]['state'] = AttendanceEnum.UserAttendanceState(user['state'])
                user_list[idx]['first_auth_time'] = str(user['first_auth_time'])
                user_list[idx]['second_auth_time'] = str(user['second_auth_time'])

            return user_list, 200
    
@attendance.route('/user')
class AttendanceUserAPI(Resource):
    # 회원 출석 정보 얻기
    @attendance.expect(AdminAttendanceDTO.query_ids, validate=True)
    @attendance.response(200, 'OK', AdminAttendanceDTO.model_user_attendance)
    @attendance.response(400, 'Bad Request', AdminAttendanceDTO.response_message)
    @attendance.doc(security='apiKey')
    @api_access_level(2)
    def get(self):
        # Query Parameter 데이터 읽어오기
        attendance_id = request.args['attendance_id']
        user_id = request.args['user_id']

        # DB 예외처리
        try:
            # DB에서 회원 출석 정보 불러오기
            database = Database()
            sql = "SELECT * FROM user_attendance WHERE attendance_id = %s and user_id = %s;"
            user_attendance = database.execute_one(sql, (attendance_id, user_id))
        except Exception as e:
            return {'message': '서버에 오류가 발생했어요 :(\n지속적으로 발생하면 문의주세요!', 'error': str(e)}, 400
        finally:
            database.close()

        # 회원 출석 정보가 존재할 시 처리
        if user_attendance:
            # 회원 출석 state, 출석 인증 시간을 문자열로 변경
            user_attendance['state'] = AttendanceEnum.UserAttendanceState(user_attendance['state'])
            user_attendance['first_auth_time'] = str(user_attendance['first_auth_time'])
            user_attendance['second_auth_time'] = str(user_attendance['second_auth_time'])
        
        return user_attendance, 200

    @attendance.expect(AdminAttendanceDTO.model_user_attendance, validate=True)
    @attendance.response(200, 'OK', AdminAttendanceDTO.response_message)
    @attendance.response(400, 'Bad Request', AdminAttendanceDTO.response_message)
    @attendance.doc(security='apiKey')
    @api_access_level(2)
    def put(self):
        # Body 데이터 읽어오기
        user_attendance = request.get_json()

        # 회원 출석 state를 index로 변경
        user_attendance['state'] = AttendanceEnum.UserAttendanceState(user_attendance['state'])

        # DB 예외처리
        try:
            # 수정된 회원 출석 정보를 DB에 반영
            database = Database()
            sql = "INSERT INTO user_attendance (attendance_id, user_id, state, first_auth_time, second_auth_time) VALUES(%s, %s, %s, %s, %s) "\
                  "ON DUPLICATE KEY UPDATE state = %s, first_auth_time = %s, second_auth_time = %s;"
            values = (
                user_attendance['attendance_id'],
                user_attendance['user_id'],
                user_attendance['state'],
                user_attendance['first_auth_time'],
                user_attendance['second_auth_time'],
                user_attendance['state'],
                user_attendance['first_auth_time'],
                user_attendance['second_auth_time']
            )
            database.execute(sql, values)
            database.commit()
        except Exception as e:
            return {'message': '서버에 오류가 발생했어요 :(\n지속적으로 발생하면 문의주세요!', 'error': str(e)}, 400
        finally:
            database.close()

        return {'message': '유저 출석 정보를 수정했어요 :)'}, 200
