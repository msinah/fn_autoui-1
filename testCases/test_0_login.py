"""登录态初始化用例。

执行 YAML 中的登录/跳转步骤后暂停浏览器，允许人工完成登录，再把 Cookie
和 localStorage 保存到 configs/cookies.json，供后续业务用例复用。
"""

import pytest
from unit_tools.handle_data.read_data import data
from configs.setting import FILE_PATH
from unit_tools.assert_control import *
import os


# 模块加载时读取 YAML；loginpage 列表中的每一项会成为一条测试参数。
data_path = FILE_PATH['data']
cases_dict = data.load_yaml(os.path.join(data_path,'login.yaml'))

class Testfbmcart:
    """生成后续购物车和汇出用例所需的登录态。"""

    @pytest.mark.skipif(cases_dict['loginpage'][0]['skip'] == True, reason='跳过执行')
    @pytest.mark.parametrize('CaseData', cases_dict['loginpage'])
    def test_login(self,page, run_case_fixture, CaseData):
        """执行登录流程并持久化当前浏览器上下文。"""
        run_case_fixture(page, CaseData)
        try:
            # page.wait_for_timeout(1000)
            page.pause()
            # storage_state 同时保存 Cookie 和 localStorage，不只是 Cookie。
            cookies_path = FILE_PATH['set_cookies']
            page.context.storage_state(path=cookies_path)
        except Exception as e:
            print(f'结果错误{e}')
            raise
