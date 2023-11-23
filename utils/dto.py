from flask_restx import Namespace, fields

def nullable(field):
    class NullableField(field):
        __schema_type__ = [field.__schema_type__, "null"]
        __schema_example__ = f"nullable {field.__schema_type__}"
    return NullableField

class AttendanceDTO:
    api = Namespace('attendance', description='회원 출석 기능')

    model_attendance = api.model('model_attendance', {
        'date': fields.Date(description='출석 날짜', example='2023-09-19'),
        'category': fields.String(description='회의 종류', enum=['디자인', '아트', '프로그래밍', '정기', '기타']),
        'first_auth_start_time': fields.String(description='1차 인증 시작 시간', example='16:55:00'),
        'first_auth_end_time': fields.String(description='1차 인증 종료 시간', example='17:04:59'),
        'second_auth_start_time': fields.String(description='2차 인증 시작 시간', example='17:55:00'),
        'second_auth_end_time': fields.String(description='2차 인증 종료 시간', example='18:04:59'),
        'state': nullable(fields.String)(description='출석 상태', enum=['출석', '지각', '불참', None]),
        'first_auth_time': nullable(fields.String)(description='1차 인증 시간', example='16:52:00'),
        'second_auth_time': nullable(fields.String)(description='2차 인증 시간', example='17:53:00')
    })

    model_record = api.model('model_record', {
        'date': fields.Date(description='출석 일자'),
        'state': fields.String(description='출석 여부')
    })

    model_user_attendance = api.model('model_user_attendance', {
        'state': nullable(fields.String)(description='출석 상태', enum=['출석', '지각', '불참', None]),
        'first_auth_time': nullable(fields.String)(description='1차 인증 시간'),
        'second_auth_time': nullable(fields.String)(description='2차 인증 시간')
    })

    response_data = api.model('response_data', {
        'attendance': fields.Nested(model_attendance, description='금일 참여해야 할 출석 목록'),
        'record_list': fields.List(fields.Nested(model_record), description='최근 4건의 출석 여부')
    })

    response_message = api.model('response_message', {
        'message': fields.String(description='결과 메시지')
    })

    query_user_id = api.parser().add_argument(
        'user_id', type=str, help='유저 ID'
    )

    query_prev_attendance_count = api.parser().add_argument(
        'prev_attendance_count', type=str, help='과거 출석 기록 수'
    )

class AdminNotificationDTO:
    api = Namespace('notification', description='임원진 알림 관리')

    model_notification = api.model('model_notification', {
        'id': fields.Integer(description='알림 ID (POST 시에는 유효하지 않습니다.)'),
        'member_category': fields.String(description="알림 대상자 종류", enum=['활동 중인 회원 전체', '활동 중인 정회원', '활동 중인 수습회원', '기타 선택']),
        'time': fields.String(description='알림 시간'),
        'start_date': fields.String(description='시작일'),
        'end_date': fields.String(description='종료일'),
        'day': nullable(fields.String)(description="요일", example='월요일'),
        'cycle': fields.String(description='알림 주기'),
        'message': nullable(fields.String)(description='알림 메시지'),
        'memo': nullable(fields.String)(description='메모'),
        'member_list': fields.List(fields.String, description="알림 대상자 목록('알림 대상자 종류가 '기타 선택'이 아닌 경우 빈 리스트)")
    })

    model_user = api.model('model_user', {
        'id': fields.String(description='회원 ID'),
        'name': fields.String(description='이름'),
        'grade': fields.Integer(description='학년')
    })

    model_payment_period = api.model('model_payment_period', {
        'date': fields.String(description='년/월 (YYYY-MM-01)'),
        'start_date': fields.String(description='납부 시작일'),
        'end_date': fields.String(description='납부 마감일')
    })

    response_message = api.model('response_message', {
        'message': fields.String(description='결과 메시지')
    })

    response_notification_list = api.model('response_notification_list', {
        'notification_list': fields.List(fields.Nested(model_notification), description='알림 목록')
    })

    response_user_list = api.model('response_user_list', {
        'user_list': fields.List(fields.Nested(model_user), description='회원 목록')
    })

    response_payment_period_list = api.model('response_payment_period_list', {
        'payment_period_list': fields.List(fields.Nested(model_payment_period), description='회비 납부 기간 목록')
    })

    query_notification_id = api.parser().add_argument(
        'notification_id', type=str, help='알림 ID'
    )

class AdminAttendanceDTO:
    api = Namespace('attendance', description='임원진 출석 관리')

    model_attendance = api.model('model_attendance', {
        'id': fields.Integer(description='ID'),
        'date': fields.Date(description='출석 날짜'),
        'first_auth_start_time': nullable(fields.String)(description='1차 인증 시작 시간'),
        'first_auth_end_time': nullable(fields.String)(description='1차 인증 종료 시간'),
        'second_auth_start_time': nullable(fields.String)(description='2차 인증 시작 시간'),
        'second_auth_end_time': nullable(fields.String)(description='2차 인증 종료 시간'),
    })

    model_user = api.model('model_user', {
        'id': fields.String(description='ID'),
        'name': fields.String(description='이름'),
        'grade': fields.String(description='학년'),
        'part_index': fields.Integer(description='소속 파트'),
        'rest_type': fields.String(description='활동 여부'),
        'state': nullable(fields.String)(description='출석 상태', enum=['출석', '지각', '불참', None]),
        'first_auth_time': nullable(fields.String)(description='1차 인증 시간'),
        'second_auth_time': nullable(fields.String)(description='2차 인증 시간')
    })

    model_user_attendance = api.model('model_user_attendance', {
        'user_id': fields.String(description='ID'),
        'state': nullable(fields.String)(description='출석 상태', enum=['출석', '지각', '불참', None]),
        'first_auth_time': nullable(fields.String)(description='1차 인증 시간'),
        'second_auth_time': nullable(fields.String)(description='2차 인증 시간')
    })

    response_attendance = api.model('response_attendance', {
        'date': fields.Date(description='출석 날짜'),
        'first_auth_start_time': fields.String(description='1차 인증 시작 시간'),
        'first_auth_end_time': fields.String(description='1차 인증 종료 시간'),
        'second_auth_start_time': fields.String(description='2차 인증 시작 시간'),
        'second_auth_end_time': fields.String(description='2차 인증 종료 시간')
    })

    response_user_list = api.model('model_user_list', {
        'user_list': fields.List(fields.Nested(model_user), description='회원 목록')
    })

    response_message = api.model('response_message', {
        'message': fields.String(description='결과 메시지')
    })

    query_date = api.parser().add_argument(
        'date', type=str, help='출석 일자'
    )
    
    query_user_id = api.parser().add_argument(
        'user_id', type=str, help='유저 ID'
    )
    
    query_attendance_id = api.parser().add_argument(
        'attendance_id', type=int, help='출석 ID'
    )

class WarningDTO:
    api = Namespace('warning', description='회원 경고 기능')

    model_warning = api.model('model_warning', {
        'category': fields.String(description='회의 종류', enum=['경고 차감', '주의 차감', '주의 부여', '경고 부여', '경고 초기화']),
        'date': fields.String(description='날짜', example='2023-09-26'),
        'description': fields.String(description='사유', example='지각'),
        'comment': nullable(fields.String)(description='비고', example='연락없이 무단 지각 함.')
    })

    model_warning_with_id = api.inherit('model_warning_with_id', model_warning, {
        'id': fields.Integer(description='경고 ID')
    })

    model_warning_list = api.model('model_warning_list', {
        'warning_list': fields.List(fields.Nested(model_warning_with_id), description='경고 목록')
    })

    model_warning_list_with_total = api.inherit('model_warning_list_with_total', model_warning_list, {
        'warning_total': fields.Float(description='누적 경고 횟수', example='2.5')
    })

    query_user_id = api.parser().add_argument(
        'user_id', type=str, help='유저 ID'
    )

    query_warning_id = api.parser().add_argument(
        'id', type=str, help='경고 ID'
    )

    warning_response_message = api.model('warning_reponse_message', {
        'message': fields.String(description='결과 메시지', example="경고 정보를 수정했어요 :)")
    })
    
class AccountingDTO:
    api = Namespace('accounting', description='회원 회비 납부 내역')

    model_monthly_payment = api.model('model_monthly_payment', {
        'date': fields.String(description='납부 년/월 (YYYY-MM-01 형식)', example='2023-09-01'),
        'amount': fields.Integer(description='납부 금액', example=5000),
        'category': fields.String(description='납부 상태', example='납부 완료')
    })

    model_payment_period = api.model('model_payment_period', {
        'start_date': fields.String(description='금월 납부 기간 시작일', example='2023-09-20'),
        'end_date': fields.String(description='금월 납부 기간 마감일', example='2023-09-28')
    })

    model_payment_info = api.model('model_payment_info', {
        'monthly_payment_list': fields.List(fields.Nested(model_monthly_payment)),
        'payment_period': nullable(fields.Nested)(model_payment_period),
        'payment_amount': fields.Integer(description='금월 납부 금액', example=5000),
        'total_amount': fields.Integer(description='동아리 계좌 총 금액', example=900000)
    })

    model_accounting = api.model('mode_accounting', {
        'id': fields.Integer(description='계좌 내역 ID', example=1),
        'date': fields.String(description='입/출금 날짜', example='2023-09-01'),
        'amount': fields.Integer(description='입/출금 금액', example=20000),
        'description': (nullable)(fields.String)(description='설명', example='아트 파트 책 구매'),
        'category': fields.String(description='내역 유형', example='비품비'),
        'pament_method': fields.String(description='입/출금 방식', enum=['통장', '금고'])
    })

    model_accounting_info = api.model('model_accounting_info', {
        'accounting_list': fields.List(fields.Nested(model_accounting)),
        'total_amount': fields.Integer(description='동아리 계좌 총 금액', example=900000)
    })

    accounting_response_message = api.model('accounting_response_message', {
        'message': fields.String(description='결과 메시지', example="데이터베이스 오류가 발생했어요 :(")
    })

    query_user_id = api.parser().add_argument(
        'user_id', type=str, help='유저 ID'
    )

class AdminAccountingDTO:
    api = Namespace('accounting', description='임원진 회계 관리 기능')

    model_user_payment = api.model('model_user_payment', {
        'date': fields.String(description='납부 년/월 (YYYY-MM-01 형식)', example='2023-09-01'),
        'name': fields.String(description='이름', example='홍길동'),
        'level': fields.String(description='회원 등급', example='정회원'),
        'grade': fields.Integer(description='학년', example=4),
        'amount': fields.Integer(description='납부 금액', example=5000),
        'category': fields.String(description='납부 상태', example='납부 완료')
    })

    model_monthly_payment = api.model('model_monthly_payment', {
        'date': fields.String(description='납부 년/월 (YYYY-MM-01 형식)', example='2023-09-01'),
        'start_date': fields.String(description='금월 납부 기간 시작일', example='2023-09-20'),
        'end_date': fields.String(description='금월 납부 기간 마감일', example='2023-09-28'),
        'user_payment_list':  fields.List(fields.Nested(model_user_payment))
    })

    model_monthly_payment_list = api.model('model_monthly_payment_list', {
        'monthly_payment_list': fields.List(fields.Nested(model_monthly_payment))
    })

    model_payment_period = api.model('model_payment_period', {
        'date': fields.String(description='납부 년/월 (YYYY-MM-01 형식)', example='2023-09-01'),
        'start_date': fields.String(description='금월 납부 기간 시작일', example='2023-09-20'),
        'end_date': fields.String(description='금월 납부 기간 마감일', example='2023-09-28')
    })

    model_payment_period_list = api.model('model_payment_period_list', {
        'payment_period_list': fields.List(fields.Nested(model_payment_period))
    })

    response_message = api.model('response_message', {
        'message': fields.String(description='결과 메시지', example="결과 메시지")
    })

    query_admin_account_date = api.parser().add_argument(
        'date', type=str, help='날짜'
    )

class SeminarDTO:
    api = Namespace('seminar', description='세미나 내역')

    model_seminar = api.model('model_seminar', {
        'title': fields.String(description='제목', example='세미나 제목'),
        'url': fields.String(description='카페 내 게시물 주소', example='www.aaa.com/3'),
        'category': fields.String(description='파트', enum=['디자인', '아트', '프로그래밍', '재학생']),
        'date': fields.String(description='발표 날짜', example='2023-09-26'),
    })

    model_seminar_with_id = api.inherit('model_seminar_with_id', model_seminar, {
        'id': fields.Integer(description='세미나 ID')
    })

    model_seminar_list = api.model('model_seminar_list', {
        'seminar_list': fields.List(fields.Nested(model_seminar_with_id), description='세미나 목록')
    })

    query_user_id = api.parser().add_argument(
        'user_id', type=str, help='유저 ID'
    )

    query_seminar_id = api.parser().add_argument(
        'id', type=str, help='세미나 ID'
    )

    seminar_response_message = api.model('seminar_reponse_message', {
        'message': fields.String(description='결과 메시지', example="결과 메시지 입니다 :)")
    })

class UserDTO:
    api = Namespace('user', description='내 정보')

    model_user_profile = api.model('model_user_profile', {
        'name': fields.String(description='제목', example='홍길동'),
        'level': fields.String(description='출석 상태', enum=['탈퇴자', '정회원', '수습회원', '명예회원', '수습회원(휴학)', '졸업생']),
        'grade': fields.Integer(desciption='학년', example=2),
        'part_index': fields.String(description='소속 파트', enum=['디자인', '아트', '프로그래밍']),
        'rest_type': fields.String(description='활동 상태', enum=['활동', '일반휴학', '군휴학']),
        'profile_image': nullable(fields.String)(description='프로필 이미지')
    })

    model_user_warning = api.model('model_user_warning', {
        'total_warning': fields.Float(description='누적 경고 횟수', example=0.5)
    })

    model_user_project = api.model('model_user_project', {
        'id': fields.Integer(description='프로젝트 ID', example=1),
        'name': fields.String(description='프로젝트 명', example='PCubePlus'),
        'type': fields.String(description='종류', enum=['메인 프로젝트', '꼬꼬마 프로젝트']),
        'status': fields.String(desciption='상태', enum=['완료', '진행 중', '시작 전']),
        'start_date': fields.String(desciption='시작일', example='2023-01-01'),
        'end_date': nullable(fields.String)(desciption='종료일'),
        'graphic': fields.String(desciption='그래픽', example='2D'),
        'platform': fields.String(desciption='플랫폼', example='PC'),
        'is_finding_member': fields.Boolean(desciption='멤버 모집 여부', example=False),
        'is_able_inquiry': fields.Boolean(description='질의 가능 여부', example=True)
    })

    model_user_project_list = api.model('model_user_project_list', {
        'project_list': fields.List(fields.Nested(model_user_project), description='회원 프로젝트 목록')
    })

    response_message = api.model('response_message', {
        'message': fields.String(description='결과 메시지', example="결과 메시지")
    })