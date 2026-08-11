# -*- coding:utf-8 -*-
"""控制台彩色日志与滚动文件日志配置。"""

import logging
import os
import time
from configs.setting import FILE_PATH
from logging.handlers import RotatingFileHandler  # 按文件大小滚动备份
import colorlog

# 导入模块时确保日志目录存在，并按日期创建当天的日志文件。
logs_path = FILE_PATH['log']
if not os.path.exists(logs_path):
    os.mkdir(logs_path)


logfile_name = logs_path + r'\test.{}.log'.format(time.strftime('%Y%m%d'))

class HandleLogs:
    """创建全项目复用的 logger，避免每次导入都重复添加 Handler。"""

    @classmethod
    def setting_log_color(cls):
        """创建仅用于控制台输出的彩色格式器。"""
        log_color_config = {
            'DEBUG': 'cyan',
            'INFO': 'green',
            'ERROR': 'red',
            'WARNING': 'yellow',
            'CRITICAL': 'red'
        }
        formatter = colorlog.ColoredFormatter('%(log_color)s %(levelname)s - %(asctime)s - %(filename)s:%(lineno)d -[%(module)s:%(funcName)s] - %(message)s',
                                  log_colors=log_color_config)
        return formatter

    @classmethod
    def output_logs(cls):
        """配置控制台及滚动文件输出，并返回 logger。"""
        logger = logging.getLogger(__name__)
        steam_format = cls.setting_log_color()
        # 防止重复打印日志
        if not logger.handlers:
            logger.setLevel(logging.DEBUG)
            log_format = logging.Formatter('%(levelname)s - %(asctime)s - %(filename)s:%(lineno)d -[%(module)s:%(funcName)s] - %(message)s')
            # 把日志信息输出到控制台
            sh = logging.StreamHandler()
            sh.setLevel(logging.DEBUG)
            sh.setFormatter(steam_format)
            logger.addHandler(sh)

            # 把日志输出到文件里面
            fh = RotatingFileHandler(filename=logfile_name,mode='a',maxBytes=5242880,backupCount=7,encoding='utf-8')
            fh.setLevel(logging.DEBUG)
            fh.setFormatter(log_format)
            logger.addHandler(fh)

        return logger

# 其他模块统一通过 ``from ...recordlog import logs`` 使用此单例。
handle = HandleLogs()
logs = handle.output_logs()


# logs.info('这是info的日志级别')
# logs.error('这是error日志信息')
# logs.debug('这是debug日志信息')
# logs.warning('这是警告日志信息')
# logs.critical('这是严重的日志信息')

