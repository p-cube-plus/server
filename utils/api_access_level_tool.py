from functools import wraps
from flask import current_app
from utils.enum_tool import AdminEnum
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request

# memcached에 저장되어 있는 사용자의 API 접근 권한 불러오기
def get_access_level(user_id):
    mc = current_app.extensions['memcache_client']
    access_level = mc.get('api_access_level_' + user_id)
    return access_level

# memcached에 사용자의 API 접근 권한 저장하기 (수정 必)
def store_access_level(user_id, role):
    mc = current_app.extensions['memcache_client']
    mc.set('api_access_level_' + user_id, 2)

# memcached에서 사용자의 API 접근 권한 제거하기
def erase_access_level(user_id):
    mc = current_app.extensions['memcache_client']
    mc.delete('api_access_level_' + user_id)

# API 접근 권한을 설정하는 데코레이터 생성 함수
def api_access_level(access_level, **extargs):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not access_level == 0:
                verify_jwt_in_request(extargs)
                user_id = get_jwt_identity()
                # user_access_level = get_access_level(user_id)
                user_access_level = 2
                if user_access_level < access_level:
                    return {'message': 'API에 대한 접근 권한이 없어요 :('}, 401
            return current_app.ensure_sync(func)(*args, **kwargs)
        return wrapper
    return decorator