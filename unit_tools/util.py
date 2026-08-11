"""时间、命令执行和跨平台路径处理等基础工具。"""

import datetime
import subprocess
import os
from typing import Text

def get_nowtime():
    """返回适合写入日志的当前时间字符串。"""
    # now_time = datetime.datetime.now()
    now_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    return now_time


def invoke(cmd):
    """执行 shell 命令并返回标准输出文本。"""
    output, errors = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
    o = output.decode("utf-8")
    return o


def root_path():
    """返回项目根目录。"""
    path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return path


def ensure_path_sep(path: Text) -> Text:
    """统一 Windows/Linux 路径分隔符，并转换成项目内绝对路径。"""
    if "/" in path:
        path = os.sep.join(path.split("/"))

    if "\\" in path:
        path = os.sep.join(path.split("\\"))

    return root_path() + path


if __name__ == '__main__':
    print(ensure_path_sep('/Auth'))
