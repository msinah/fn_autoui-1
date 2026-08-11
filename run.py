"""简化的 pytest 启动入口。

直接运行本文件等价于在项目根目录执行 pytest，具体收集规则来自 pytest.ini。
"""

import pytest
import sys


if __name__ == '__main__':
    pytest.main()
