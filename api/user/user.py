from flask import Flask, redirect, request, current_app
from flask_restx import Resource, Api, Namespace
from database.database import Database
from utils.dto import UserDTO
from utils.enum_tool import convert_to_string, convert_to_index, UserEnum, WarningEnum, ProjectEnum
from flask_jwt_extended import jwt_required, get_jwt_identity
from utils.aes_cipher import AESCipher

user = UserDTO.api

@user.route("/profile")
class UserProfileAPI(Resource):
    @user.response(200, 'OK', UserDTO.model_user_profile)
    @user.response(400, 'Bad Request', UserDTO.response_message)
    @user.doc(security='apiKey')
    @jwt_required()
    def get(self):
        user_id = get_jwt_identity()

        # DB 예외 처리
        try:
            # DB에서 회원 정보 조회
            database = Database()
            sql = f"SELECT name, level, grade, part_index, rest_type, profile_image FROM users WHERE id = '{user_id}';"
            user = database.execute_one(sql)
        except:
            return {'message': '서버에 오류가 발생했어요 :(\n지속적으로 발생하면 문의주세요!'}, 400
        finally:
            database.close()

        if not user: # 회원 정보가 조회되지 않을 시 처리
            return { 'message': '회원 정보를 찾지 못했어요 :(' }, 400
        else:
            # 회원 이름 복호화
            crypt = AESCipher()
            user['name'] = crypt.decrypt(user['name'])

            # index를 문자열로 변경
            user['level'] = convert_to_string(UserEnum.LEVEL, user['level'])
            user['part_index'] = convert_to_string(UserEnum.PART, user['part_index'])
            user['part'] = user.pop('part_index')
            user['rest_type'] = convert_to_string(UserEnum.REST_TYPE, user['rest_type'])
            
            return user, 200

@user.route('/warning')
class UserWarningAPI(Resource):
    @user.response(200, 'OK', UserDTO.model_user_warning)
    @user.response(400, 'Bad Request', UserDTO.response_message)
    @user.doc(security='apiKey')
    @jwt_required()
    def get(self):
        user_id = get_jwt_identity()

        # DB 예외 처리
        try:
            # DB에서 user_id값에 맞는 경고 목록 불러오기
            database = Database()
            sql = f"SELECT * FROM warnings WHERE user_id = '{user_id}' ORDER BY date;"
            warning_list = database.execute_all(sql)
        except:
            return {'message': '서버에 오류가 발생했어요 :(\n지속적으로 발생하면 문의주세요!'}, 400
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

            return project_list, 200
        
@user.route("/user/setting/notification")
class UserNotificationSettingAPI(Resource):
    @user.response(200, 'OK', UserDTO.model_user_notification_setting)
    @user.response(400, 'Bad Request', UserDTO.response_message)
    @user.doc(security='apiKey')
    @jwt_required()
    def get(self):
        user_id = get_jwt_identity()
        
        # DB 예외 처리
        try:
            # DB에서 회원 알림 설정 정보 얻기
            database = Database()
            sql = f"SELECT * FROM notification_setting WHERE user_id = '{user_id}';"
            setting = database.execute_one(sql)
        except:
            return {'message': '서버에 오류가 발생했어요 :(\n지속적으로 발생하면 문의주세요!'}, 400
        finally:
            database.close()

        # 불필요한 컬럼 제거
        setting.pop('user_id')

        # index를 Boolean 값으로 변경
        for key in setting.keys():
            setting[key] = True if setting[key] else False

        return setting, 200

    @user.expect(UserDTO.model_user_notification_setting, validate=True)
    @user.response(200, 'OK', UserDTO.response_message)
    @user.response(400, 'Bad Request', UserDTO.response_message)
    @user.doc(security='apiKey')
    @jwt_required()
    def put(self):
        user_id = get_jwt_identity()
        setting = request.get_json()

        # DB 예외 처리
        try:
            # 회원 알림 설정을 DB에 저장
            database = Database()

            sql = "INSERT INTO notification_setting (user_id, permission, regular_meeting, part_meeting, membership_fee, cleaning, book_rental) "\
                "VALUES(%s, %s, %s, %s, %s, %s, %s) "\
                "ON DUPLICATE KEY UPDATE permission = %s, regular_meeting = %s, part_meeting = %s, membership_fee = %s, cleaning = %s, book_rental = %s;"
            
            value = (user_id, setting['permission'], setting['regular_meeting'], setting['part_meeting'], 
                    setting['membership_fee'], setting['cleaning'], setting['book_rental'],
                    setting['permission'], setting['regular_meeting'], setting['part_meeting'], 
                    setting['membership_fee'], setting['cleaning'], setting['book_rental'])

            database.execute(sql, value)
            database.commit()
        except:
            return {'message': '서버에 오류가 발생했어요 :(\n지속적으로 발생하면 문의주세요!'}, 400
        finally:
            database.close()
        
        return {'message': '회원의 알림 설정 정보를 수정했어요 :)'}, 200