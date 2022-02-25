# -*- coding: UTF-8 -*-


import os
import unittest
import pickle
import codecs
from typing import Optional, Any, Callable, Dict

import inject
import template_logging
from template_cache import Cache

# 创建日志目录
os.makedirs('./logs/', exist_ok=True)
template_logging.init_logger()
logger = template_logging.getLogger(__name__)


class TestTemplateCacheMethods(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """
            进行该测试用例整体的初始化
        """
        # 存储缓存仓库
        cls.cache_store = dict()

        def get_cache_handler(key: str, timeout: Optional[int], **user_kwargs) -> Any:
            """
                获得缓存的handler
            """
            return cls.cache_store.get(key, None)

        def store_cache_handler(key: str, value: Any, timeout: Optional[int], **user_kwargs) -> Any:
            """
                存储cache的handler
            """
            cls.cache_store[key] = value

        def generate_cache_key_handler(func: Callable, *args: Any, **kwargs: Any) -> str:
            """
                生成缓存key
            """
            key_dict: Dict[str, Any] = {
                'module': object.__getattribute__(func, '__module__'),
                'func_name': func.__name__,
                'args': args,
                'kwargs': kwargs,
            }
            key: str = codecs.encode(pickle.dumps(key_dict), "base64").decode()
            return key

        def my_config(binder):
            cache_instance: Cache = Cache()
            # 设置handler
            cache_instance.set_get_cache_handler(get_cache_handler)
            cache_instance.set_store_cache_handler(store_cache_handler)
            cache_instance.set_generate_cache_key_handler(generate_cache_key_handler)
            binder.bind(Cache, cache_instance)

        # 将实例绑定到inject
        inject.configure(my_config)

    @classmethod
    def tearDownClass(cls):
        # 清理
        inject.clear()
        cls.cache_store = None

    def setUp(self):
        self.passed: bool = False
        self.cache: Optional[Cache] = inject.instance(Cache)

    def tearDown(self):
        # 销毁
        self.cache = None
        # 打印结果
        logger.info(
            f"func {self.__class__.__name__}.{self._testMethodName}.........{'passed' if self.passed else 'failed'}"
        )

    def test_unuse_cache(self):
        @self.cache.use_cache()
        def test_add_func(a: int, b: int):
            """
            这是一个测试方法，接下来会对该方法进行缓存
            """
            return a + b

        self.assertEqual(len(self.cache_store), 0)
        self.assertEqual(test_add_func(1, 2), 3)
        self.assertEqual(len(self.cache_store), 1)
        self.passed = True

    def test_use_cache(self):
        # 自定义异常
        class MyException(Exception):
            pass

        @self.cache.use_cache()
        def test_add_func(a: int, b: int):
            """
            这是一个测试方法，接下来会对该方法进行缓存
            """
            raise MyException()

        self.assertEqual(test_add_func(1, 2), 3)
        # 清除缓存
        self.cache_store.clear()
        # 断言预期的异常
        with self.assertRaises(MyException):
            test_add_func(1, 2)

        self.passed = True


if __name__ == '__main__':
    unittest.main()
