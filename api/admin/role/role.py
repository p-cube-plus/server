from flask import Flask, request
from flask_restx import Resource, Namespace
from database.database import Database
from datetime import datetime, date
from utils.dto import AdminRoleDTO
from flask_jwt_extended import jwt_required, get_jwt_identity
from utils.enum_tool import AdminEnum
from utils.api_access_level_tool import api_access_level

role = AdminRoleDTO.api

@role.route('/list')
class AdminRoleListAPI(Resource):   
    @role.response(200, 'OK', [AdminRoleDTO.model_admin_role])
    @role.response(400, 'Bad Request', AdminRoleDTO.response_admin_role_message)
    @role.doc(security='apiKey')
    @api_access_level(2)
    def get(self):
        try:
            database = Database()
            sql = "SELECT * FROM admin;"
            admin_list = database.execute_all(sql)
        except Exception as e:
            return {'message': '서버에 오류가 발생했어요 :(\n지속적으로 발생하면 문의주세요!', 'error': str(e)}, 400
        finally:
            database.close()

        if not admin_list:
            return [], 200
        else:
            for idx, admin in enumerate(admin_list):
                admin_list[idx]['start_date'] = admin['start_date'].strftime('%Y-%m-%d')
                admin_list[idx]['end_date'] = admin['end_date'].strftime('%Y-%m-%d')
                admin_list[idx]['role'] = AdminEnum.Role(admin['role'])
            return admin_list, 200

@role.route('')
class AdminRoleAPI(Resource):
    @role.expect(AdminRoleDTO.query_admin_id, validate=True)
    @role.response(200, 'OK', AdminRoleDTO.model_admin_role)
    @role.response(400, 'Bad Request', AdminRoleDTO.response_admin_role_message)
    @role.doc(security='apiKey')
    @api_access_level(2)
    def get(self):
        id = request.args['id']

        try:
            database = Database()
            sql = "SELECT * FROM admin WHERE id = %s;"
            values = (id,)
            admin = database.execute_one(sql, values)
        except Exception as e:
            return {'message': '서버에 오류가 발생했어요 :(\n지속적으로 발생하면 문의주세요!', 'error': str(e)}, 400
        finally:
            database.close()

        if not admin:
            return None, 200
        else:
            admin['start_date'] = admin['start_date'].strftime('%Y-%m-%d')
            admin['end_date'] = admin['end_date'].strftime('%Y-%m-%d')
            admin['role'] = AdminEnum.Role(admin['role'])

            return admin, 200
    
    @role.expect(AdminRoleDTO.model_admin_role_without_id, validate=True)
    @role.response(201, 'Created', AdminRoleDTO.response_admin_role_message)
    @role.response(400, 'Bad Request', AdminRoleDTO.response_admin_role_message)
    @role.doc(security='apiKey')
    @api_access_level(2)
    def post(self):
        admin = request.get_json()

        admin['role'] = AdminEnum.Role(admin['role'])

        try:
            database = Database()
            sql = "INSERT INTO admin (user_id, role, start_date, end_date) VALUES (%s, %s, %s, %s);"
            values = (admin['user_id'], admin['role'], admin['start_date'], admin['end_date'])
            database.execute(sql, values)
            database.commit()
        except Exception as e:
            return {'message': '서버에 오류가 발생했어요 :(\n지속적으로 발생하면 문의주세요!', 'error': str(e)}, 400
        finally:
            database.close()

        return {'message': '임원진 직책 정보를 추가했어요 :)'}, 201

    @role.expect(AdminRoleDTO.model_admin_role, validate=True)
    @role.response(200, 'OK', AdminRoleDTO.response_admin_role_message)
    @role.response(400, 'Bad Request', AdminRoleDTO.response_admin_role_message)
    @role.doc(security='apiKey')
    @api_access_level(2)
    def put(self):
        admin = request.get_json()

        admin['role'] = AdminEnum.Role(admin['role'])

        try:
            database = Database()
            sql = "UPDATE admin SET user_id = %s, role = %s, start_date = %s, end_date = %s WHERE id = %s;"
            values = (admin['user_id'], admin['role'], admin['start_date'], admin['end_date'], admin['id'])
            database.execute(sql, values)
            database.commit()
        except Exception as e:
            return {'message': '서버에 오류가 발생했어요 :(\n지속적으로 발생하면 문의주세요!', 'error': str(e)}, 400
        finally:
            database.close()

        return {'message': '임원진 직책 정보를 수정했어요 :)'}, 200
    
    @role.expect(AdminRoleDTO.query_admin_id, validate=True)
    @role.response(200, 'OK', AdminRoleDTO.response_admin_role_message)
    @role.response(400, 'Bad Request', AdminRoleDTO.response_admin_role_message)
    @role.doc(security='apiKey')
    @api_access_level(2)
    def delete(self):
        id = request.args['id']

        try:
            database = Database()
            sql = "DELETE FROM admin WHERE id = %s;"
            values = (id,)
            database.execute(sql, values)
            database.commit()
        except Exception as e:
            return {'message': '서버에 오류가 발생했어요 :(\n지속적으로 발생하면 문의주세요!', 'error': str(e)}, 400
        finally:
            database.close()

        return {'message': '임원진 직책 정보를 삭제했어요 :)'}, 200
    
@role.route('/user')
class AdminRoleCheckAPI(Resource):
    @role.expect(AdminRoleDTO.query_user_id, validate=True)
    @role.response(200, 'OK', AdminRoleDTO.model_admin_role_user)
    @role.response(400, 'Bad Request', AdminRoleDTO.response_admin_role_message)
    @role.doc(security='apiKey')
    @api_access_level(2)
    def get(self):
        user_id = request.args['user_id']

        try:
            database = Database()
            sql = "SELECT * FROM admin WHERE user_id = %s ORDER BY start_date DESC;"
            values = (user_id,)
            record_list = database.execute_all(sql, values)
        except Exception as e:
            return {'message': '서버에 오류가 발생했어요 :(\n지속적으로 발생하면 문의주세요!', 'error': str(e)}, 400
        finally:
            database.close()

        if not record_list:
            return {'current_role': None, 'record_list': []}, 200
        else:
            current_date = datetime.today().date()
            current_role = None

            for idx, record in enumerate(record_list):
                if record['start_date'] <= current_date <= record['end_date']:
                    current_role = AdminEnum.Role(record['role'])
                
                record_list[idx]['start_date'] = record['start_date'].strftime('%Y-%m-%d')
                record_list[idx]['end_date'] = record['end_date'].strftime('%Y-%m-%d')
                record_list[idx]['role'] = AdminEnum.Role(record['role'])

            return {'current_role': current_role, 'record_list': record_list}, 200

@role.route('/api-access-level')
class AdminAPIAccessLevelAPI(Resource):
    @role.doc(security='apiKey')
    @api_access_level(2)
    def get(self):
        user_id = request.args['user_id']

        try:
            database = Database()
            sql = "SELECT api_access_level FROM users WHERE id = %s;"
            values = (user_id,)
            api_access_level = database.execute_one(sql, values)
        except Exception as e:
            return {'message': '서버에 오류가 발생했어요 :(\n지속적으로 발생하면 문의주세요!', 'error': str(e)}, 400
        finally:
            database.close()

        return {'api_access_level': api_access_level}, 200
    
    @role.doc(security='apiKey')
    @api_access_level(2)
    def put(self):
        data = request.get_json()

        try:
            database = Database()
            sql = "UPDATE users SET api_access_level = %s WHERE id = %s;"
            values = (data['api_access_level'], data['user_id'])
            database.execute(sql, values)
            database.commit()
        except Exception as e:
            return {'message': '서버에 오류가 발생했어요 :(\n지속적으로 발생하면 문의주세요!', 'error': str(e)}, 400
        finally:
            database.close()

        return {'message': 'API 접근 권한을 수정했어요 :)'}, 200
