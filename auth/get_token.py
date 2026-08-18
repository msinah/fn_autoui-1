"""通过登录接口获取 token，并存入进程内缓存。"""

import os

import requests

from unit_tools.cache_pools import CacheHandler
from unit_tools.log_util.recordlog import logs


def get_token():
    """使用环境变量中的登录凭据获取并缓存 token。"""
    url = os.getenv("LOGIN_URL", "")
    username = os.getenv("LOGIN_USERNAME", "")
    password = os.getenv("LOGIN_PASSWORD", "")

    if not all((url, username, password)):
        logs.info("未配置登录凭据，跳过 token 获取。")
        return None

    response = requests.post(
        url=url,
        json={"userName": username, "password": password},
        timeout=30,
    )
    response.raise_for_status()
    token = response.json().get("token")
    if token:
        CacheHandler.update_cache(cache_name="login_token", value=token)
        return token

    logs.info("登录接口未返回 token。")
    return None


if __name__ == "__main__":
    get_token()
