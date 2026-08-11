import base64
import time
import hmac
import hashlib
import urllib.parse
import requests
from configs import setting


def generate_sign():
    """
    生成签名计算
    :return:
    """
    # 获取当前时间的时间戳
    timestamp = str(round(time.time() * 1000))
    # 获取钉钉机器人里面的加签密钥
    secret = setting.secret
    # 转码成utf-8
    secret_enc = secret.encode('utf-8')
    # 组合当前时间戳和加签密钥
    str_to_sign = f"{timestamp}\n{secret}"
    # 转成byte类型
    str_to_sign_enc = str_to_sign.encode('utf-8')
    # 通过加密方式加密当前时间戳和密钥
    hmac_code = hmac.new(secret_enc,str_to_sign_enc,digestmod=hashlib.sha256).digest()
    sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
    return timestamp, sign


def send_dd_msg(content,at_all=False):
    """
    向钉钉群发送消息
    :param content: 发送内容
    :param at_all: @全员，默认为True
    :return:
    """
    timestamp, sign = generate_sign()
    # 组成一个完整的url地址
    url = f"{setting.webhook}&timestamp={timestamp}&sign={sign}"
    headers = {"Content-Type": "application/json;charset=UTF-8"}
    data = {
        'msgtype': 'text',
        'text': {
            'content': content
        },
        'at': {
            'isAtAll': at_all
        }
    }
    session = requests.Session()
    session.trust_env = False
    res = session.post(url=url, headers=headers, json=data, timeout=15)
    return res.text


