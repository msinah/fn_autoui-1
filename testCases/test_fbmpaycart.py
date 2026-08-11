"""FBM 自发货购物车下单流程。"""

import pytest
from unit_tools.handle_data.read_data import data
from configs.setting import FILE_PATH
from unit_tools.assert_control import *
import os


# 通用加购和 FBM 支付分别维护，运行时在同一个页面连续执行。
data_path = FILE_PATH['data']
cases_dict = data.load_yaml(os.path.join(data_path,'fbmaddtocart.yaml'))
fbmpaycart_dict = data.load_yaml(os.path.join(data_path,'fbmpaycart.yaml'))

@pytest.fixture(scope="class")
def shared_context(browser):
    """恢复登录态，并在该测试类中复用浏览器上下文。"""
    storage_state_path = FILE_PATH.get("set_cookies")
    context = browser.new_context(storage_state=storage_state_path) if storage_state_path and os.path.exists(storage_state_path) else browser.new_context()
    try:
        yield context
    finally:
        context.close()


@pytest.fixture(scope="class")
def shared_page(shared_context):
    """共享页面以保留购物车状态，测试类结束时再关闭。"""
    page = shared_context.new_page()
    try:
        yield page
    finally:
        page.close()


class Testfbmcart:
    """按“加入购物车 → FBM 支付”的顺序执行两条测试。"""

    @pytest.mark.skipif(cases_dict['loginpage'][0]['skip'] == True, reason='跳过执行')
    @pytest.mark.parametrize('CaseData', cases_dict['loginpage'])
    def test_fbmaddtocart(self, shared_page, run_case_fixture, CaseData):
        run_case_fixture(shared_page, CaseData)
        try:
            shared_page.wait_for_timeout(1000)
        except Exception as e:
            print(f'结果错误{e}')
            raise

    @pytest.mark.skipif(fbmpaycart_dict['loginpage'][0]['skip'] == True, reason='跳过执行')
    @pytest.mark.parametrize('CaseData', fbmpaycart_dict['loginpage'])
    def test_fbmpaycart(self, shared_page, run_case_fixture, CaseData):
        run_case_fixture(shared_page, CaseData)
        try:
            shared_page.wait_for_timeout(1000)
            assert_title(shared_page, CaseData["assertion"], CaseData["title"])
        except Exception as e:
            logs.error(f'断言结果为False，错误信息：{e}')
            raise

    # @pytest.mark.skipif(fbmpaycart_dict['loginpage'][0]['skip'] == True, reason='跳过执行')
    # @pytest.mark.parametrize('CaseData', fbmpaycart_dict['loginpage'])
    # def test_fbmpaycart(self, suite_page, run_case_fixture, CaseData):
    #     run_case_fixture(suite_page, CaseData)
    #     try:
    #         suite_page.wait_for_timeout(6000)
    #     except Exception as e:
    #         print(f'结果错误{e}')
    #         raise
