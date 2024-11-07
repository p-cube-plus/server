from flask import Flask, request
from flask_restx import Resource, Namespace
from flask_jwt_extended import jwt_required, get_jwt_identity
from database.database import Database
from utils.dto import HomeDTO
from datetime import datetime, date, timedelta
from calendar import monthcalendar
from utils.api_access_level_tool import api_access_level

def get_meeting_weekdays(month_calendar, weekday):
    dates = []
    for week in month_calendar:
        if week[weekday] != 0:
            dates.append(week[weekday])
    return dates

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

            sql = "SELECT * FROM schedule WHERE title LIKE %s AND start_date >= CURDATE() ORDER BY start_date;"
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

@home.route('/schedule/upcoming')
@home.response(200, 'Success', [HomeDTO.model_home_schedule])
@home.response(401, 'Unauthorized')
class HomeScheduleUpcomingAPI(Resource):
    @home.doc(security='apiKey')
    @api_access_level(1)
    def get(self):
        today = datetime.today().date()

        week_dates = []
        for i in range(7):
            week_dates.append(today + timedelta(days=i))

        end_date = week_dates[-1]

        try:
            database = Database()

            sql = "SELECT * FROM schedule WHERE start_date BETWEEN %s AND %s ORDER BY start_date, start_time;"
            values = (today, end_date)
            schedule_list = database.execute_all(sql, values)

            sql = "SELECT id, type, title, day, time FROM meeting ORDER BY day, time;"
            meeting_list = database.execute_all(sql)
        except Exception as e:
            return {'message': '서버에 오류가 발생했어요 :(\n지속적으로 발생하면 문의주세요!', 'error': str(e)}, 400
        finally:
            database.close()

        for meeting in meeting_list:
            if meeting['day'] < today.weekday():
                day_index = 7 - today.weekday() + meeting['day']
            else:
                day_index = meeting['day'] - today.weekday()
            meeting['start_date'] = week_dates[day_index]
            meeting['start_time'] = meeting['time']
            meeting['end_date'] = None
            meeting['end_time'] = None
            meeting.pop('day')
            meeting.pop('time')
        
        upcoming_list = list(meeting_list) + list(schedule_list)
        upcoming_list.sort(key=lambda x: (x['start_date'], x['start_time']))

        for schedule in upcoming_list:
            schedule['start_date'] = schedule['start_date'].strftime('%Y-%m-%d')
            if schedule['end_date']:
                schedule['end_date'] = schedule['end_date'].strftime('%Y-%m-%d')
            if schedule['start_time']:
                schedule['start_time'] = (datetime.min + schedule['start_time']).strftime('%H:%M')
            if schedule['end_time']:
                schedule['end_time'] = (datetime.min + schedule['end_time']).strftime('%H:%M')

        return upcoming_list, 200

@home.route('/schedule/all')
@home.expect(HomeDTO.query_home_schedule_year_and_month, validate=True)
@home.response(200, 'Success', [HomeDTO.model_home_schedule])
@home.response(401, 'Unauthorized')
class HomeScheduleAllAPI(Resource):
    @home.doc(security='apiKey')
    @api_access_level(1)
    def get(self):
        year = int(request.args['year'])
        month = int(request.args['month'])

        start_date = date(year, month, 1)
        end_date = date(year, month + 1 if month != 12 else 1, 1) - timedelta(days=1)

        try:
            database = Database()

            sql = "SELECT * FROM schedule WHERE start_date BETWEEN %s AND %s ORDER BY start_date, start_time;"
            values = (start_date, end_date)
            schedule_list = database.execute_all(sql, values)

            sql = "SELECT id, type, title, day, time FROM meeting ORDER BY day, time;"
            meeting_list = database.execute_all(sql)
        except Exception as e:
            return {'message': '서버에 오류가 발생했어요 :(\n지속적으로 발생하면 문의주세요!', 'error': str(e)}, 400
        finally:
            database.close()

        monthly_list = []
        month_calendar = monthcalendar(year, month)

        for meeting in meeting_list:
            meeting['start_date'] = None
            meeting['start_time'] = meeting['time']
            meeting['end_date'] = None
            meeting['end_time'] = None
            meeting_weekdays = get_meeting_weekdays(month_calendar, meeting['day'])
            meeting.pop('time')
            meeting.pop('day')

            for meeting_weekday in meeting_weekdays:
                meeting['start_date'] = date(year, month, meeting_weekday)
                monthly_list.append(meeting.copy())
            
        monthly_list += list(schedule_list)
        monthly_list.sort(key=lambda x: (x['start_date'], x['start_time']))

        for schedule in monthly_list:
            schedule['start_date'] = schedule['start_date'].strftime('%Y-%m-%d')
            if schedule['end_date']:
                schedule['end_date'] = schedule['end_date'].strftime('%Y-%m-%d')
            if schedule['start_time']:
                schedule['start_time'] = (datetime.min + schedule['start_time']).strftime('%H:%M')
            if schedule['end_time']:
                schedule['end_time'] = (datetime.min + schedule['end_time']).strftime('%H:%M')

        return monthly_list, 200


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
