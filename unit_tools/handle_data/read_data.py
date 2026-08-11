import yaml
from configs import *
from unit_tools.log_util.recordlog import logs

class ReadData(object):
    """读取 yaml 文件中的数据"""
    def __init__(self):
        pass

    # 读取yaml文件
    def load_yaml(self,file_path):
        logs.info("加载 {} 文件...".format(file_path))
        with open(file_path, encoding='utf-8') as f:
            data = yaml.safe_load(f)
        logs.info("读到数据-->{}".format(data))
        return data


data = ReadData()

if __name__ == '__main__':
    data = ReadData()
    print(data.load_yaml('../../data/login.yaml'))