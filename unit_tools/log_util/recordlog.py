# -*- coding:utf-8 -*-
import logging
import os
import time
from configs.setting import FILE_PATH
from logging.handlers import RotatingFileHandler  # 按文件大小滚动备份
import colorlog

logs_path = FILE_PATH['log']
if not os.path.exists(logs_path):
    os.mkdir(logs_path)


logfile_name = logs_path + r'\test.{}.log'.format(time.strftime('%Y%m%d'))

class HandleLogs:

    @classmethod
    def setting_log_color(cls):
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

handle = HandleLogs()
logs = handle.output_logs()


# logs.info('这是info的日志级别')
# logs.error('这是error日志信息')
# logs.debug('这是debug日志信息')
# logs.warning('这是警告日志信息')
# logs.critical('这是严重的日志信息')

