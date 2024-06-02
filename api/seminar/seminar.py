from flask import Flask, request
from flask_restx import Resource, Namespace
from database.database import Database
from utils.dto import SeminarDTO
from flask_jwt_extended import jwt_required, get_jwt_identity
from utils.enum_tool import SeminarEnum
from utils.api_access_level_tool import api_access_level

seminar = SeminarDTO.api

@seminar.route('')
class SeminarUserAPI(Resource):
    # 회원의 세미나 목록 얻기
    @seminar.expect(SeminarDTO.query_user_id, validate=True)
    @seminar.response(200, 'OK', [SeminarDTO.model_seminar_with_id])
    @seminar.response(400, 'Bad Request', SeminarDTO.seminar_response_message)
    @seminar.doc(security='apiKey')
    @api_access_level(1)
    def get(self):
        user_id = request.args['user_id']

        # DB 예외 처리
        try:
            # DB에서 user_id값에 맞는 세미나 목록 불러오기
            database = Database()
            sql = "SELECT * FROM seminars WHERE user_id = %s;"
            values = (user_id,)
            seminar_list = database.execute_all(sql, values)
        except Exception as e:
            return {'message': '서버에 오류가 발생했어요 :(\n지속적으로 발생하면 문의주세요!', 'error': str(e)}, 400
        finally:
            database.close()

        if not seminar_list: # 세미나를 한 적이 없을 때 처리
            return [], 200
        else:
            for idx, seminar in enumerate(seminar_list):
                # date 및 category를 문자열로 변경
                seminar_list[idx]['date'] = seminar['date'].strftime('%Y-%m-%d')
                seminar_list[idx]['category'] = SeminarEnum.Category(seminar['category'])
            return seminar_list, 200
        
    # 세미나 정보 추가
    @seminar.expect(SeminarDTO.query_user_id, SeminarDTO.model_seminar, validate=True)
    @seminar.response(201, 'Created', SeminarDTO.seminar_response_message)
    @seminar.response(400, 'Bad Request', SeminarDTO.seminar_response_message)
    @seminar.doc(security='apiKey')
    @api_access_level(1)
    def post(self):
        user_id = request.args['user_id']

        # Body 데이터 읽어오기
        seminar = request.get_json()

        # category를 index로 변환
        seminar['category'] = SeminarEnum.Category(seminar['category'])

        # DB 예외 처리
        try:
            # 세미나 정보를 DB에 추가
            database = Database()
            sql = "INSERT INTO seminars (user_id, title, url, category, date) VALUES (%s, %s, %s, %s, %s);"
            values = (user_id, seminar['title'], seminar['url'], seminar['category'], seminar['date'])
            database.execute(sql, values)
            database.commit()
        except Exception as e:
            return {'message': '서버에 오류가 발생했어요 :(\n지속적으로 발생하면 문의주세요!', 'error': str(e)}, 400
        finally:
            database.close()

        return {'message': '세미나 정보를 추가했어요 :)'}, 201

    # 세미나 정보 수정
    @seminar.expect(SeminarDTO.query_user_id, SeminarDTO.model_seminar_with_id, validate=True)
    @seminar.response(200, 'OK', SeminarDTO.seminar_response_message)
    @seminar.response(400, 'Bad Request', SeminarDTO.seminar_response_message)
    @seminar.doc(security='apiKey')
    @api_access_level(1)
    def put(self):
        user_id = request.args['user_id']

        # Body 데이터 받아오기
        seminar = request.get_json()

        # category를 index로 변환
        seminar['category'] = SeminarEnum.Category(seminar['category'])

        # DB 예외 처리
        try:
            # 수정된 사항을 DB에 반영
            database = Database()
            sql = "UPDATE seminars SET user_id = %s, title = %s, url = %s, category = %s, date = %s WHERE id = %s;"
            values = (user_id, seminar['title'], seminar['url'], seminar['category'], seminar['date'], seminar['id'])
            database.execute(sql, values)
            database.commit()
        except Exception as e:
            return {'message': '서버에 오류가 발생했어요 :(\n지속적으로 발생하면 문의주세요!', 'error': str(e)}, 400
        finally:
            database.close()

        return {'message': '세미나 정보를 수정했어요 :)'}, 200

    # 세미나 정보 삭제
    @seminar.expect(SeminarDTO.query_seminar_id, validate=True)
    @seminar.response(200, 'OK', SeminarDTO.seminar_response_message)
    @seminar.response(400, 'Bad Request', SeminarDTO.seminar_response_message)
    @seminar.doc(security='apiKey')
    @api_access_level(1)
    def delete(self):
        seminar_id = request.args['id']

        # DB 예외 처리
        try:
            # 세미나 정보를 DB에서 삭제
            database = Database()
            sql = "DELETE FROM seminars WHERE id = %s;"
            values = (seminar_id,)
            database.execute(sql, values)
            database.commit()
        except Exception as e:
            return {'message': '서버에 오류가 발생했어요 :(\n지속적으로 발생하면 문의주세요!', 'error': str(e)}, 400
        finally:
            database.close()

        return {'message': '세미나 정보를 삭제했어요 :)'}, 200
