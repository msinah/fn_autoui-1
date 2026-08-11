"""pytest 的全局配置与 UI 自动化执行核心。

pytest 会自动加载根目录中的 conftest.py，因此测试文件无需显式导入它。
这里集中管理浏览器生命周期、YAML 步骤执行、失败诊断、Allure 报告和结果通知。
"""

import pytest
import allure
import os
import json
from configs.setting import RunConfig, is_dd_msg
import time
from datetime import timedelta
from urllib.parse import urlsplit, urlunsplit
from unit_tools.ding_rebot import send_dd_msg


# ==================== 浏览器生命周期 ====================
@pytest.fixture(scope="session")
def browser(playwright):
    """整个测试会话只启动一次 Chromium 浏览器，并在结束时关闭。"""
    browser = playwright.chromium.launch(headless=False)
    yield browser
    browser.close()

# ==================== YAML 定位器解析 ====================
def _normalize_selector(locator: str) -> str:
    """规范 CSS/XPath 定位器，并给裸 XPath 自动补上 ``xpath=`` 前缀。"""
    if locator is None:
        return locator
    locator = str(locator).strip()
    if not locator:
        return locator
    if locator.startswith("xpath=") or locator.startswith("css=") or locator.startswith("text="):
        return locator
    if locator.startswith("/") or locator.startswith("//") or locator.startswith("("):
        return f"xpath={locator}"
    return locator


def _resolve_get_by_locator(page, locator_spec: str):
    """安全解析 YAML 中形如 get_by_text(...) 的 Playwright 定位器。

    使用 AST 白名单而不是 eval，避免 YAML 内容执行任意 Python 代码。
    """
    if locator_spec is None:
        return None
    text = str(locator_spec).strip()
    if not text:
        return None
    text = text.lstrip("\ufeff")
    if not text.startswith("get_by_"):
        return None

    import ast

    allowed = {
        "get_by_placeholder",
        "get_by_text",
        "get_by_role",
        "get_by_label",
        "get_by_test_id",
        "get_by_title",
        "get_by_alt_text",
    }
    try:
        node = ast.parse(text, mode="eval").body
        def eval_expr(expr):
            if isinstance(expr, ast.Call):
                if isinstance(expr.func, ast.Name):
                    method = expr.func.id
                    if method not in allowed:
                        return None
                    args = []
                    for a in expr.args:
                        if not isinstance(a, ast.Constant):
                            return None
                        args.append(a.value)
                    kwargs = {}
                    for kw in expr.keywords or []:
                        if kw.arg is None:
                            return None
                        if not isinstance(kw.value, ast.Constant):
                            return None
                        kwargs[kw.arg] = kw.value.value
                    fn = getattr(page, method, None)
                    if fn is None:
                        return None
                    return fn(*args, **kwargs)

                if isinstance(expr.func, ast.Attribute):
                    base = eval_expr(expr.func.value)
                    if base is None:
                        return None
                    attr = expr.func.attr
                    if attr == "filter":
                        if expr.args:
                            return None
                        kwargs = {}
                        for kw in expr.keywords or []:
                            if kw.arg is None:
                                return None
                            if not isinstance(kw.value, ast.Constant):
                                return None
                            kwargs[kw.arg] = kw.value.value
                        return base.filter(**kwargs)
                    if attr == "nth":
                        if len(expr.args) != 1 or expr.keywords:
                            return None
                        a = expr.args[0]
                        if not isinstance(a, ast.Constant):
                            return None
                        return base.nth(int(a.value))
                    return None
                return None

            if isinstance(expr, ast.Attribute):
                base = eval_expr(expr.value)
                if base is None:
                    return None
                if expr.attr in {"first", "last"}:
                    return getattr(base, expr.attr)
                return None

            return None

        return eval_expr(node)
    except Exception:
        return None


def _resolve_case_locator(page, case: dict):
    """尝试把单个 YAML 步骤中的 locator 解析为 Locator 对象。"""
    raw_locator = case.get("locator")
    if not raw_locator:
        return None, ""
    get_by_locator = _resolve_get_by_locator(page, raw_locator)
    if get_by_locator is not None:
        return get_by_locator, raw_locator
    return None, raw_locator


def _resolve_locator_spec(page, locator_spec):
    """返回可执行定位器，以及用于日志和报错的原始定位器描述。"""
    get_by_locator = _resolve_get_by_locator(page, locator_spec)
    if get_by_locator is not None:
        return get_by_locator, str(locator_spec)
    return _normalize_selector(locator_spec), str(locator_spec or "")


# ==================== 页面诊断与操作后等待 ====================
def _visible_texts(page, selector, limit=12):
    """提取指定选择器命中的可见文本，供失败诊断使用。"""
    try:
        texts = page.locator(selector).evaluate_all(
            """(nodes, limit) => nodes
                .filter(node => {
                    const style = window.getComputedStyle(node);
                    const box = node.getBoundingClientRect();
                    return style.display !== 'none'
                        && style.visibility !== 'hidden'
                        && box.width > 0
                        && box.height > 0;
                })
                .slice(0, limit)
                .map(node => (node.innerText || node.textContent || '').trim())
                .filter(Boolean)""",
            limit,
        )
    except Exception:
        return []
    return [text for text in texts if text]


def _page_diagnostics(page):
    """收集当前 URL、标题以及常见页面错误提示。"""
    try:
        title = page.title()
    except Exception:
        title = ""
    try:
        url = page.url
    except Exception:
        url = ""

    selectors = [
        ".el-message",
        ".el-message-box__wrapper",
        ".el-dialog__wrapper:not([style*='display: none'])",
        ".el-form-item__error",
        ".is-error",
        ".el-tooltip__popper",
        ".el-popover",
        "[role='alert']",
    ]
    messages = []
    for selector in selectors:
        for text in _visible_texts(page, selector):
            messages.append(f"{selector}: {text}")

    detail = [f"url={url}", f"title={title}"]
    if messages:
        detail.append("visible_messages:")
        detail.extend(f"- {message}" for message in messages[:20])
    else:
        detail.append("visible_messages: none")
    return "\n".join(detail)


def _fail_with_page_diagnostics(page, message):
    """把诊断信息附加到 Allure，然后让当前 pytest 用例失败。"""
    detail = _page_diagnostics(page)
    allure.attach(detail, name="页面诊断信息", attachment_type=allure.attachment_type.TEXT)
    pytest.fail(f"{message}\n{detail}")


def _wait_after_click(page, case: dict):
    """按 YAML 配置等待点击后的目标元素出现；未配置时不额外等待。"""
    wait_locator = case.get("wait_after_locator") or case.get("wait_for_locator")
    if not wait_locator:
        return

    timeout = case.get("wait_after_timeout") or case.get("wait_for_timeout") or 10000
    try:
        timeout = int(timeout)
    except Exception:
        timeout = 10000

    locator_obj, locator_desc = _resolve_locator_spec(page, wait_locator)
    try:
        if hasattr(locator_obj, "wait_for"):
            locator_obj.wait_for(state="visible", timeout=timeout)
        else:
            page.wait_for_selector(locator_obj, state="visible", timeout=timeout)
    except Exception as e:
        step_name = case.get("name") or case.get("method") or "click"
        _fail_with_page_diagnostics(
            page,
            f"点击步骤后未出现预期结果: step={step_name} wait_locator={locator_desc} timeout={timeout} error={e}",
        )


def _format_allure_step(case: dict) -> str:
    """把 YAML 步骤整理成便于阅读的 Allure 步骤标题。"""
    name = str(case.get("name") or case.get("method") or "未命名步骤")
    method = case.get("method")
    details = []
    for key in ("url", "locator", "value", "key", "press"):
        value = case.get(key)
        if value not in (None, ""):
            details.append(f"{key}={value}")
    if method and method != name:
        details.insert(0, f"method={method}")
    return f"{name} ({', '.join(details)})" if details else name


# ==================== 失败截图 ====================
def _is_playwright_page(value):
    """通过关键方法判断某个 fixture 参数是否为 Playwright Page。"""
    return all(hasattr(value, attr) for attr in ("screenshot", "url", "title"))


def _attach_failure_screenshot(item):
    """查找测试参数中的 Page，并把全页截图与 URL 附加到 Allure。"""
    pages = []
    for name, value in getattr(item, "funcargs", {}).items():
        if _is_playwright_page(value):
            pages.append((name, value))

    for name, page in pages:
        try:
            title = page.title()
        except Exception:
            title = ""
        try:
            url = page.url
        except Exception:
            url = ""
        attachment_name = f"失败截图-{name}"
        if title:
            attachment_name = f"{attachment_name}-{title}"
        try:
            screenshot = page.screenshot(full_page=True)
            allure.attach(
                screenshot,
                name=attachment_name,
                attachment_type=allure.attachment_type.PNG,
            )
            if url:
                allure.attach(
                    url,
                    name=f"失败页面地址-{name}",
                    attachment_type=allure.attachment_type.TEXT,
                )
        except Exception as e:
            allure.attach(
                f"截图失败: {e}\nurl: {url}\ntitle: {title}",
                name=f"失败截图异常-{name}",
                attachment_type=allure.attachment_type.TEXT,
            )


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """pytest 每阶段结束时触发；测试主体失败时自动截图。"""
    outcome = yield
    report = outcome.get_result()
    if report.when == "call" and report.failed:
        _attach_failure_screenshot(item)


# ==================== Allure 结果后处理 ====================
def _clear_allure_parameters(config):
    """清除参数化产生的冗长 parameters，使报告展示更简洁。"""
    report_dir = (
        getattr(config.option, "allure_report_dir", None)
        or os.getenv("ALLURE_RESULTS_DIR")
        or os.path.join(os.getcwd(), "report", "temp")
    )
    if not report_dir or not os.path.isdir(report_dir):
        return

    for filename in os.listdir(report_dir):
        if not filename.endswith("-result.json"):
            continue
        path = os.path.join(report_dir, filename)
        try:
            with open(path, "r", encoding="utf-8") as file:
                result = json.load(file)
            if result.get("parameters"):
                result["parameters"] = []
                with open(path, "w", encoding="utf-8") as file:
                    json.dump(result, file, ensure_ascii=False)
        except Exception:
            continue


def _has_label(labels, name):
    return any(label.get("name") == name for label in labels)


def _behavior_values_from_result(result):
    """从结果标题、描述和 suite 推导 Allure 的 feature/story。"""
    title = str(result.get("name") or "").strip()
    description = str(result.get("description") or "").strip()
    labels = result.get("labels") or []
    suite = ""
    for label in labels:
        if label.get("name") == "suite":
            suite = str(label.get("value") or "").strip()
            break

    feature = title.split("|", 1)[0].strip() if "|" in title else title
    story = description or title or suite or "UI"
    feature = feature or suite or "UI"
    return feature, story


def _ensure_allure_behavior_labels(config):
    """给缺少行为标签的 Allure 结果补上 feature 和 story。"""
    report_dir = (
        getattr(config.option, "allure_report_dir", None)
        or os.getenv("ALLURE_RESULTS_DIR")
        or os.path.join(os.getcwd(), "report", "temp")
    )
    if not report_dir or not os.path.isdir(report_dir):
        return

    for filename in os.listdir(report_dir):
        if not filename.endswith("-result.json"):
            continue
        path = os.path.join(report_dir, filename)
        try:
            with open(path, "r", encoding="utf-8") as file:
                result = json.load(file)
            labels = result.setdefault("labels", [])
            feature, story = _behavior_values_from_result(result)
            changed = False
            if not _has_label(labels, "feature"):
                labels.append({"name": "feature", "value": feature})
                changed = True
            if not _has_label(labels, "story"):
                labels.append({"name": "story", "value": story})
                changed = True
            if changed:
                with open(path, "w", encoding="utf-8") as file:
                    json.dump(result, file, ensure_ascii=False)
        except Exception:
            continue


def pytest_sessionfinish(session, exitstatus):
    """测试会话结束后统一整理 Allure JSON 结果。"""
    _clear_allure_parameters(session.config)
    _ensure_allure_behavior_labels(session.config)


# ==================== YAML 关键字执行器 ====================
@pytest.fixture
def run_case_fixture():
    """返回 YAML 用例执行函数。

    测试调用 ``run_case_fixture(page, CaseData)`` 后，这里会逐条执行
    ``CaseData["cases"]``。每条 case 的 method 就是动作关键字，例如
    goto、click、fill、press、hover 或 wait_for_timeout。
    """
    # 匹配并搜集（在元组中）所有包含位置的函数
    def run_step(case, func, *value):
        """执行普通 Playwright 方法，并包装成一个 Allure 步骤。"""
        with allure.step(_format_allure_step(case)):
            func(*value)


    def run_case(page, testdata):
        """解释一组 YAML 数据，执行完成后返回最终 Page 或 Frame。"""
        cases = testdata['cases']
        if testdata.get("title"):
            title = str(testdata["title"])
            allure.dynamic.title(title)
            allure.dynamic.feature(title.split("|", 1)[0].strip() or title)
        if testdata.get("des"):
            des = str(testdata["des"])
            allure.dynamic.description(des)
            allure.dynamic.story(des)
        # current_page 会随弹窗或 Frame 切换而改变，page 保留原始页面。
        current_page = page
        try:
            # 遍历cases
            for case in cases:
                func_name = case['method']
                # 判断method如果为goto，则重新拼接url地址
                if func_name == "goto":
                    # YAML 可以只写相对路径，运行时会与 baseUrl 拼成完整地址。
                    expected_url = str(case.get('url', '')).strip()
                    raw_url = str(case.get('url', '')).strip()
                    raw_url = raw_url.strip('`').strip()
                    if raw_url.startswith("http://") or raw_url.startswith("https://"):
                        case['url'] = raw_url
                    else:
                        base = str(RunConfig.baseUrl).rstrip("/")
                        path = raw_url if raw_url.startswith("/") else f"/{raw_url}"
                        case['url'] = f"{base}{path}"
                    with allure.step(_format_allure_step(case)):
                        current_page.goto(case['url'])
                        current_page.wait_for_load_state('networkidle')
                        if expected_url and ("/fnHome" not in expected_url) and ("/fnHome" in current_page.url):
                            pytest.fail(f"页面可能未登录/被重定向：期望 {expected_url}，实际 {current_page.url}")
                    continue
                switch = case['switch_to_page']
                # switch_to_page == 1且method==click时打开新的tab
                if switch == 1:
                    if func_name == "click":
                        # 通过with page.expect_popup()语句捕获弹出窗口对象
                        with current_page.expect_popup() as popup_info:
                            # 动态获取到current_page对象中具有相应名称的属性或方法，然后将其赋值给变量func
                            func = current_page.__getattribute__(func_name)
                            # case.values()可以获取case字典中的所有值并转换成list
                            caselist = list(case.values())
                            # 传递参数时解包，caselist[3:]表示从索引为3的位置开始获取列表元素
                            run_step(case, func, *caselist[3:])
                        # 然后将弹出窗口对象赋值给current_page变量
                        current_page = popup_info.value  # 获取弹出窗口对象
                # switch_to_page == 2 时跳转到新的frame框架
                elif switch == 2:
                    func_name = case['method']
                    func = current_page.__getattribute__(func_name)
                    caselist = list(case.values())
                    run_step(case, func, *caselist[3:])  # 传递参数时解包
                    if func_name == "frame":
                        frame_name = case['locator']
                        current_page = current_page.frame(frame_name)  # 切换到指定的框架
                # switch_to_page == 3 时跳出frame框架
                elif switch == 3:
                    with allure.step(_format_allure_step(case)):
                        current_page = page
                # switch_to_page == 其他 时不进行任何处理
                else:
                    func_name = case['method']
                    # click/fill/press 单独处理，以便先等待元素可见，并兼容
                    # 普通 CSS/XPath 和 get_by_* 两种定位器写法。
                    if func_name == "click":
                        get_by_locator, locator_desc = _resolve_case_locator(current_page, case)
                        if get_by_locator is not None:
                            try:
                                get_by_locator.wait_for(state="visible")
                            except Exception as e:
                                try:
                                    title = current_page.title()
                                except Exception:
                                    title = ""
                                pytest.fail(
                                    f"元素未出现或不可见，无法点击：locator={locator_desc} url={current_page.url} title={title} error={e}"
                                )
                            times = case.get("times", 1)
                            if times is None:
                                times = 1
                            try:
                                times = int(times)
                            except Exception:
                                times = 1
                            if times < 1:
                                times = 1
                            with allure.step(_format_allure_step(case)):
                                for _ in range(times):
                                    get_by_locator.click()
                            _wait_after_click(current_page, case)
                            continue

                        raw_locator = case.get("locator")
                        locator = _normalize_selector(raw_locator)
                        if locator:
                            try:
                                current_page.wait_for_selector(locator, state="visible")
                            except Exception as e:
                                try:
                                    title = current_page.title()
                                except Exception:
                                    title = ""
                                pytest.fail(
                                    f"元素未出现或不可见，无法点击：locator={locator} url={current_page.url} title={title} error={e}"
                                )
                            times = case.get("times", 1)
                            if times is None:
                                times = 1
                            try:
                                times = int(times)
                            except Exception:
                                times = 1
                            if times < 1:
                                times = 1
                            with allure.step(_format_allure_step(case)):
                                for _ in range(times):
                                    current_page.click(locator)
                            _wait_after_click(current_page, case)
                            continue
                    if func_name == "fill":
                        get_by_locator, locator_desc = _resolve_case_locator(current_page, case)
                        value = case.get("value", "")
                        if get_by_locator is not None:
                            try:
                                get_by_locator.wait_for(state="visible")
                            except Exception as e:
                                try:
                                    title = current_page.title()
                                except Exception:
                                    title = ""
                                pytest.fail(
                                    f"元素未出现或不可见，无法输入：locator={locator_desc} url={current_page.url} title={title} error={e}"
                                )
                            with allure.step(_format_allure_step(case)):
                                get_by_locator.fill(str(value))
                                press = case.get("press")
                                if press:
                                    get_by_locator.press(str(press))
                            continue

                        raw_locator = case.get("locator")
                        locator = _normalize_selector(raw_locator)
                        if locator:
                            try:
                                current_page.wait_for_selector(locator, state="visible")
                            except Exception as e:
                                try:
                                    title = current_page.title()
                                except Exception:
                                    title = ""
                                pytest.fail(
                                    f"元素未出现或不可见，无法输入：locator={locator} url={current_page.url} title={title} error={e}"
                                )
                            with allure.step(_format_allure_step(case)):
                                current_page.fill(locator, str(value))
                                press = case.get("press")
                                if press:
                                    current_page.press(locator, str(press))
                            continue
                    if func_name == "press":
                        get_by_locator, locator_desc = _resolve_case_locator(current_page, case)
                        key = case.get("key", None)
                        if key is None:
                            key = case.get("value", None)
                        if key is None:
                            key = case.get("press", None)
                        if key is None:
                            pytest.fail("press步骤缺少 key/value/press 参数")
                        if get_by_locator is not None:
                            try:
                                get_by_locator.wait_for(state="visible")
                            except Exception as e:
                                try:
                                    title = current_page.title()
                                except Exception:
                                    title = ""
                                pytest.fail(
                                    f"元素未出现或不可见，无法按键：locator={locator_desc} url={current_page.url} title={title} error={e}"
                                )
                            with allure.step(_format_allure_step(case)):
                                get_by_locator.press(str(key))
                            continue

                        raw_locator = case.get("locator")
                        locator = _normalize_selector(raw_locator)
                        if locator:
                            try:
                                current_page.wait_for_selector(locator, state="visible")
                            except Exception as e:
                                try:
                                    title = current_page.title()
                                except Exception:
                                    title = ""
                                pytest.fail(
                                    f"元素未出现或不可见，无法按键：locator={locator} url={current_page.url} title={title} error={e}"
                                )
                            with allure.step(_format_allure_step(case)):
                                current_page.press(locator, str(key))
                            continue
                    # 其他关键字（如 hover、wait_for_timeout）按 method 名反射调用。
                    # 参数取自 YAML 字段顺序，因此不要随意在动作字段中间插入元数据。
                    func = current_page.__getattribute__(func_name)
                    caselist = list(case.values())
                    run_step(case, func, *caselist[3:])  # 传递参数时解析包
        except Exception as e:
            pytest.fail('用例执行失败,{}'.format(e))
        return current_page
    return run_case

# ==================== 终端汇总与通知 ====================
def format_duration(seconds):
    """将秒数转换为时分秒格式"""
    return str(timedelta(seconds=seconds)).split('.')[0]

def _duration_seconds_from_delta(delta):
    if delta is None:
        return None
    total_seconds = getattr(delta, "total_seconds", None)
    if callable(total_seconds):
        try:
            return float(total_seconds())
        except Exception:
            return None
    seconds = getattr(delta, "seconds", None)
    if isinstance(seconds, (int, float)):
        return float(seconds)
    if hasattr(delta, "__float__"):
        try:
            return float(delta)
        except Exception:
            return None
    return None


def _replace_url_host(url, public_host):
    if not url or not public_host:
        return url
    try:
        parts = urlsplit(url)
        public_parts = urlsplit(public_host if "://" in public_host else f"{parts.scheme}://{public_host}")
        netloc = public_parts.netloc or parts.netloc
        scheme = public_parts.scheme or parts.scheme
        return urlunsplit((scheme, netloc, parts.path, parts.query, parts.fragment))
    except Exception:
        return url


def _get_allure_report_url():
    configured_url = os.getenv("ALLURE_REPORT_URL")
    if configured_url:
        return configured_url

    public_allure_url = os.getenv("PUBLIC_ALLURE_REPORT_URL")
    if public_allure_url:
        return public_allure_url

    build_url = os.getenv("BUILD_URL")
    if build_url:
        public_host = (
            os.getenv("JENKINS_PUBLIC_HOST")
            or os.getenv("JENKINS_PUBLIC_URL")
            or os.getenv("JENKINS_PUBLIC_BASE_URL")
            or "http://192.168.2.27:8080"
        )
        public_build_url = _replace_url_host(build_url, public_host)
        return f"{public_build_url.rstrip('/')}/allure/#behaviors"

    return RunConfig.NEW_REPORT or "未配置，请以 allure serve 启动后控制台输出的地址为准"

def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """
    Pytest框架里面预定义的钩子函数，用于在测试结束后自动收集测试结果
    :param terminalreporter:
    :param exitstatus:
    :param config:
    :return:
    """
    # print(terminalreporter.stats)
    testcase_total = terminalreporter._numcollected
    passed_num = len(terminalreporter.stats.get('passed', []))
    failed_num = len(terminalreporter.stats.get('failed', []))
    error_num = len(terminalreporter.stats.get('error', []))
    skip_num = len(terminalreporter.stats.get('skipped', []))
    duration_seconds = 0
    session_starttime = getattr(terminalreporter, "_sessionstarttime", None)
    if isinstance(session_starttime, (int, float)):
        duration_seconds = time.time() - float(session_starttime)
    else:
        session_start = getattr(terminalreporter, "_session_start", None)
        session_stop = getattr(terminalreporter, "_session_stop", None)
        if session_start is not None and session_stop is not None:
            duration_seconds = _duration_seconds_from_delta(session_stop - session_start) or 0
    duration = round(duration_seconds, 2)
    formatted_duration = format_duration(duration)

    # 统计通过率、失败率、错误率
    pass_rate = f"{(passed_num / testcase_total) * 100:.0f}%" if testcase_total > 0 else "N/A"
    failed_rate = f"{(failed_num / testcase_total) * 100:.0f}%" if testcase_total > 0 else "N/A"
    error_rate = f"{(error_num / testcase_total) * 100:.0f}%" if testcase_total > 0 else "N/A"
    allure_report_url = _get_allure_report_url()

    summary = f"""
    自动化测试结果，通知如下，具体执行结果：
    测试用例总数：{testcase_total}
    测试用例通过数：{passed_num}   
    通过率：{pass_rate}
    测试用例失败数：{failed_num}   
    失败率：{failed_rate}
    测试用例错误数：{error_num}    
    错误率：{error_rate}
    测试用例跳过数：{skip_num}
    执行总时长：{duration}s ({formatted_duration})
    allure报告：{allure_report_url}
    """
    print(summary)
    if is_dd_msg:
        try:
            dd_result = send_dd_msg(summary)
            print(f"DingTalk notice result: {dd_result}")
        except Exception as e:
            print(f"DingTalk notice failed: {e}")
