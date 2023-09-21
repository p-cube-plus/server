from flask_restx import Namespace, fields

def nullable(field):
    class NullableField(field):
        __schema_type__ = [field.__schema_type__, "null"]
        __schema_example__ = f"nullable {field.__schema_type__}"
    return NullableField
    
class AttendanceDTO:
    api = Namespace('attendance', description='회원 출석 기능')

    model_attendance = api.model('model_attendance', {
        'date': fields.Date(description='출석 날짜'),
        'category': fields.String(description='회의 종류'),
        'first_auth_start_time': fields.String(description='1차 인증 시작 시간'),
        'first_auth_end_time': fields.String(description='1차 인증 종료 시간'),
        'second_auth_start_time': fields.String(description='2차 인증 시작 시간'),
        'second_auth_end_time': fields.String(description='2차 인증 종료 시간'),
        'state': nullable(fields.String)(description='출석 상태', enum=['출석', '지각', '불참', None]),
        'first_auth_time': nullable(fields.String)(description='1차 인증 시간'),
        'second_auth_time': nullable(fields.String)(description='2차 인증 시간')
    })

    model_record = api.model('model_record', {
        'date': fields.Date(description='출석 일자'),
        'state': fields.String(description='출석 여부')
    })

    model_user_attendance = api.model('model_user_attendance', {
        'user_id': fields.String(description='유저 ID'),
        'state': nullable(fields.String)(description='출석 상태', enum=['출석', '지각', '불참', None]),
        'first_auth_time': nullable(fields.String)(description='1차 인증 시간'),
        'second_auth_time': nullable(fields.String)(description='2차 인증 시간')
    })

    response_data = api.model('response_data', {
        'attendance': fields.Nested(model_attendance, description='금일 참여해야 할 출석 목록'),
        'record_list': fields.List(fields.Nested(model_record), description='최근 4건의 출석 여부')
    })

    response_data_with_code = api.inherit('response_data_with_code', response_data, {
        'code': fields.Integer(description='상태 코드', example=200)
    })

    response_message = api.model('response_message', {
        'message': fields.String(description='결과 메시지', example="회원의 출석 인증 정보를 수정했어요 :)")
    })

    response_message_with_code = api.inherit('response_message', response_message, {
        'code': fields.Integer(description='상태 코드', example=200)
    })

    query_user_id = api.parser().add_argument(
        'user_id', type=str, help='유저 ID'
    )