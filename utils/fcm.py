from apscheduler.schedulers.background import BackgroundScheduler
import firebase_admin
from firebase_admin import credentials, messaging
import datetime

scheduler = BackgroundScheduler()
scheduler.start()

cred_path = "config/firebase-adminsdk.json"
cred = credentials.Certificate(cred_path)
firebase_admin.initialize_app(cred)

def load_messages():
    pass

def send_message(title, body, tokens=None, topic=None):
    if topic:
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body
            ),
            topic=topic
        )
        response = messaging.send(message)        
    elif len(tokens) == 1:
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body
            ),
            token=tokens[0],
        )
        response = messaging.send(message)
    else:
        message = messaging.MulticastMessage(
            notification=messaging.Notification(
                title=title,
                body=body
            ),
            tokens=tokens
        )
        response = messaging.send_multicast(message)
    return response

def schedule_message(id, title, body, date, day, time, tokens=None, topic=None):
    if scheduler.get_job(id) is not None:
        remove_message(id)

    hour, minute = map(int, time.split(':'))
    day_of_week = str(day)
    
    if date:
        run_date = datetime.strptime(f"{date} {time}", '%Y-%m-%d %H:%M')
        scheduler.add_job(send_message, 'date', [title, body, tokens, topic], id=id, run_date=run_date)
    else:
        scheduler.add_job(send_message, 'cron', [title, body, tokens, topic], id=id, day_of_week=day_of_week, hour=hour, minute=minute)

def remove_message(id):
    scheduler.remove_job(id)

def subscribe(tokens, topic):
    response = messaging.subscribe_to_topic(tokens, topic)
    return response