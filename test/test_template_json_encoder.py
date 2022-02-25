# -*- coding: UTF-8 -*-


import os
import unittest
import json
from datetime import datetime, timedelta, date
from decimal import Decimal
from uuid import uuid1, uuid4
from enum import Enum
from dataclasses import dataclass

import inject
import numpy
import template_logging
from template_babel import LazyString, TemplateBabel
from template_json_encoder import TemplateJSONEncoder

# 创建日志目录
os.makedirs('./logs/', exist_ok=True)
template_logging.init_logger()
logger = template_logging.getLogger(__name__)


class TestTemplateJsonEncoderMethods(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """
            进行该测试用例整体的初始化
        """

        def my_config(binder):
            binder.bind(TemplateBabel, TemplateBabel("messages", "./translations"))

        # 将实例绑定到inject
        inject.configure(my_config)

        cls.default = TemplateJSONEncoder().default

    @classmethod
    def tearDownClass(cls):
        # 清理
        inject.clear()
        cls.default = None

    def setUp(self):
        self.passed: bool = False

    def tearDown(self):
        # 打印结果
        logger.info(
            f"func {self.__class__.__name__}.{self._testMethodName}.........{'passed' if self.passed else 'failed'}"
        )

    def test_time(self):
        dt = datetime.now()
        json_string = json.dumps({'result': dt}, default=self.default)
        self.assertEqual(json.loads(json_string)['result'], str(dt))

        tl = timedelta(hours=12, minutes=25, seconds=9)
        json_string = json.dumps({'result': tl}, default=self.default)
        self.assertEqual(json.loads(json_string)['result'], str(tl))

        d = date(dt.year, dt.month, dt.day)
        json_string = json.dumps({'result': d}, default=self.default)
        self.assertEqual(json.loads(json_string)['result'], str(d))

        self.passed = True

    def test_decimal(self):
        target = Decimal("1.12349")
        json_string = json.dumps({'result': target}, default=self.default)
        self.assertEqual(json.loads(json_string)['result'], float(target))
        self.passed = True

    def test_uuid(self):
        target = uuid1()
        json_string = json.dumps({'result': target}, default=self.default)
        self.assertEqual(json.loads(json_string)['result'], str(target))

        target = uuid4()
        json_string = json.dumps({'result': target}, default=self.default)
        self.assertEqual(json.loads(json_string)['result'], str(target))

        self.passed = True

    def test_lazy_string(self):
        target = LazyString("123")
        json_string = json.dumps({'result': target}, default=self.default)
        self.assertEqual(json.loads(json_string)['result'], str(target))

        self.passed = True

    def test_enum(self):
        # 定义一个枚举
        class MyEnum(Enum):
            YEAR = 'hello'
            MONTH = 'name'

        target = MyEnum.MONTH
        json_string = json.dumps({'result': target}, default=self.default)
        self.assertEqual(json.loads(json_string)['result'], target.value)

        self.passed = True

    def test_dataclass(self):
        # 定义一个dataclass

        @dataclass
        class MyDataClass:
            name: str = "1"
            year: int = 2009

        target = MyDataClass()
        json_string = json.dumps({'result': target}, default=self.default)
        self.assertEqual(json.loads(json_string)['result']['name'], target.name)
        self.assertEqual(json.loads(json_string)['result']['year'], target.year)

        self.passed = True

    def test_ndarray(self):
        target = numpy.array([1, 2, 3], dtype='int8')
        json_string = json.dumps({'result': target}, default=self.default)
        self.assertEqual(json.loads(json_string)['result'], target.tolist())

        self.passed = True


if __name__ == '__main__':
    unittest.main()
