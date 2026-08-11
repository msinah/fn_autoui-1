# 我的产品亚马逊汇出流程
import os

import pytest

from configs.setting import FILE_PATH
from unit_tools.assert_control import *
from unit_tools.handle_data.read_data import data


data_path = FILE_PATH["cmout"]
cmoutamazon_dict = data.load_yaml(os.path.join(data_path, "cmoutamazon.yaml"))
cmoutwalmart_dict = data.load_yaml(os.path.join(data_path, "cmoutwalmart.yaml"))
cmoutdefaultstore_dict = data.load_yaml(os.path.join(data_path, "cmoutdefaultstore.yaml"))
cmouttemuhalf_dict = data.load_yaml(os.path.join(data_path, "cmouttemuhalf.yaml"))
cmoutshein_dict = data.load_yaml(os.path.join(data_path, "cmoutshein.yaml"))
cmouttiktok_dict = data.load_yaml(os.path.join(data_path, "cmouttiktok.yaml"))


@pytest.fixture(scope="class")
def shared_context(browser):
    storage_state_path = FILE_PATH.get("set_cookies")
    context = (
        browser.new_context(storage_state=storage_state_path)
        if storage_state_path and os.path.exists(storage_state_path)
        else browser.new_context()
    )
    try:
        yield context
    finally:
        context.close()


@pytest.fixture(scope="class")
def shared_page(shared_context):
    page = shared_context.new_page()
    try:
        yield page
    finally:
        page.close()


class TestAmazonOut:
    @pytest.mark.skipif(cmoutamazon_dict["loginpage"][0]["skip"] == True, reason="跳过执行")
    @pytest.mark.parametrize("CaseData", cmoutamazon_dict["loginpage"])
    def test_cmoutamazon(self, shared_page, run_case_fixture, CaseData):
        current_page = run_case_fixture(shared_page, CaseData)
        try:
            current_page.wait_for_timeout(1000)
            if CaseData.get("success_assertion"):
                current_page.wait_for_selector(CaseData["success_assertion"], state="visible", timeout=10000)
                assert_element_visible(current_page, CaseData["success_assertion"], "亚马逊汇出成功提示")
            assert_title(current_page, CaseData["assertion"], CaseData["title"])
        except Exception as e:
            logs.error(f"断言结果为False，错误信息：{e}")
            raise

    @pytest.mark.skipif(cmoutwalmart_dict["loginpage"][0]["skip"] == True, reason="跳过执行")
    @pytest.mark.parametrize("CaseData", cmoutwalmart_dict["loginpage"])
    def test_cmoutwalmart(self, shared_page, run_case_fixture, CaseData):
        current_page = run_case_fixture(shared_page, CaseData)
        try:
            current_page.wait_for_timeout(1000)
            if CaseData.get("success_assertion"):
                current_page.wait_for_selector(CaseData["success_assertion"], state="visible", timeout=10000)
                assert_element_visible(current_page, CaseData["success_assertion"], "沃尔玛汇出成功提示")
            assert_title(current_page, CaseData["assertion"], CaseData["title"])
        except Exception as e:
            logs.error(f"断言结果为False，错误信息：{e}")
            raise

    @pytest.mark.skipif(cmoutdefaultstore_dict["loginpage"][0]["skip"] == True, reason="跳过执行")
    @pytest.mark.parametrize("CaseData", cmoutdefaultstore_dict["loginpage"])
    def test_cmoutdefaultstore(self, shared_page, run_case_fixture, CaseData):
        current_page = run_case_fixture(shared_page, CaseData)
        try:
            current_page.wait_for_timeout(1000)
            if CaseData.get("success_assertion"):
                current_page.wait_for_selector(CaseData["success_assertion"], state="visible", timeout=10000)
                assert_element_visible(current_page, CaseData["success_assertion"], "通用店铺汇出成功提示")
            assert_title(current_page, CaseData["assertion"], CaseData["title"])
        except Exception as e:
            logs.error(f"断言结果为False，错误信息：{e}")
            raise

    @pytest.mark.skipif(cmouttemuhalf_dict["loginpage"][0]["skip"] == True, reason="跳过执行")
    @pytest.mark.parametrize("CaseData", cmouttemuhalf_dict["loginpage"])
    def test_cmouttemuhalf(self, shared_page, run_case_fixture, CaseData):
        current_page = run_case_fixture(shared_page, CaseData)
        try:
            current_page.wait_for_timeout(1000)
            if CaseData.get("success_assertion"):
                current_page.wait_for_selector(CaseData["success_assertion"], state="visible", timeout=10000)
                assert_element_visible(current_page, CaseData["success_assertion"], "temu半托管汇出成功提示")
            assert_title(current_page, CaseData["assertion"], CaseData["title"])
        except Exception as e:
            logs.error(f"断言结果为False，错误信息：{e}")
            raise

    @pytest.mark.skipif(cmoutshein_dict["loginpage"][0]["skip"] == True, reason="跳过执行")
    @pytest.mark.parametrize("CaseData", cmoutshein_dict["loginpage"])
    def test_cmoutshein(self, shared_page, run_case_fixture, CaseData):
        current_page = run_case_fixture(shared_page, CaseData)
        try:
            current_page.wait_for_timeout(1000)
            if CaseData.get("success_assertion"):
                current_page.wait_for_selector(CaseData["success_assertion"], state="visible", timeout=10000)
                assert_element_visible(current_page, CaseData["success_assertion"], "shein汇出成功提示")
            assert_title(current_page, CaseData["assertion"], CaseData["title"])
        except Exception as e:
            logs.error(f"断言结果为False，错误信息：{e}")
            raise

    @pytest.mark.skipif(cmouttiktok_dict["loginpage"][0]["skip"] == True, reason="跳过执行")
    @pytest.mark.parametrize("CaseData", cmouttiktok_dict["loginpage"])
    def test_cmouttiktok(self, shared_page, run_case_fixture, CaseData):
        current_page = run_case_fixture(shared_page, CaseData)
        try:
            current_page.wait_for_timeout(1000)
            if CaseData.get("success_assertion"):
                current_page.wait_for_selector(CaseData["success_assertion"], state="visible", timeout=10000)
                assert_element_visible(current_page, CaseData["success_assertion"], "tiktok汇出成功提示")
            assert_title(current_page, CaseData["assertion"], CaseData["title"])
        except Exception as e:
            logs.error(f"断言结果为False，错误信息：{e}")
            raise


