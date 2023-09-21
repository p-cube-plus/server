from flask import Flask, request
from flask_restx import Resource, Namespace
from database.database import Database
from datetime import datetime, date
from flask_jwt_extended import jwt_required, get_jwt_identity

home = Namespace('home')

@home.route('/attendance')
@home.response(200, 'Success')
@home.response(401, 'Unauthorized')
class HomeAttendanceAPI(Resource):
    # 예정된 회의 정보 얻기
    @home.doc(security='apiKey')
    @jwt_required()
    def get(self):
        database = Database()

        # DB에서 예정된 회의 찾기
        sql = "SELECT * FROM schedules "\
            "WHERE title like '%%회의%%' AND start_date >= CURDATE() "\
            "ORDER BY start_date;"
        
        meeting_list = database.execute_all(sql)
        database.close()

        if not meeting_list: # 예정된 회의가 없는 경우
            return [], 200
        else:
            # date 및 time을 문자열로 변경
            for meeting in meeting_list:
                meeting['start_date'] = meeting['start_date'].strftime('%Y-%m-%d')
                meeting['start_time'] = (datetime.min + meeting['start_time']).strftime('%H:%M')

            return meeting_list, 200

@home.route('/schedule')
@home.response(200, 'Success')
@home.response(401, 'Unauthorized')
class HomeScheduleAPI(Resource):
    # 예정된 일정 목록 얻기
    @home.doc(security='apiKey')
    @jwt_required()
    def get(self):
        database = Database()

        # DB에서 일정 찾기
        sql = "SELECT * FROM schedules ORDER BY start_date;"

        schedule_list = database.execute_all(sql)
        database.close()

        if not schedule_list: # 예정된 일정이 없는 경우
            return [], 200
        else:
            for idx, schedule in enumerate(schedule_list):
                # date 및 category를 문자열로 변환
                schedule_list[idx]['start_date'] = schedule['start_date'].strftime('%Y-%m-%d')
                if schedule['end_date']:
                    schedule_list[idx]['end_date'] = schedule['end_date'].strftime('%Y-%m-%d')
                if schedule['start_time']:
                    schedule_list[idx]['start_time'] = (datetime.min + schedule['start_time']).strftime('%H:%M')

        return schedule_list, 200

@home.route('/product')
@home.response(200, 'Success')
@home.response(401, 'Unauthorized')
class HomeProductAPI(Resource):
    # DB에서 user_id에 따른 물품 대여 목록 얻기
    @home.doc(security='apiKey')
    @jwt_required()
    def get(self):
        database = Database()
        user_id = get_jwt_identity()

        # user_id에 따른 물품 대여 목록 얻기 및 D-day 계산
        sql = "SELECT p.category, rl.rent_day, datediff(rl.deadline, now()) as d_day "\
            "FROM rent_list rl JOIN products p on rl.product_code = p.code "\
            f"WHERE rl.user_id = '{user_id}' and rl.return_day is NULL "\
            "ORDER BY d_day;"
        
        rent_product_list = database.execute_all(sql)
        database.close()

        if not rent_product_list: # 물품 대여 목록이 없는 경우
            return [], 200
        else:
            for idx, rent_product in enumerate(rent_product_list):
                # date를 문자열로 변환
                rent_product_list[idx]['rent_day'] = rent_product['rent_day'].strftime('%Y-%m-%d')

            return rent_product_list, 200
