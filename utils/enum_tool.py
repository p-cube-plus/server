# index 데이터를 문자열로 변경
def convert_to_string(dictionary, index):
    return dictionary.get(index, None)

# 문자열 데이터를 index로 변경
def convert_to_index(dictionary, string):
    for key, value in dictionary.items():
        if value == string:
            return key
    return None
    
class UserEnum:
    # 회원 분류
    LEVEL = {0: '탈퇴자', 1: '정회원', 2: '수습회원', 3: '명예회원', 4: '수습회원(휴학)', 5: '졸업생'}
    # 회원 소속 파트
    PART = {0: '디자인', 1: '아트', 2: '프로그래밍'}
    # 회원 학적 상태
    REST_TYPE = {-1: '활동', 0: '일반휴학', 1:'군휴학'}

class AttendanceEnum:
    # 출석 종류
    CATEGORY = {0: '디자인', 1: '아트', 2: '프로그래밍', 3: '정기', 4: '기타'}
    # 유저 출석 상태
    USER_ATTENDANCE_STATE = {0: '출석', 1: '지각', 2: '불참'}

class NotificationEnum:
    # 알림 종류
    CATEGORY = {0: '디자인', 1: '아트', 2: '프로그래밍', 3: '정기', 4: '청소', 5: '회비', 6: '기타'}
    # 알림 대상 종류
    MEMBER_CATEGORY = {0: '활동 중인 회원 전체', 1: '활동 중인 정회원', 2: '활동 중인 수습회원', 3: '기타 선택'}
    # 요일 종류
    DAY_CATEGORY = {0: '월요일', 1: '화요일', 2: '수요일', 3: '목요일', 4: '금요일', 5: '토요일', 6: '일요일'}
    # FCM topic 종류
    FCM_TOPIC = {0: 'design', 1: 'art', 2: 'programming', 3: 'global'}

class AccountingEnum:
    # 회비 입금 상태
    PAYMENT_STATE = {0: '환불 대상', 1: '기간 내 납입', 2: '조기 납입', 3: '체납', 4: '미입금'}
    # 입출금 방법
    PAYMENT_METHOD = {0: '통장', 1: '금고'}

class SeminarEnum:
    # 세미나 종류
    CATEGORY = {0: '디자인', 1: '아트', 2: '프로그래밍', 3: '재학생'}

class WarningEnum:
    # 경고 종류
    CATEGORY = {-2: '경고 차감', -1: '주의 차감', 1: '주의 부여', 2: '경고 부여', 0: '경고 초기화'}

class ProjectEnum:
    # 프로젝트 타입
    TYPE = {0: '메인 프로젝트', 1: '꼬꼬마 프로젝트'}
    # 현재 상태
    STATUS = {0: '완료', 1: '진행 중', 2: '시작 전'}