"""SHEIN 汇出模板新增并删除流程。"""

import copy
import os
import time

import pytest

from configs.setting import FILE_PATH
from unit_tools.assert_control import *
from unit_tools.handle_data.read_data import data


data_path = FILE_PATH["cmout"]
# 一份 YAML 描述完整业务步骤，测试文件只负责动态数据和最终断言。
addshopshein_dict = data.load_yaml(os.path.join(data_path, "addshopshein.yaml"))


def _replace_placeholders(value, replacements):
    """递归替换 YAML 字典、列表和字符串中的动态占位符。"""
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
    """创建类级浏览器上下文，并在存在时载入已保存的登录态。"""
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
    """同一测试类复用一个页面，结束后统一关闭。"""
    page = shared_context.new_page()
    try:
        yield page
    finally:
        page.close()


class TestCmoutAddShop:
    """验证模板的新建、使用和删除完整链路。"""

    @pytest.mark.skipif(addshopshein_dict["loginpage"][0]["skip"] == True, reason="跳过执行")
    @pytest.mark.parametrize("CaseData", addshopshein_dict["loginpage"])
    def test_addshopshein(self, shared_page, run_case_fixture, CaseData):
        """替换唯一名称后执行 YAML，并检查删除提示和页面标题。"""
        # 深拷贝可避免参数原对象被占位符替换永久修改。
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
