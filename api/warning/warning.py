from flask import Flask, request
from flask_restx import Resource, Namespace
from database.database import Database
from utils.dto import WarningDTO
from flask_jwt_extended import jwt_required, get_jwt_identity
from utils.enum_tool import WarningEnum
from utils.api_access_level_tool import api_access_level

warning = WarningDTO.api

@warning.route('')
class WarningUserAPI(Resource):
    # 회원의 경고 목록 얻기
    @warning.response(200, 'OK', WarningDTO.model_warning_list_with_total)
    @warning.doc(security='apiKey')
    @api_access_level(1)
    def get(self):
        user_id = get_jwt_identity()

        # DB 예외 처리
        try:
            # DB에서 user_id값에 맞는 경고 목록 불러오기
            database = Database()
            sql = f"SELECT id, category, date, description, comment FROM warnings WHERE user_id = '{user_id}' ORDER BY date;"
            warning_list = database.execute_all(sql)
        except:
            return {'message': '서버에 오류가 발생했어요 :(\n지속적으로 발생하면 문의주세요!'}, 400
        finally:
            database.close()

        if not warning_list: # 경고를 받은 적이 없을 때 처리
            return {
                'warning_category': {}, 
                'warning_add_list': [],
                'warning_remove_list': [],
                'total_warning': 0,
                'total_add_warning': 0,
                'total_remove_warning': 0
            }, 200
        else:
            total_warning = total_add_warning = total_remove_warning = 0
            add_list, remove_list = [], []
            for idx, warning in enumerate(warning_list):
                # date를 문자열로 변환
                warning_list[idx]['date'] = warning['date'].strftime('%Y-%m-%d')
                
                # 누적 경고 횟수 계산
                if warning['category'] == 0:
                    total_warning = 0
                else:
                    total_warning += warning['category']
                    total_warning = max(total_warning, 0)

                # 경고 부여, 차감에 따라 원소 분리
                if warning['category'] >= WarningEnum.Category('주의 부여'):
                    add_list.append(warning)
                    total_add_warning += warning['category']
                else:
                    remove_list.append(warning)
                    total_remove_warning += abs(warning['category']) \
                        if warning['category'] != 0 \
                        else total_add_warning - total_remove_warning

            return {
                'warning_category': {-2: '경고 차감', -1: '주의 차감', 1: '주의 부여', 2: '경고 부여', 0: '경고 초기화'},
                'warning_add_list': add_list,
                'warning_remove_list': remove_list,
                'total_warning': total_warning / 2.0,
                'total_add_warning': total_add_warning / 2.0,
                'total_remove_warning': total_remove_warning / 2.0,
            }, 200
