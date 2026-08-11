# shein汇出模板新增并删除流程
import copy
import os
import time

import pytest

from configs.setting import FILE_PATH
from unit_tools.assert_control import *
from unit_tools.handle_data.read_data import data


data_path = FILE_PATH["cmout"]
addshopshein_dict = data.load_yaml(os.path.join(data_path, "addshopshein.yaml"))


def _replace_placeholders(value, replacements):
    if isinstance(value, dict):
        return {key: _replace_placeholders(val, replacements) for key, val in value.items()}
    if isinstance(value, list):
        return [_replace_placeholders(item, replacements) for item in value]
    if isinstance(value, str):
        for key, replacement in replacements.items():
            value = value.replace(key, replacement)
    return value


@pytest.fixture(scope="class")
def shared_context(browser):
    storage_state_path = FILE_PATH.get("set_cookies")
    context_kwargs = {"viewport": {"width": 2503, "height": 1322}}
    if storage_state_path and os.path.exists(storage_state_path):
        context_kwargs["storage_state"] = storage_state_path
    context = browser.new_context(**context_kwargs)
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


class TestCmoutAddShop:
    @pytest.mark.skipif(addshopshein_dict["loginpage"][0]["skip"] == True, reason="跳过执行")
    @pytest.mark.parametrize("CaseData", addshopshein_dict["loginpage"])
    def test_addshopshein(self, shared_page, run_case_fixture, CaseData):
        case_data = copy.deepcopy(CaseData)
        suffix = time.strftime("%Y%m%d%H%M%S")
        case_data = _replace_placeholders(case_data, {"{{template_suffix}}": suffix})

        current_page = run_case_fixture(shared_page, case_data)
        try:
            current_page.wait_for_timeout(1000)
            if case_data.get("delete_success_assertion"):
                current_page.wait_for_selector(case_data["delete_success_assertion"], state="visible", timeout=10000)
                assert_element_visible(current_page, case_data["delete_success_assertion"], "shein模板删除成功提示")
            assert_title(current_page, case_data["assertion"], case_data["title"])
        except Exception as e:
            logs.error(f"断言结果为False，错误信息：{e}")
            raise
