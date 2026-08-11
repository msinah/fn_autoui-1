"""YAML 测试数据读取工具。"""

import yaml
from configs import *
from unit_tools.log_util.recordlog import logs


class ReadData(object):
    """读取 YAML 文件并转换为 Python 字典或列表。"""

    def __init__(self):
        pass

    def load_yaml(self, file_path):
        """按 UTF-8 编码加载 YAML，并记录加载过程。"""
        logs.info("加载 {} 文件...".format(file_path))
        with open(file_path, encoding='utf-8') as f:
            data = yaml.safe_load(f)
        logs.info("读到数据-->{}".format(data))
        return data

# 模块级单例：测试文件导入 data 后即可直接调用 data.load_yaml(...)。
data = ReadData()

if __name__ == '__main__':
    data = ReadData()
    print(data.load_yaml('../../data/login.yaml'))
