from flask import Flask, request
from flask_restx import Resource, Namespace
from database.database import Database
from datetime import datetime, date
from utils.dto import AdminRoleDTO
from flask_jwt_extended import jwt_required, get_jwt_identity
from utils.enum_tool import AdminEnum

role = AdminRoleDTO.api

@role.route('/list')
class AdminRoleListAPI(Resource):   

    # 임원진 직책 정보 목록 조회
    @role.response(200, 'OK', [AdminRoleDTO.model_admin_role])
    @role.response(400, 'Bad Request', AdminRoleDTO.response_admin_role_message)
    @role.doc(security='apiKey')
    @jwt_required()
    def get(self):
        # DB 예외처리
        try:
            database = Database()
            sql = "SELECT * FROM admin;"
            admin_list = database.execute_all(sql)
        except:
            return {'message': '서버에 오류가 발생했어요 :(\n지속적으로 발생하면 문의주세요!'}, 400
        finally:
            database.close()

        if not admin_list: # 임원진 직책이 존재하지 않을 시 처리
            return [], 200
        else:
            # 날짜 및 직책을 문자열로 변경
            for idx, admin in enumerate(admin_list):
                admin_list[idx]['start_date'] = admin['start_date'].strftime('%Y-%m-%d')
                admin_list[idx]['end_date'] = admin['end_date'].strftime('%Y-%m-%d')
                admin_list[idx]['role'] = AdminEnum.Role(admin['role'])
            return admin_list, 200
        
    
@role.route('')
class AdminRoleAPI(Resource):

    # 임원진 직책 정보 조회
    @role.expect(AdminRoleDTO.query_admin_id, validate=True)
    @role.response(200, 'OK', AdminRoleDTO.model_admin_role)
    @role.response(400, 'Bad Request', AdminRoleDTO.response_admin_role_message)
    @role.doc(security='apiKey')
    @jwt_required()
    def get(self):
        # Query parameter 값 얻어오기
        id = request.args['id']

        # DB 예외처리
        try:
            database = Database()
            sql = f"SELECT * FROM admin WHERE id = {id};"
            admin = database.execute_one(sql)
            database.close()
        except:
            return {'message': '서버에 오류가 발생했어요 :(\n지속적으로 발생하면 문의주세요!'}, 400
        finally:
            database.close()

        if not admin: # 임원진 정보가 없을 시 처리
            return None, 200
        else:
            # 날짜 및 직책을 문자열로 변경
            admin['start_date'] = admin['start_date'].strftime('%Y-%m-%d')
            admin['end_date'] = admin['end_date'].strftime('%Y-%m-%d')
            admin['role'] = AdminEnum.Role(admin['role'])

            return admin, 200
    
    # 임원진 직책 정보 추가
    @role.expect(AdminRoleDTO.model_admin_role_without_id, validate=True)
    @role.response(201, 'Created', AdminRoleDTO.response_admin_role_message)
    @role.response(400, 'Bad Request', AdminRoleDTO.response_admin_role_message)
    @role.doc(security='apiKey')
    @jwt_required()
    def post(self):
        # Body 데이터 얻어오기
        admin = request.get_json()

        # 직책을 index로 변경
        admin['role'] = AdminEnum.Role(admin['role'])

        # DB 예외처리
        try:
            database = Database()
            sql = "INSERT INTO admin VALUES(NULL, %s, %s, %s, %s);"
            values = (admin['user_id'], admin['role'], admin['start_date'], admin['end_date'])
            database.execute(sql, values)
            database.commit()
        except:
            return {'message': '서버에 오류가 발생했어요 :(\n지속적으로 발생하면 문의주세요!'}, 400
        finally:
            database.close()

        return {'message': '임원진 직책 정보를 추가했어요 :)'}, 201

    # 임원진 직책 정보 수정
    @role.expect(AdminRoleDTO.model_admin_role, validate=True)
    @role.response(200, 'OK', AdminRoleDTO.response_admin_role_message)
    @role.response(400, 'Bad Request', AdminRoleDTO.response_admin_role_message)
    @role.doc(security='apiKey')
    @jwt_required()
    def put(self):
        # Body 데이터 얻어오기
        admin = request.get_json()

        # 직책을 index로 변경
        admin['role'] = AdminEnum.Role(admin['role'])

        # DB 예외처리
        try:
            database = Database()
            sql = "UPDATE admin SET "\
                "user_id = %s, role = %s, start_date = %s, end_date = %s "\
                "WHERE id = %s;"
            values = (admin['user_id'], admin['role'], admin['start_date'], admin['end_date'], admin['id'])
            database.execute(sql, values)
            database.commit()
        except:
            return {'message': '서버에 오류가 발생했어요 :(\n지속적으로 발생하면 문의주세요!'}, 400
        finally:
            database.close()

        return {'message': '임원진 직책 정보를 수정했어요 :)'}, 200
    
    # 임원진 직책 정보 삭제
    @role.expect(AdminRoleDTO.query_admin_id, validate=True)
    @role.response(200, 'OK', AdminRoleDTO.response_admin_role_message)
    @role.response(400, 'Bad Request', AdminRoleDTO.response_admin_role_message)
    @role.doc(security='apiKey')
    @jwt_required()
    def delete(self):
        # Query parameter 값 얻어오기
        id = request.args['id']

        # DB 예외처리
        try:
            database = Database()
            sql = f"DELETE FROM admin WHERE id = {id};"
            database.execute(sql)
            database.commit()
        except:
            return {'message': '서버에 오류가 발생했어요 :(\n지속적으로 발생하면 문의주세요!'}, 400
        finally:
            database.close()

        return {'message': '임원진 직책 정보를 삭제했어요 :)'}, 200
    
@role.route('/user')
class AdminRoleCheckAPI(Resource):

    # 회원의 임원진 정보 조회
    @role.expect(AdminRoleDTO.query_user_id, validate=True)
    @role.response(200, 'OK', AdminRoleDTO.model_admin_role_user)
    @role.response(400, 'Bad Request', AdminRoleDTO.response_admin_role_message)
    @role.doc(security='apiKey')
    @jwt_required()
    def get(self):
        # Query parameter 값 얻어오기
        user_id = request.args['user_id']

        # DB 예외처리
        try:
            database = Database()
            sql = f"SELECT * FROM admin WHERE user_id = '{user_id}' ORDER BY start_date DESC;"
            record_list = database.execute_all(sql)
        except:
            return {'message': '서버에 오류가 발생했어요 :(\n지속적으로 발생하면 문의주세요!'}, 400
        finally:
            database.close()

        if not record_list: # 회원의 임원진 정보가 없을 시 처리
            return {'current_role': None, 'record_list': []}, 200
        else:
            # 현재 날짜 및 직책 설정
            current_date = datetime.today().date()
            current_role = None

            for idx, record in enumerate(record_list):
                # 임기 중인 직책을 현재 직책으로 설정
                if record['start_date'] <= current_date <= record['end_date']:
                     current_role = AdminEnum.Role(record['role'])
                
                # 날짜 및 직책 문자열로 변환
                record_list[idx]['start_date'] = record['start_date'].strftime('%Y-%m-%d')
                record_list[idx]['end_date'] = record['end_date'].strftime('%Y-%m-%d')
                record_list[idx]['role'] = AdminEnum.Role(record['role'])

            return {'current_role': current_role, 'record_list': record_list}, 200

@role.route('/api-access-level')
class AdminAPIAccessLevelAPI(Resource):

    @role.doc(security='apiKey')
    @jwt_required()
    def get(self):
        user_id = request.args['user_id']

        database = Database()
        sql = f"SELECT api_access_level FROM users WHERE id = '{user_id}';"
        api_access_level = database.execute_one(sql)
        database.close()

        return {'api_access_level': api_access_level}, 200
    
    @role.doc(security='apiKey')
    @jwt_required()
    def put(self):
        data = request.get_json()

        database = Database()
        sql = f"UPDATE users SET api_access_level = {data['api_access_level']} WHERE id = '{data['user_id']}';"
        database.execute(sql)
        database.close()

        return {'message': 'API 접근 권한을 수정했어요 :)'}, 200