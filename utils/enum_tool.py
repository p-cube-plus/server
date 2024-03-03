class EnumData:
    # 생성자
    def __init__(self, index, string):
        self.index = index
        self.string = string

    def __str__(self):
        return self.string
    
    def __int__(self):
        return self.index
    
    def __eq__(self, other):
        if isinstance(other, int):
            return self.index == other
        if isinstance(other, str):
            return self.string == other
        if isinstance(other, EnumData):
            return self.index == other.index or self.string == other.string
        return False
    
class EnumMeta(type):
    def __call__(cls, value):
        for data in cls.__dict__.values():
            if isinstance(data, EnumData):
                if isinstance(value, int) and data.index == value:
                    return data.string
                if isinstance(value, str) and data.string == value:
                    return data.index
        return None
    
    def __contains__(cls, value):
        for data in cls.__dict__.values():
            if isinstance(data, EnumData):
                if isinstance(value, int) and data.index == value:
                    return True
                elif isinstance(value, str) and data.string == value:
                    return True
        return False
    
class EnumSet(metaclass=EnumMeta):
    pass
    
class UserEnum:
    # 회원 분류
    class Level(EnumSet):
        WITHDRWAN = EnumData(0, '탈퇴자')
        REGULAR = EnumData(1, '정회원')
        TRAINEE = EnumData(2, '수습회원')
        HONORARY = EnumData(3, '명예회원')
        TRAINEE_ON_LEAVE = EnumData(4, '수습회원(휴학)')
        GRADUATE = EnumData(5, '졸업생')
    
    # 회원 소속 파트
    class Part(EnumSet):
        DESIGN = EnumData(0, '디자인')
        ART = EnumData(1, '아트')
        PROGRAMMING = EnumData(2, '프로그래밍')
    
    # 회원 학적 상태
    class RestType(EnumSet):
        ACTIVE = EnumData(-1, '활동')
        GENERAL_LEAVE = EnumData(0, '일반휴학')
        MILITARY_LEAVE = EnumData(1, '군휴학')

class AttendanceEnum:
    class Category(EnumSet):
        DESIGN = EnumData(0, '디자인')
        ART = EnumData(1, '아트')
        PROGRAMMING = EnumData(2, '프로그래밍')
        REGULAR = EnumData(3, '정기')
        ETC = EnumData(4, '기타')

    class UserAttendanceState(EnumSet):
        ATTENDANCE = EnumData(0, '출석')
        TARDINESS = EnumData(1, '지각')
        ABSENCE = EnumData(2, '불참')

class NotificationEnum:
    class Category(EnumSet):
        DESIGN = EnumData(0, '디자인')
        ART = EnumData(1, '아트')
        PROGRAMMING = EnumData(2, '프로그래밍')
        REGULAR = EnumData(3, '정기')
        CLEANING = EnumData(4, '청소')
        MONLTHLY_FEE = EnumData(5, '회비')
        ETC = EnumData(6, '기타')

    class MemberCategory(EnumSet):
        ALL_ACTIVE_MEMBERS = EnumData(0, '활동 중인 회원 전체')
        ACTIVE_REGULAR_MEMBERS = EnumData(1, '활동 중인 정회원')
        ACTIVE_TRAINEE_MEMBERS = EnumData(2, '활동 중인 수습회원')
        ETC = EnumData(3, '기타 선택')

    class DayCategory(EnumSet):
        MONDAY = EnumData(0, '월요일')
        TUESDAY = EnumData(1, '화요일')
        WEDNESDAY = EnumData(2, '수요일')
        THURSDAY = EnumData(3, '목요일')
        FRIDAY = EnumData(4, '금요일')
        SATURDAY = EnumData(5, '토요일')
        SUNDAY = EnumData(6, '일요일')

    class FcmTopic(EnumSet):
        DESIGN = EnumData(0, 'design')
        ART = EnumData(1, 'art')
        PROGRAMMING = EnumData(2, 'programming')

class AccountingEnum:
    class PaymentState(EnumSet):
        REFUND_ELIGIBLE = EnumData(0, '환불 대상')
        PAID_ON_TIME = EnumData(1, '기간 내 납입')
        EARLY_PAYMENT = EnumData(2, '조기 납입')
        ARREARS = EnumData(3, '체납')
        NOT_PAID = EnumData(4, '미입금')
    
    class PaymentMethod(EnumSet):
        BANK_TRANSFER = EnumData(0, '통장')
        SAFE = EnumData(1, '금고')

class SeminarEnum:
    class Category(EnumSet):
        DESIGN = EnumData(0, '디자인')
        ART = EnumData(1, '아트')
        PROGRAMMING = EnumData(2, '프로그래밍')
        STUDENT = EnumData(3, '재학생')

class WarningEnum:
    class Category(EnumSet):
        WARNING_DECREMENT = EnumData(-2, '경고 차감')
        CAUTION_DECREMENT = EnumData(-1, '주의 차감')
        CAUTION_INCREMENT = EnumData(1, '주의 부여')
        WARNING_INCREMENT = EnumData(2, '경고 부여')
        WARNING_RESET = EnumData(0, '경고 초기화')

class ProjectEnum:
    class Type(EnumSet):
        MAIN_PROJECT = EnumData(0, '메인 프로젝트')
        MINI_PROJECT = EnumData(1, '꼬꼬마 프로젝트')

    class Status(EnumSet):
        COMPLETED = EnumData(0, '완료')
        IN_PROGRESS = EnumData(1, '진행 중')
        NOT_STARTED = EnumData(2, '시작 전')