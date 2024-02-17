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
        'category': fields.String(description='알림 종류', example='디자인 or 아트 or 프로그래밍 or 정기 or 기타'),
        'member_category': fields.String(description="알림 대상자 종류", example='활동 중인 회원 전체 or 활동 중인 정회원 or 활동 중인 수습회원 or 기타 선택'),
        'date': nullable(fields.String)(description='날짜'),
        'day': nullable(fields.String)(description='요일'),
        'time': fields.String(description='시간'),
        'location': nullable(fields.String)(description='장소'),
        'schedule': nullable(fields.String)(description='일정'),
        'message': nullable(fields.String)(desciption='메시지 기타 알림인 경우 설정)'),
        'memo': nullable(fields.String)(description='메모'),
        'member_list': fields.List(fields.String, description="알림 대상자 목록('알림 대상자 종류가 '기타 선택'이 아닌 경우 빈 리스트)")
    })

    model_notification_without_id = api.model('model_notification_without_id', {
        'category': fields.String(description='알림 종류', example='디자인 or 아트 or 프로그래밍 or 정기 or 기타'),
        'member_category': fields.String(description="알림 대상자 종류", example='활동 중인 회원 전체 or 활동 중인 정회원 or 활동 중인 수습회원 or 기타 선택'),
        'date': nullable(fields.String)(description='날짜'),
        'day': nullable(fields.String)(description='요일'),
        'time': fields.String(description='시간'),
        'location': nullable(fields.String)(description='장소'),
        'schedule': nullable(fields.String)(description='일정'),
        'message': nullable(fields.String)(desciption='메시지 기타 알림인 경우 설정)'),
        'memo': nullable(fields.String)(description='메모'),
        'member_list': fields.List(fields.String, description="알림 대상자 목록('알림 대상자 종류가 '기타 선택'이 아닌 경우 빈 리스트)")
    })

    model_admin_notification_user = api.model('model_admin_notification_user', {
        'id': fields.String(description='회원 ID'),
        'name': fields.String(description='이름'),
        'grade': fields.Integer(description='학년')
    })

    model_admin_notification_payment_period = api.model('model_admin_notification_payment_period', {
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
        'user_list': fields.List(fields.Nested(model_admin_notification_user), description='회원 목록')
    })

    response_payment_period_list = api.model('response_payment_period_list', {
        'payment_period_list': fields.List(fields.Nested(model_admin_notification_payment_period), description='회비 납부 기간 목록')
    })

    query_notification_id = api.parser().add_argument(
        'id', type=str, help='알림 ID'
    )

    query_notification_category = api.parser().add_argument(
        'category', type=str, help="알림 종류"
    )

class AdminAttendanceDTO:
    api = Namespace('attendance', description='임원진 출석 관리')

    model_attendance = api.model('model_attendance', {
        'id': fields.Integer(description='ID', example=0),
        'date': fields.Date(description='출석 날짜', example='2023-09-19'),
        'first_auth_start_time': nullable(fields.String)(description='1차 인증 시작 시간', example='16:55:00 (nullable)'),
        'first_auth_end_time': nullable(fields.String)(description='1차 인증 종료 시간', example='16:55:00 (nullable)'),
        'second_auth_start_time': nullable(fields.String)(description='2차 인증 시작 시간', example='16:55:00 (nullable)'),
        'second_auth_end_time': nullable(fields.String)(description='2차 인증 종료 시간', example='16:55:00 (nullable)'),
    })

    model_admin_attendance_user = api.model('model_admin_attendance_user', {
        'id': fields.String(description='회원 ID'),
        'name': fields.String(description='이름', example='홍길동'),
        'grade': fields.Integer(description='학년', example=4),
        'part': fields.String(description='소속 파트', example='디자인 or 아트 or 프로그래밍'),
        'rest_type': fields.String(description='활동 상태', example='활동 or 일반휴학 or 군휴학'),
        'state': nullable(fields.String)(description='출석 상태', example='출석 or 지각 or 불참 (nullable)'),
        'first_auth_time': nullable(fields.String)(description='1차 인증 시간', example='16:55:00 (nullable)'),
        'second_auth_time': nullable(fields.String)(description='2차 인증 시간', example='16:55:00 (nullable)')
    })

    model_user_attendance = api.model('model_user_attendance', {
        'attendance_id': fields.Integer(description='출석 ID'),
        'user_id': fields.String(description='회원 ID'),
        'state': nullable(fields.String)(description='출석 상태', example='출석 or 지각 or 불참 (nullable)'),
        'first_auth_time': nullable(fields.String)(description='1차 인증 시간', example='16:55:00 (nullable)'),
        'second_auth_time': nullable(fields.String)(description='2차 인증 시간', example='16:55:00 (nullable)')
    })

    model_attendance_without_id = api.model('model_attendance_without_id', {
        'category': fields.String(description='출석 종류', example='정기'),
        'date': fields.Date(description='출석 날짜', example='2023-09-19'),
        'first_auth_start_time': nullable(fields.String)(description='1차 인증 시작 시간', example='16:55:00 (nullable)'),
        'first_auth_end_time': nullable(fields.String)(description='1차 인증 종료 시간', example='16:55:00 (nullable)'),
        'second_auth_start_time': nullable(fields.String)(description='2차 인증 시작 시간', example='16:55:00 (nullable)'),
        'second_auth_end_time': nullable(fields.String)(description='2차 인증 종료 시간', example='16:55:00 (nullable)')
    })

    response_user_list = api.model('model_user_list', {
        'user_list': fields.List(fields.Nested(model_admin_attendance_user), description='회원 목록')
    })

    response_message = api.model('response_message', {
        'message': fields.String(description='결과 메시지', example="결과 메시지")
    })

    query_date_and_category = api.parser().add_argument(
        'date', type=str, help='출석 일자'
    ).add_argument(
        'category', type=str, help='출석 종류'
    )

    query_ids = api.parser().add_argument(
        'user_id', type=str, help='유저 ID'
    ).add_argument(
        'attendance_id', type=int, help='출석 ID'
    )
    
    query_user_id = api.parser().add_argument(
        'user_id', type=str, help='유저 ID'
    )

    query_raw_attendance_id = api.parser().add_argument(
        'id', type=int, help='ID'
    )
    
    query_attendance_id = api.parser().add_argument(
        'attendance_id', type=int, help='출석 ID'
    )

class WarningDTO:
    api = Namespace('warning', description='회원 경고 기능')

    model_warning = api.model('model_warning', {
        'category': fields.Integer(description='회의 종류', enum=[-2, -1, 0, 1, 2]),
        'date': fields.String(description='날짜', example='2023-09-26'),
        'description': fields.String(description='사유', example='지각'),
        'comment': nullable(fields.String)(description='비고', example='연락없이 무단 지각 함.')
    })

    model_warning_with_id = api.inherit('model_warning_with_id', model_warning, {
        'id': fields.Integer(description='경고 ID')
    })

    model_warning_category = api.model('model_warning_category', {
        -2: fields.String(example='경고 차감'),
        -1: fields.String(example='주의 차감'),
        1: fields.String(example='주의 부여'),
        2: fields.String(example='경고 부여'),
        0: fields.String(example='경고 초기화'),
    })

    model_warning_list = api.model('model_warning_list', {
        'warning_category': fields.Nested((model_warning_category), description='경고 카테고리 인덱스 설명'),
        'warning_add_list': fields.List(fields.Nested(model_warning_with_id), description='경고 목록'),
        'warning_remove_list': fields.List(fields.Nested(model_warning_with_id), description='경고 차감 목록'),
    })

    model_warning_list_with_total = api.inherit('model_warning_list_with_total', model_warning_list, {
        'total_warning': fields.Float(description='누적 경고 횟수', example='2.5'),
        'total_add_warning': fields.Float(description='누적 경고 부여 횟수', example='2.5'),
        'total_remove_warning': fields.Float(description='누적 경고 차감 횟수', example='2.5'),
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

class HomeDTO:
    api = Namespace('home', description='홈 화면 관련 기능(스케줄, 출석, 물품)')

    model_all_schedule_item_info = api.model('model_all_schedule_item_info', {
        'id': fields.Integer(description='계좌 내역 ID', example=1),
        'type': fields.Integer(description='일정 종류', example=1),
        'title': fields.String(description='일정 이름', example='정기회의'),
        'start_date': fields.Date(description='일정 시작 일', example='2023-01-01'),
        'start_time': fields.String(description='일정 시작 시간', example='09:00:00'),
        'end_date': fields.Date(description='일정 마지막 일', example='2023-01-02'),
    })

    model_upcoming_schedule_info = api.model('model_upcoming_schedule_info', {
        'id': fields.Integer(description='계좌 내역 ID', example=1),
        'type': fields.Integer(description='일정 종류', example=1),
        'title': fields.String(description='일정 이름', example='정기회의'),
        'start_date': fields.Date(description='일정 시작 일', example='2023-01-01'),
        'start_time': fields.String(description='일정 시작 시간', example='09:00:00'),
        'end_date': fields.Date(description='일정 마지막 일', example='2023-01-02'),
    })

    model_schedule_info = api.model('model_schedule_info', {
        'all_list': fields.List(fields.Nested(model_all_schedule_item_info)),
        'upcoming_list': fields.List(fields.Nested(model_upcoming_schedule_info)),
    })

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
        'part': fields.String(description='소속 파트', enum=['디자인', '아트', '프로그래밍']),
        'rest_type': fields.String(description='활동 상태', enum=['활동', '일반휴학', '군휴학']),
        'profile_image': nullable(fields.String)(description='프로필 이미지')
    })

    model_user_warning = api.model('model_user_warning', {
        'total_warning': fields.Float(description='누적 경고 횟수', example=0.5)
    })

    model_user_project = api.model('model_user_project', {
        'id': fields.Integer(description='프로젝트 ID', example=1),
        'name': fields.String(description='프로젝트 명', example='PCubePlus'),
        'type': nullable(fields.String)(description='종류', enum=['메인 프로젝트', '꼬꼬마 프로젝트'], example='메인 프로젝트 (nullable)'),
        'status': fields.String(desciption='상태', enum=['완료', '진행 중', '시작 전']),
        'start_date': nullable(fields.String)(desciption='시작일', example='2023-01-01 (nullable)'),
        'end_date': nullable(fields.String)(desciption='종료일', example='2023-01-01 (nullable)'),
        'graphic': nullable(fields.String)(desciption='그래픽', example='2D (nullable)'),
        'platform': fields.List(fields.String(desciption='플랫폼'), example= ['PC', 'Mobile']),
        'is_finding_member': fields.Boolean(desciption='멤버 모집 여부', example=False),
        'is_able_inquiry': fields.Boolean(description='질의 가능 여부', example=True)
    })

    model_user_project_list = api.model('model_user_project_list', {
        'project_list': fields.List(fields.Nested(model_user_project), description='회원 프로젝트 목록')
    })

    response_message = api.model('response_message', {
        'message': fields.String(description='결과 메시지', example="결과 메시지")
    })

class ProjectDTO:
    api = Namespace('project', description='프로젝트 참여 내역')

    model_member = api.model('model_member', {
        'is_signed': fields.Boolean(description="PCube+ 가입 여부", example=True),
        'name': fields.String(description="멤버 이름", example="홍길동"),
        'level': fields.Integer(description="회원 분류(정회원, 수습회원 등)", example=1),
        'part_index': fields.Integer(description="파트 인덱스", example=1),
        'profile_image': nullable(fields.String)(description="PCube+ 프로필 이미지", example="url (nullable)"),
    })

    model_project = api.model('model_project', {
        'id': fields.Integer(description='프로젝트 ID', example=1),
        'name': fields.String(description='프로젝트 명', example='PCubePlus'),
        'type': nullable(fields.String)(description='종류', enum=['메인 프로젝트', '꼬꼬마 프로젝트'], example='메인 프로젝트 (nullable)'),
        'status': fields.String(desciption='상태', enum=['완료', '진행 중', '시작 전']),
        'start_date': nullable(fields.String)(desciption='시작일', example='2023-01-01 (nullable)'),
        'end_date': nullable(fields.String)(desciption='종료일', example='2023-01-01 (nullable)'),
        'graphic': nullable(fields.String)(desciption='그래픽', example='2D (nullable)'),
        'platform': fields.List(fields.String(desciption='플랫폼'), example=['PC', 'Mobile']),
        'is_finding_member': fields.Boolean(desciption='멤버 모집 여부', example=False),
        'is_able_inquiry': fields.Boolean(description='질의 가능 여부', example=True),
        'pm': fields.Nested(model_member, description='프로젝트 PM 정보 (nullable)'),
        'members': fields.List(fields.Nested(model_member), description="PM을 제외한 프로젝트 멤버 목록")
    })

    response_message = api.model('response_message', {
        'message': fields.String(description='결과 메시지', example="결과 메시지")
    })

class OAuthDTO:
    api = Namespace('oauth', description='OAuth 인증')

    model_oauth_code_request = api.model('model_oauth_code_request', {
        'phone_number': fields.String(description='회원 휴대폰 번호', example='010-XXXX-YYYY')
    })

    model_oauth_code_confirm = api.model('model_oauth_code_confirm', {
        'code': fields.String(description='인증 번호', example='123456')
    })

    model_oauth_user = api.model('model_oauth_user', {
        'name': fields.String(desciption='회원 이름', example='홍길동'),
        'phone_number': fields.String(description='회원 휴대폰 번호', example='010-XXXX-YYYY'),
        'fcm_token': fields.String(description='회원 FCM 토큰')
    })

    response_oauth_sms_validation = api.model('response_oauth_sms_validation', {
        'is_success': fields.Boolean(description='SMS API 정상 호출 여부', example=True)
    })

    response_oauth_code_result = api.model('response_oauth_result', {
        'is_verified': fields.Boolean(description='인증 성공 여부', example=True)
    })

    response_oauth_user = api.model('response_oauth_user', {
        'is_member': fields.Boolean(description='가입 여부', example=True),
        'access_token': nullable(fields.String)(desription='엑세스 토큰', example='string (nullable)'),
        'refresh_token': nullable(fields.String)(desription='리프레시 토큰', example='string (nullable)'),
    })

    response_oauth_message = api.model('response_oauth_message', {
        'message': fields.String(description='결과 메시지', example="결과 메시지")
    })

class AuthDTO:
    api = Namespace('auth', description='Auth 인증')

    query_auth_user_id = api.parser().add_argument(
        'user_id', type=str, help='유저 ID'
    )

    response_logout_message = api.model('reponse_logout_message', {
        'message': fields.String(desciption='로그아웃 결과 메시지', example="Access 토큰이 성공적으로 제거되었어요 :)")
    })