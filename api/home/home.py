from flask import Flask, request
from flask_restx import Resource, Namespace
from flask_jwt_extended import jwt_required, get_jwt_identity
from database.database import Database
from utils.dto import HomeDTO
from datetime import datetime, timedelta
from utils.api_access_level_tool import api_access_level

home = HomeDTO.api

@home.route('/attendance')
@home.response(200, 'Success')
@home.response(401, 'Unauthorized')
class HomeAttendanceAPI(Resource):
    @home.doc(security='apiKey')
    @api_access_level(1)
    def get(self):
        try:
            database = Database()

            sql = "SELECT * FROM schedules WHERE title LIKE %s AND start_date >= CURDATE() ORDER BY start_date;"
            values = ("%회의%",)
            meeting_list = database.execute_all(sql, values)
        except Exception as e:
            return {'message': '서버에 오류가 발생했어요 :(\n지속적으로 발생하면 문의주세요!', 'error': str(e)}, 400
        finally:
            database.close()

        if not meeting_list:
            return [], 200
        else:
            for meeting in meeting_list:
                meeting['start_date'] = meeting['start_date'].strftime('%Y-%m-%d')
                meeting['start_time'] = (datetime.min + meeting['start_time']).strftime('%H:%M')

            return meeting_list, 200

@home.route('/schedule')
@home.response(200, 'Success', HomeDTO.model_schedule_info)
@home.response(401, 'Unauthorized')
class HomeScheduleAPI(Resource):
    @home.doc(security='apiKey')
    @api_access_level(1)
    def get(self):
        try:
            database = Database()

            sql = "SELECT * FROM schedules ORDER BY start_date;"
            schedule_list = database.execute_all(sql)
        except Exception as e:
            return {'message': '서버에 오류가 발생했어요 :(\n지속적으로 발생하면 문의주세요!', 'error': str(e)}, 400
        finally:
            database.close()

        if not schedule_list:
            return {'all_list': schedule_list, 'upcoming_list': []}, 200
        else:
            upcoming_list = []
            today = datetime.today().date()
            limit_day = today + timedelta(days=7)
            for idx, schedule in enumerate(schedule_list):
                if schedule['start_date'] >= today and schedule['start_date'] <= limit_day:
                    upcoming_list.append(schedule)
                schedule_list[idx]['start_date'] = schedule['start_date'].strftime('%Y-%m-%d')
                if schedule['end_date']:
                    schedule_list[idx]['end_date'] = schedule['end_date'].strftime('%Y-%m-%d')
                if schedule['start_time']:
                    schedule_list[idx]['start_time'] = (datetime.min + schedule['start_time']).strftime('%H:%M')

        return {'all_list': schedule_list, 'upcoming_list': upcoming_list}, 200

@home.route('/product')
@home.response(200, 'Success')
@home.response(401, 'Unauthorized')
class HomeProductAPI(Resource):
    @home.doc(security='apiKey')
    @api_access_level(1)
    @jwt_required()
    def get(self):
        user_id = get_jwt_identity()

        try:
            database = Database()

            sql = """
                SELECT p.category, rl.rent_day, datediff(rl.deadline, now()) as d_day
                FROM rent_list rl 
                JOIN products p ON rl.product_code = p.code 
                WHERE rl.user_id = %s AND rl.return_day IS NULL 
                ORDER BY d_day;
            """
            values = (user_id,)
            rent_product_list = database.execute_all(sql, values)
        except Exception as e:
            return {'message': '서버에 오류가 발생했어요 :(\n지속적으로 발생하면 문의주세요!', 'error': str(e)}, 400
        finally:
            database.close()

        if not rent_product_list:
            return [], 200
        else:
            for idx, rent_product in enumerate(rent_product_list):
                rent_product_list[idx]['rent_day'] = rent_product['rent_day'].strftime('%Y-%m-%d')

            return rent_product_list, 200
