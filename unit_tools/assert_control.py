from typing import Any
from playwright.sync_api import Page
from unit_tools.log_util.recordlog import logs

def assert_title(page: Page, assertion: str, title: str):
    """
    1. 断言title是否一致
    2. assert_title(page, CaseData["assertion"], CaseData["title"])
    :param page:
    :param assertion:
    :param title:
    :return:
    """
    try:
        actual_title = page.title().strip()
        expected_title = str(assertion).strip()
        assert actual_title == expected_title
        logs.info(f"断言结果为True, 页面标题与预期一致: 用例={title}, 预期={expected_title}, 实际={actual_title}")
    except AssertionError as e:
        actual_title = page.title().strip()
        expected_title = str(assertion).strip()
        logs.error(f"断言结果为False, 页面标题与预期不一致: 用例={title}, 预期={expected_title}, 实际={actual_title}, 错误信息: {e}")
        raise


def assert_element_exists(page, element_locator, element_description):
    """
    1、检查元素是否存在
    2、assert_element_exists(page, CaseData["assertion"], CaseData["title"])
    """
    if not page.query_selector(element_locator):
        logs.error(f"断言结果为False，元素不存在：{element_description}")
        raise AssertionError(f"Element not found: {element_description}")
    logs.info(f"断言结果为True，元素存在：{element_description}")


def assert_text_equal(actual_text: str, expected_text: str, description: str):
    """
    1、检查文本是否相等
    2、assert_text_equal(actual_text, expected_text, description)
    3、实例：
        assert_text_equal(page.inner_text(CaseData["assertion"]), "马楼楼", CaseData["title"])
    """
    try:
        assert actual_text == expected_text
        logs.info(f"断言结果为True，文本一致：{description}")
    except AssertionError as e:
        logs.error(f"断言结果为False，文本不一致：{description}，错误信息: {e}")
        raise


def assert_equal(actual: Any, expected: Any, message: str = ""):
    """
    1、断言两个值相等
    2、assert_equal(2 + 2, 4, "2 + 2 不等于 4")
    3、实例：
        assert_equal(page.inner_text(CaseData["assertion"]), "马楼楼1", CaseData["title"])
    """
    if actual != expected:
        error_message = f"AssertionError: {message}\nExpected: {expected}\nActual: {actual}"
        logs.error(error_message)
        raise AssertionError(error_message)
    else:
        logs.info(f"断言结果为True")


def assert_true(condition: bool, message: str = ""):
    """
    1、断言条件为真
    2、assert_true(page.title() == "Login Page", "页面标题错误")
    """
    if not condition:
        error_message = f"AssertionError: {message}"
        logs.error(error_message)
        raise AssertionError(error_message)
    else:
        logs.info("断言结果为True")


# def assert_false(condition: bool, message: str = ""):
#     """
#     断言条件为假
#     assert_false(page.query_selector("#error-message").is_visible(), "错误消息应该不可见")
#     """
#     if condition:
#         error_message = f"AssertionError: {message}"
#         logs.error(error_message)
#         raise AssertionError(error_message)
#     else:
#         logs.info("断言结果为True")


def assert_element_visible(page, element_locator, element_description):
    """
    1、断言元素可见
    2、assert_element_visible(page, CaseData["assertion"], "错误消息应该不可见")
    """
    element = page.query_selector(element_locator)
    if not element or not element.is_visible():
        error_message = f"AssertionError: Element '{element_description}' is not visible"
        logs.error(error_message)
        raise AssertionError(error_message)
    else:
        logs.info(f"断言结果为True，元素可见：{element_description}")
