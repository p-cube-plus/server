from apscheduler.schedulers.background import BackgroundScheduler
import firebase_admin
from firebase_admin import credentials, messaging
from datetime import datetime
from database.database import Database
from utils.enum_tool import convert_to_index, convert_to_string, NotificationEnum

scheduler = BackgroundScheduler()
scheduler.start()

cred_path = "config/firebase-adminsdk.json"
cred = credentials.Certificate(cred_path)
firebase_admin.initialize_app(cred)

# DB에 저장된 알림 정보를 스케줄러에 등록 (서버 시작 시 호출 필요)
def load_messages():
    # DB 예외 처리
    try:
        # DB에서 알림 목록 가져오기 (현재는 회의 알림만 가져온다.)
        database = Database()
        sql = f"SELECT * FROM notification;"
        notification_list = database.execute_all(sql)

        for idx, notification in enumerate(notification_list):
            # 날짜 및 시간을 문자열로 변경
            if notification['date']:
                notification_list[idx]['date'] = notification['date'].strftime('%Y-%m-%d')
            notification_list[idx]['time'] = str(notification['time'])

            # 알림 category
            category = notification['category']


            # 알림 대상자 설정
            if category == 3: # 정기 회의인 경우
                sql = f"SELECT id FROM users WHERE rest_type = -1;"
                notification['member_list'] = [user['id'] for user in database.execute_all(sql)]
            elif category <= 2: # 파트 회의인 경우
                sql = f"SELECT id FROM users WHERE rest_type = -1 AND part_index = {category};"
                notification['member_list'] = [user['id'] for user in database.execute_all(sql)]

            # FCM 알림 예약
            if category in NotificationEnum.FCM_TOPIC.keys(): # 회의 알림인 경우
                # 내용 및 주제 설정
                title = "회의 알림"
                body = notification['message']
                topic = convert_to_string(NotificationEnum.FCM_TOPIC, category)

                # 알림 예약
                schedule_message(str(notification['id']), title, body, notification['time'], date=notification['date'], day=notification['day'], topic=topic, targets=notification['member_list'])
            else: # 청소 및 기타 알림인 경우
                # 추후 구현 예정
                pass
    except:
        print('서버에 오류가 발생했어요 :(\n지속적으로 발생하면 문의주세요!')
    finally:
        database.close()

# 유저 알림 상태 갱신
def update_user_notification(id, targets):
    # DB 예외 처리
    try:
        database = Database()
        sql = f"UPDATE notification_member SET is_sent = 1 WHERE id = {id} and user_id = %s;"
        values = [(target,) for target in targets]
        database.execute_many(sql, values)
        database.commit()
    except:
        print('서버에 오류가 발생했어요 :(\n지속적으로 발생하면 문의주세요!')
    finally:
        database.close()

# FCM 알림 전송
def send_message(id, title, body, tokens=None, topic=None, targets=None):
    if topic: # topic이 설정된 경우
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body
            ),
            topic=topic
        )
        response = messaging.send(message)        
    elif len(tokens) == 1: # token이 1개인 경우
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body
            ),
            token=tokens[0],
        )
        response = messaging.send(message)
    else: # token이 여러개인 경우
        message = messaging.MulticastMessage(
            notification=messaging.Notification(
                title=title,
                body=body
            ),
            tokens=tokens
        )
        response = messaging.send_multicast(message)

    update_user_notification(id, targets)

    return response

# FCM 알림 예약
def schedule_message(id, title, body, time, date = None, day = None, tokens=None, topic=None, targets=None):
    # 같은 id의 알림이 존재할 시 삭제
    if scheduler.get_job(id) is not None:
        remove_message(id)
    
    if date: # 날짜가 설정된 경우
        time = ':'.join(time.split(':')[:2])
        run_date = datetime.strptime(f"{date} {time}", '%Y-%m-%d %H:%M')
        scheduler.add_job(send_message, 'date', [id, title, body, tokens, topic, targets], id=id, run_date=run_date)
    else: # 대신 요일이 설정된 경우
        hour, minute = map(int, time.split(':')[:2])
        day_of_week = str(day)
        scheduler.add_job(send_message, 'cron', [id, title, body, tokens, topic, targets], id=id, day_of_week=day_of_week, hour=hour, minute=minute)

# FCM 알림 예약 취소
def remove_message(id):
    if scheduler.get_job(id) is not None:
        scheduler.remove_job(id)

# FCM 알림 구독
def subscribe(tokens, topic):
    response = messaging.subscribe_to_topic(tokens, topic)
    return response

# FCM 알림 구독 취소
def unsubscribe(tokens, topic):
    response = messaging.unsubscribe_from_topic(tokens, topic)
    return response