from flask import Flask, redirect, request, current_app
from flask_restx import Resource, Api, Namespace
from database.database import Database
from utils.dto import UserDTO
from utils.enum_tool import UserEnum, WarningEnum, ProjectEnum
from flask_jwt_extended import jwt_required, get_jwt_identity
from utils.aes_cipher import AESCipher
from utils.api_access_level_tool import api_access_level

user = UserDTO.api

@user.route("/profile")
class UserProfileAPI(Resource):
    @user.response(200, 'OK', UserDTO.model_user_profile)
    @user.response(400, 'Bad Request', UserDTO.response_message)
    @user.doc(security='apiKey')
    @api_access_level(1)
    def get(self):
        user_id = get_jwt_identity()

        # DB 예외 처리
        try:
            # DB에서 회원 정보 조회
            database = Database()
            sql = "SELECT name, level, grade, part_index, rest_type, profile_image FROM users WHERE id = %s;"
            values = (user_id,)
            user = database.execute_one(sql, values)
        except Exception as e:
            return {'message': '서버에 오류가 발생했어요 :(\n지속적으로 발생하면 문의주세요!', 'error': str(e)}, 400
        finally:
            database.close()

        if not user: # 회원 정보가 조회되지 않을 시 처리
            return {'message': '회원 정보를 찾지 못했어요 :('}, 400
        else:
            # 회원 이름 복호화
            crypt = AESCipher()
            user['name'] = crypt.decrypt(user['name'])

            # index를 문자열로 변경
            user['level'] = UserEnum.Level(user['level'])
            user['part_index'] = UserEnum.Part(user['part_index'])
            user['part'] = user.pop('part_index')
            user['rest_type'] = UserEnum.RestType(user['rest_type'])
            
            return user, 200

@user.route('/warning')
class UserWarningAPI(Resource):
    @user.response(200, 'OK', UserDTO.model_user_warning)
    @user.response(400, 'Bad Request', UserDTO.response_message)
    @user.doc(security='apiKey')
    @api_access_level(1)
    def get(self):
        user_id = get_jwt_identity()

        # DB 예외 처리
        try:
            # DB에서 user_id값에 맞는 경고 목록 불러오기
            database = Database()
            sql = "SELECT * FROM warnings WHERE user_id = %s ORDER BY date;"
            values = (user_id,)
            warning_list = database.execute_all(sql, values)
        except Exception as e:
            return {'message': '서버에 오류가 발생했어요 :(\n지속적으로 발생하면 문의주세요!', 'error': str(e)}, 400
        finally:
            database.close()

        # 누적 경고 횟수 계산
        total_warning = 0
        for warning in warning_list:
            if warning['category'] == 0:
                total_warning = 0
            else:
                total_warning += warning['category']
                total_warning = max(total_warning, 0)

        # 정수로 보정되어 있던 값을 실제 횟수로 변환하여 반환
        return {'total_warning': total_warning / 2.0}, 200

@user.route('/project')
class UserProjectAPI(Resource):
    @user.response(200, 'OK', [UserDTO.model_user_project])
    @user.response(400, 'Bad Request', UserDTO.response_message)
    @user.doc(security='apiKey')
    @api_access_level(1)
    def get(self):
        user_id = get_jwt_identity()

        # DB 예외 처리
        try:
            # DB에서 user_id값에 맞는 프로젝트 목록 불러오기
            database = Database()
            sql = """
                SELECT p.* 
                FROM projects p 
                JOIN project_members pm ON p.id = pm.project_id 
                WHERE pm.user_id = %s 
                ORDER BY p.start_date DESC;
            """
            values = (user_id,)
            project_list = database.execute_all(sql, values)
        except Exception as e:
            return {'message': '서버에 오류가 발생했어요 :(\n지속적으로 발생하면 문의주세요!', 'error': str(e)}, 400
        finally:
            database.close()

        if not project_list: # 프로젝트를 한 적이 없을 때 처리
            return [], 200
        else:
            for idx, project in enumerate(project_list):
                # index를 문자열로 변환
                project_list[idx]['type'] = ProjectEnum.Type(project['type'])
                project_list[idx]['status'] = ProjectEnum.Status(project['status'])
                # date를 문자열로 변환
                if project['start_date']:
                    project_list[idx]['start_date'] = project['start_date'].strftime('%Y-%m-%d')
                if project['end_date']:
                    project_list[idx]['end_date'] = project['end_date'].strftime('%Y-%m-%d')

                # platform을 리스트로 변환
                project_list[idx]['platform'] = project['platform'].split(',') if project['platform'] else []

                # index를 Boolean 값으로 변경
                project_list[idx]['is_finding_member'] = bool(project['is_finding_member'])
                project_list[idx]['is_able_inquiry'] = bool(project['is_able_inquiry'])

            return project_list, 200
        
@user.route('/list')
class UserListAPI(Resource):
    @user.expect(UserDTO.query_user_params, validate=True)
    @user.response(200, 'OK', [UserDTO.model_user_profile])
    @user.response(400, 'Bad Request', UserDTO.response_message)
    @user.doc(security='apiKey')
    @api_access_level(1)
    def get(self):
        # 쿼리 파라미터 얻기
        part_index = request.args.get('part', None)
        level = request.args.get('level', None)
        rest_type = request.args.get('rest_type', None)

        # 쿼리 파라미터에 맞게 SQL문 구성
        sql = "SELECT id, name, level, grade, part_index, rest_type, profile_image FROM users WHERE 1=1"
        values = []
        if part_index:
            sql += " AND part_index = %s"
            values.append(UserEnum.Part(part_index))
        if level:
            sql += " AND level = %s"
            values.append(UserEnum.Level(level))
        if rest_type:
            sql += " AND rest_type = %s"
            values.append(UserEnum.RestType(rest_type))

        # DB 예외처리
        try:
            # 회원 목록 얻기
            database = Database()
            user_list = database.execute_all(sql, tuple(values))
        except Exception as e:
            return {'message': '서버에 오류가 발생했어요 :(\n지속적으로 발생하면 문의주세요!', 'error': str(e)}, 400
        finally:
            database.close()

        if not user_list:  # 회원이 없을 때 처리
            return [], 200
        else:
            crypt = AESCipher()
            for idx, user in enumerate(user_list):
                # 회원 이름 복호화
                user_list[idx]['name'] = crypt.decrypt(user['name'])

                # index를 문자열로 변경
                user_list[idx]['level'] = UserEnum.Level(user['level'])
                user_list[idx]['part_index'] = UserEnum.Part(user['part_index'])
                user_list[idx]['part'] = user_list[idx].pop('part_index')
                user_list[idx]['rest_type'] = UserEnum.RestType(user['rest_type'])

            return user_list, 200
