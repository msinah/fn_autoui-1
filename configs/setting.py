"""项目路径、测试环境和通知相关的集中配置。"""

import os
import sys


DIR_PATH = os.path.dirname(os.path.dirname(__file__))
sys.path.append(DIR_PATH)


FILE_PATH = {
    "extract": os.path.join(DIR_PATH, "extract.yaml"),
    "ini": os.path.join(DIR_PATH, "configs", "config.ini"),
    "log": os.path.join(DIR_PATH, "logs"),
    "data": os.path.join(DIR_PATH, "data"),
    "cmout": os.path.join(DIR_PATH, "data", "cmout"),
    "set_cookies": os.path.join(DIR_PATH, "configs", "cookies.json"),
}


is_dd_msg = False

# 通知凭据只从运行环境读取，禁止写入仓库。
secret = os.getenv("DINGTALK_SECRET", "")
token = os.getenv("DINGTALK_TOKEN", "")


class RunConfig:
    """UI 自动化运行参数。"""

    browser = "chromium"
    mode = "headless"
    HostUrl = "xxx.xxxx.com"
    baseUrl = "http://front.fnconsumertest.com"
    rerun = "0"
    max_fail = "5"
    NEW_REPORT = (
        os.getenv("ALLURE_REPORT_URL")
        or os.getenv("PUBLIC_ALLURE_REPORT_URL")
        or "http://192.168.2.27:8088/#behaviors"
    )
    notice_status = False
    real_time_update_test_cases = False
    need_cookie = False

    # 身份鉴权信息只从环境变量读取。
    ssotoken = os.getenv("SSO_TOKEN", "")
    cookie = os.getenv("LOGIN_COOKIE", "")
    storage_state_json = ""
