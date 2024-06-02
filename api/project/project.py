from flask import Flask, request
from flask_restx import Resource, Namespace
from database.database import Database
from utils.aes_cipher import AESCipher
from utils.dto import ProjectDTO
from flask_jwt_extended import jwt_required, get_jwt_identity
from utils.enum_tool import ProjectEnum
from utils.api_access_level_tool import api_access_level

project = ProjectDTO.api
crypt = AESCipher()

@project.route("")
class ProjectListAPI(Resource):
    # 회원의 참여 프로젝트 목록 얻기
    @project.response(200, 'OK', [ProjectDTO.model_project])
    @project.response(400, 'Bad Request', ProjectDTO.response_message)
    @project.doc(security='apiKey')
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

                try:
                    database = Database()
                    sql = """
                        SELECT u.is_signed, u.name, u.level, u.part_index, u.profile_image, pm.is_pm
                        FROM project_members AS pm
                        JOIN users AS u ON pm.user_id = u.id
                        WHERE pm.project_id = %s;
                    """
                    values = (project['id'],)
                    members = database.execute_all(sql, values)
                except Exception as e:
                    return {'message': '서버에 오류가 발생했어요 :(\n지속적으로 발생하면 문의주세요!', 'error': str(e)}, 400
                finally:
                    database.close()

                pm_idx = None
                for i, member in enumerate(members):
                    member['name'] = crypt.decrypt(member['name'])
                    member['is_signed'] = bool(member['is_signed'])
                    is_pm = member.pop('is_pm')
                    if is_pm:
                        pm_idx = i
                project_list[idx]['pm'] = members.pop(pm_idx) if pm_idx is not None else None
                project_list[idx]['members'] = members

            return project_list, 200

@project.route("/all")
class ProjectAllListAPI(Resource):
    # 전체 프로젝트 목록 얻기
    @project.response(200, 'OK', [ProjectDTO.model_project])
    @project.response(400, 'Bad Request', ProjectDTO.response_message)
    @project.doc(security='apiKey')
    @api_access_level(0)
    def get(self):
        # DB 예외 처리
        try:
            # 전체 프로젝트 목록 불러오기
            database = Database()
            sql = "SELECT * FROM projects ORDER BY start_date DESC;"
            project_list = database.execute_all(sql)
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

                try:
                    database = Database()
                    sql = """
                        SELECT u.is_signed, u.name, u.level, u.part_index, u.profile_image, pm.is_pm
                        FROM project_members AS pm
                        JOIN users AS u ON pm.user_id = u.id
                        WHERE pm.project_id = %s;
                    """
                    values = (project['id'],)
                    members = database.execute_all(sql, values)
                except Exception as e:
                    return {'message': '서버에 오류가 발생했어요 :(\n지속적으로 발생하면 문의주세요!', 'error': str(e)}, 400
                finally:
                    database.close()

                pm_idx = None
                for i, member in enumerate(members):
                    member['name'] = crypt.decrypt(member['name'])
                    member['is_signed'] = bool(member['is_signed'])
                    is_pm = member.pop('is_pm')
                    if is_pm:
                        pm_idx = i
                project_list[idx]['pm'] = members.pop(pm_idx) if pm_idx is not None else None
                project_list[idx]['members'] = members

            return project_list, 200
