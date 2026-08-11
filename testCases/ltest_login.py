"""不会被当前 pytest 规则收集的登录调试脚本。

文件名不是 test_*.py，因此适合保留手工调试逻辑；正式登录用例位于
test_0_login.py。
"""

import pytest
from unit_tools.handle_data.read_data import data
from configs.setting import FILE_PATH
from unit_tools.assert_control import *
import os


# 模块加载时读取 YAML，后续由 parametrize 展开为 pytest 用例参数。
data_path = FILE_PATH['data']
cases_dict = data.load_yaml(os.path.join(data_path,'login.yaml'))

class Testfbmcart:
    """调试登录并手工保存浏览器登录态。"""

    @pytest.mark.skipif(cases_dict['loginpage'][0]['skip'] == True, reason='跳过执行')
    @pytest.mark.parametrize('CaseData', cases_dict['loginpage'])
    def test_login(self,page, run_case_fixture, CaseData):
        """执行登录步骤，暂停供人工操作，然后保存 storage_state。"""
        run_case_fixture(page, CaseData)
        try:
            # page.wait_for_timeout(1000)
            page.pause()
            # 保存cookies
            cookies_path = FILE_PATH['set_cookies']
            page.context.storage_state(path=cookies_path)
        except Exception as e:
            print(f'结果错误{e}')
            raise
