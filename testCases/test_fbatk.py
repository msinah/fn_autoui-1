"""TikTok 购物车下单流程。"""

import pytest

from unit_tools.handle_data.read_data import data
from configs.setting import FILE_PATH
from unit_tools.assert_control import *
import os


# 通用加购 YAML 与 TikTok 支付 YAML 组合成完整链路。
data_path = FILE_PATH['data']
cases_dict = data.load_yaml(os.path.join(data_path,'fbmaddtocart.yaml'))
fba_tk_dict = data.load_yaml(os.path.join(data_path,'fbatkpaycart.yaml'))

@pytest.fixture(scope="class")
def shared_context(browser):
    """载入登录态，并让整类测试共享浏览器上下文。"""
    storage_state_path = FILE_PATH.get("set_cookies")
    context = browser.new_context(storage_state=storage_state_path) if storage_state_path and os.path.exists(storage_state_path) else browser.new_context()
    try:
        yield context
    finally:
        context.close()


@pytest.fixture(scope="class")
def shared_page(shared_context):
    """共享 Page，保证支付步骤可以承接加购结果。"""
    page = shared_context.new_page()
    try:
        yield page
    finally:
        page.close()


class Testfbmcart:
    """按“加入购物车 → TikTok 支付”的顺序执行。"""

    @pytest.mark.skipif(cases_dict['loginpage'][0]['skip'] == True, reason='跳过执行')
    @pytest.mark.parametrize('CaseData', cases_dict['loginpage'])
    def test_fbmaddtocart(self, shared_page, run_case_fixture, CaseData):
        run_case_fixture(shared_page, CaseData)
        try:
            shared_page.wait_for_timeout(1000)
        except Exception as e:
            print(f'结果错误{e}')
            raise

    @pytest.mark.skipif(fba_tk_dict['loginpage'][0]['skip'] == True, reason='跳过执行')
    @pytest.mark.parametrize('CaseData', fba_tk_dict['loginpage'])
    def test_fba_tk_paycart(self, shared_page, run_case_fixture, CaseData):
        run_case_fixture(shared_page, CaseData)
        try:
            shared_page.wait_for_timeout(1000)
            assert_title(shared_page, CaseData["assertion"], CaseData["title"])
        except Exception as e:
            logs.error(f'断言结果为False，错误信息：{e}')
            raise

