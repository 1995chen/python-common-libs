# -*- coding: UTF-8 -*-


import os
import unittest
from uuid import uuid1

import template_logging


class TestTemplateLoggingMethods(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """
            进行该测试用例整体的初始化
        """
        # 生成本次日志打印附带的uuid字符串
        cls.uuid_string: str = str(uuid1())
        cls.log_path: str = './logs/'
        # 创建目录
        os.makedirs(cls.log_path, exist_ok=True)
        # 初始化
        template_logging.init_logger('./config/log.ini')
        cls.logger = template_logging.getLogger(__name__)

    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        self.passed: bool = False

    def tearDown(self):
        # 打印结果
        self.logger.info(
            f"func {self.__class__.__name__}.{self._testMethodName}.........{'passed' if self.passed else 'failed'}"
        )

    def test_debug_log(self):
        log_text = f"this is debug {self.uuid_string}"
        self.logger.debug(log_text)

        found: bool = False
        # 查看文件是否有该日志
        with open("./logs/debug.log") as f:
            while True:
                line: str = f.readline()
                if not line:
                    break
                if line.find(log_text) != -1:
                    found = True
                    break
        self.assertEqual(found, True)

        self.passed = True

    def test_info_log(self):
        log_text = f"this is info {self.uuid_string}"
        self.logger.info(log_text)

        found: bool = False
        # 查看文件是否有该日志
        with open("./logs/info.log") as f:
            while True:
                line: str = f.readline()
                if not line:
                    break
                if line.find(log_text) != -1:
                    found = True
                    break
        self.assertEqual(found, True)

        self.passed = True

    def test_warning_log(self):
        log_text = f"this is warning {self.uuid_string}"
        self.logger.warning(log_text)

        found: bool = False
        # 查看文件是否有该日志
        with open("./logs/warning.log") as f:
            while True:
                line: str = f.readline()
                if not line:
                    break
                if line.find(log_text) != -1:
                    found = True
                    break
        self.assertEqual(found, True)

        self.passed = True

    def test_error_log(self):
        """
        未知语言默认返回中文
        """
        log_text = f"this is error {self.uuid_string}"
        self.logger.error(log_text)

        found: bool = False
        # 查看文件是否有该日志
        with open("./logs/error.log") as f:
            while True:
                line: str = f.readline()
                if not line:
                    break
                if line.find(log_text) != -1:
                    found = True
                    break
        self.assertEqual(found, True)

        self.passed = True


if __name__ == '__main__':
    unittest.main()
