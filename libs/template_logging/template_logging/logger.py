# -*- coding: UTF-8 -*-


import os
import logging
from logging.config import fileConfig

logging_config = (
        os.getenv('LOG_CONFIG_PATH') or
        os.path.join(os.path.dirname(__file__), 'log.ini')
)


def init_logger(log_config_file=None):
    """
    加载日志配置
    :param log_config_file:
    :return:
    """
    if log_config_file:
        fileConfig(log_config_file, disable_existing_loggers=False)
    else:
        fileConfig(logging_config, disable_existing_loggers=False)


def getLogger(name=None) -> logging.Logger:
    """
    保持向下兼容, 保留该方法
    :param name:
    :return:
    """
    return logging.getLogger(name)
