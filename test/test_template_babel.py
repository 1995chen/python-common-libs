# -*- coding: UTF-8 -*-


import os
import unittest
from typing import Optional

import inject
import template_logging
from template_babel import TemplateBabel, get_text as _

# 创建日志目录
os.makedirs('./logs/', exist_ok=True)
template_logging.init_logger()
logger = template_logging.getLogger(__name__)


class TestTemplateBabelMethods(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """
            进行该测试用例整体的初始化
        """

        def my_config(binder):
            binder.bind(TemplateBabel, TemplateBabel("messages", "./translations"))

        # 将实例绑定到inject
        inject.configure(my_config)

    @classmethod
    def tearDownClass(cls):
        # 清理
        inject.clear()

    def setUp(self):
        self.passed: bool = False
        self.translate_cfg: Optional[TemplateBabel] = inject.instance(TemplateBabel)
        # 定义初始值以及结果
        self.origin_text: Optional[str] = "hello"
        self.origin_en_text: Optional[str] = "hello"
        self.origin_zh_text: Optional[str] = "你好"

    def tearDown(self):
        # 销毁
        self.translate_cfg = None
        self.origin_text = None
        self.origin_en_text = None
        self.origin_zh_text = None
        # 打印结果
        logger.info(
            f"func {self.__class__.__name__}.{self._testMethodName}.........{'passed' if self.passed else 'failed'}"
        )

    def test_en_lang(self):
        self.translate_cfg.set_lang("en_US")
        self.assertEqual(self.origin_en_text, _(self.origin_text))
        self.passed = True

    def test_zh_lang(self):
        self.translate_cfg.set_lang("zh_CN")
        self.assertEqual(self.origin_zh_text, _(self.origin_text))
        self.passed = True

    def test_other_lang(self):
        """
        未知语言默认返回中文
        """
        self.translate_cfg.set_lang("other")
        self.assertEqual(self.origin_zh_text, _(self.origin_text))
        self.passed = True


if __name__ == '__main__':
    unittest.main()
