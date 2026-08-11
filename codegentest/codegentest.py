"""Playwright Codegen 生成的原始操作脚本示例。

该文件用于保留或调试录制结果，不会被 pytest.ini 当作正式测试用例收集。
"""

import re
from playwright.sync_api import Playwright, sync_playwright, expect


def run(playwright: Playwright) -> None:
    """启动浏览器并按 Codegen 生成的顺序回放页面操作。"""
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    page.goto("http://front.fnconsumertest.com/fnHome")
    page.get_by_role("button", name="登录").click()
    page.get_by_role("textbox", name="账号/手机号").click()
    page.get_by_role("textbox", name="账号/手机号").fill("18859666666")
    page.get_by_role("textbox", name="请输入登录密码").click()
    page.get_by_role("textbox", name="请输入登录密码").fill("a123654")
    page.get_by_label("密码登录").get_by_role("button", name="登录").click()
    page.locator("iframe[name=\"https://turing.captcha.qcloud.com\"]").content_frame.locator("div").filter(has_text=re.compile(r"^&nbsp;$")).click()
    page.locator("#t_mask").click()
    page.locator("iframe[name=\"https://turing.captcha.qcloud.com\"]").content_frame.locator("div").filter(has_text=re.compile(r"^&nbsp;$")).click()
    page.locator("iframe[name=\"https://turing.captcha.qcloud.com\"]").content_frame.locator("div").filter(has_text=re.compile(r"^&nbsp;$")).click()
    page.locator("iframe[name=\"https://turing.captcha.qcloud.com\"]").content_frame.locator("div").filter(has_text=re.compile(r"^&nbsp;$")).click()
    page.locator("#t_mask").click()
    page.locator("iframe[name=\"https://turing.captcha.qcloud.com\"]").content_frame.locator("div").filter(has_text=re.compile(r"^&nbsp;$")).click()
    page.locator("iframe[name=\"https://turing.captcha.qcloud.com\"]").content_frame.get_by_label("拖动下方滑块完成拼图").nth(3).click()
    page.locator("iframe[name=\"https://turing.captcha.qcloud.com\"]").content_frame.get_by_label("拖动下方滑块完成拼图").nth(3).click()
    page.locator("iframe[name=\"https://turing.captcha.qcloud.com\"]").content_frame.locator("div").filter(has_text=re.compile(r"^&nbsp;$")).click()
    page.locator("#t_mask").click()
    page.locator("iframe[name=\"https://turing.captcha.qcloud.com\"]").content_frame.locator("div").filter(has_text=re.compile(r"^&nbsp;$")).click()

    # ---------------------
    context.close()
    browser.close()


with sync_playwright() as playwright:
    run(playwright)
