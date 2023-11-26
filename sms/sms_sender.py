import time
import requests
import hmac
import configparser
import base64
import hashlib

__all__ = ['send']

config = configparser.ConfigParser()
config.read('config/config.ini')

url = config['sms']['sms_url']
uri = config['sms']['sms_uri']
access_key = config['sms']['sms_access_key']
secret_key = config['sms']['sms_secret_key']
from_number = config['sms']['sms_from_number']

# 공통 헤더 마지막 필드(x-ncp-apigw-signature-v2)에 들어가는 시그니처를 생성
def _make_signature(method, uri, timestamp):
    message = method + " " + uri + "\n" + timestamp + "\n" + access_key
    message = bytes(message, 'UTF-8')
    signature = base64.b64encode(hmac.new(bytes(secret_key, 'UTF-8'), message, digestmod=hashlib.sha256).digest())
    return signature

# SMS 발송
def send(to_number, message):
    timestamp = str(int(time.time() * 1000))
    signature = _make_signature('POST', uri, timestamp)

    headers = {
        'Content-Type': "application/json; charset=utf-8",
        'x-ncp-apigw-timestamp': timestamp,
        'x-ncp-iam-access-key': access_key,
        'x-ncp-apigw-signature-v2': signature
    }

    body = {
        'type': "SMS",
        'from': from_number,
        'content': message,
        'messages': [
            {
                'to': to_number,
                'content': message
            }
        ]
    }

    res = requests.post(url, json=body, headers=headers)
    return res