from flask import Flask, request
from flask_restx import Resource, Namespace
from database.database import Database
from utils.aes_cipher import AESCipher
from utils.dto import ProjectDTO
from flask_jwt_extended import jwt_required, get_jwt_identity
from utils.enum_tool import convert_to_string, convert_to_index, ProjectEnum

project = ProjectDTO.api
crypt = AESCipher()

@project.route("")
class ProjectListAPI(Resource):
    # 회원의 참여 프로젝트 목록 얻기
    @project.response(200, 'OK', [ProjectDTO.model_project])
    @project.response(400, 'Bad Request', ProjectDTO.response_message)
    @project.doc(security='apiKey')
    @jwt_required()
    def get(self):
        user_id = get_jwt_identity()

        # DB 예외 처리
        try:
            # DB에서 user_id값에 맞는 프로젝트 목록 불러오기
            database = Database()
            sql = f"SELECT p.* FROM projects p JOIN project_members pm ON p.id = pm.project_id "\
                f"WHERE pm.user_id = '{user_id}' ORDER BY p.start_date DESC;"
            project_list = database.execute_all(sql)
        except:
            return {'message': '서버에 오류가 발생했어요 :(\n지속적으로 발생하면 문의주세요!'}, 400
        finally:
            database.close()

        if not project_list: # 프로젝트를 한 적이 없을 때 처리
            return [], 200
        else:
            for idx, project in enumerate(project_list):
                # index를 문자열로 변환
                project_list[idx]['type'] = convert_to_string(ProjectEnum.TYPE, project['type'])
                project_list[idx]['status'] = convert_to_string(ProjectEnum.STATUS, project['status'])

                # date를 문자열로 변환
                if project['start_date']:
                    project_list[idx]['start_date'] = project['start_date'].strftime('%Y-%m-%d')
                if project['end_date']:
                    project_list[idx]['end_date'] = project['end_date'].strftime('%Y-%m-%d')

                # platform을 리스트로 변환
                project_list[idx]['platform'] = project['platform'].split(',') if project['platform'] else []

                # index를 Boolean 값으로 변경
                project_list[idx]['is_finding_member'] = True if project['is_finding_member'] else False
                project_list[idx]['is_able_inquiry'] = True if project['is_able_inquiry'] else False

                try:
                    database = Database()
                    sql = f'''SELECT u.is_signed, u.name, u.level, u.part_index, u.profile_image, p.is_pm
                            FROM users u
                            INNER JOIN project_members p ON u.id = p.user_id
                            WHERE p.project_id = {project['id']};'''
                    members = database.execute_all(sql)
                except:
                    return {'message': '서버에 오류가 발생했어요 :(\n지속적으로 발생하면 문의주세요!'}, 400
                finally:
                    database.close()

                pm_idx = None
                for i, member in enumerate(members):
                    member['name'] = crypt.decrypt(member['name'])
                    member['is_signed'] = True if member['is_signed'] else False
                    is_pm = member.pop('is_pm')
                    if is_pm:
                        pm_idx = i
                        break
                project_list[idx]['pm'] = members.pop(pm_idx) if not pm_idx else None
                project_list[idx]['members'] = members

            return project_list, 200

@project.route("/all")
class ProjectAllListAPI(Resource):
    # 회원의 참여 프로젝트 목록 얻기
    @project.response(200, 'OK', [ProjectDTO.model_project])
    @project.response(400, 'Bad Request', ProjectDTO.response_message)
    @project.doc(security='apiKey')
    @jwt_required()
    def get(self):
        # DB 예외 처리
        try:
            # DB에서 user_id값에 맞는 프로젝트 목록 불러오기
            database = Database()
            sql = f"SELECT p.* FROM projects p JOIN project_members pm ON p.id = pm.project_id "\
                "ORDER BY p.start_date DESC;"
            project_list = database.execute_all(sql)
        except:
            return {'message': '서버에 오류가 발생했어요 :(\n지속적으로 발생하면 문의주세요!'}, 400
        finally:
            database.close()

        if not project_list: # 프로젝트를 한 적이 없을 때 처리
            return [], 200
        else:
            for idx, project in enumerate(project_list):
                # index를 문자열로 변환
                project_list[idx]['type'] = convert_to_string(ProjectEnum.TYPE, project['type'])
                project_list[idx]['status'] = convert_to_string(ProjectEnum.STATUS, project['status'])

                # date를 문자열로 변환
                if project['start_date']:
                    project_list[idx]['start_date'] = project['start_date'].strftime('%Y-%m-%d')
                if project['end_date']:
                    project_list[idx]['end_date'] = project['end_date'].strftime('%Y-%m-%d')

                # platform을 리스트로 변환
                project_list[idx]['platform'] = project['platform'].split(',') if project['platform'] else []

                # index를 Boolean 값으로 변경
                project_list[idx]['is_finding_member'] = True if project['is_finding_member'] else False
                project_list[idx]['is_able_inquiry'] = True if project['is_able_inquiry'] else False

                try:
                    database = Database()
                    sql = f'''SELECT u.is_signed, u.name, u.level, u.part_index, u.profile_image, p.is_pm
                            FROM users u
                            INNER JOIN project_members p ON u.id = p.user_id
                            WHERE p.project_id = {project['id']};'''
                    members = database.execute_all(sql)
                except:
                    return {'message': '서버에 오류가 발생했어요 :(\n지속적으로 발생하면 문의주세요!'}, 400
                finally:
                    database.close()

                pm_idx = None
                for i, member in enumerate(members):
                    member['name'] = crypt.decrypt(member['name'])
                    member['is_signed'] = True if member['is_signed'] else False
                    is_pm = member.pop('is_pm')
                    if is_pm:
                        pm_idx = i
                        break
                project_list[idx]['pm'] = members.pop(pm_idx) if not pm_idx else None
                project_list[idx]['members'] = members

            return project_list, 200
