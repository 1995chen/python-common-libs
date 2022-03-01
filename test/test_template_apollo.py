# -*- coding: UTF-8 -*-


import os
import unittest
from typing import Dict, Any, List
from dataclasses import dataclass, Field, asdict

import inject
import template_logging
from dacite import from_dict
from dacite.dataclasses import get_fields
from template_apollo import ApolloClient
from flask import Flask, make_response

# 创建日志目录
os.makedirs('./logs/', exist_ok=True)
template_logging.init_logger()
logger = template_logging.getLogger(__name__)


class TestTemplateApolloMethods(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """
            进行该测试用例整体的初始化
        """

        @dataclass
        class Config:
            NAME: str = None
            DB: str = None

        @inject.autoparams()
        def init_config(apollo_client: ApolloClient) -> Config:
            _fields: List[Field] = get_fields(Config)
            config_dict: Dict[str, Any] = dict()
            for _field in _fields:
                _v: Any = apollo_client.get_value(_field.name)
                if _v:
                    # 类型转换
                    config_dict[_field.name] = _field.type(_v)
            _config = from_dict(Config, config_dict)
            return _config

        def init_apollo() -> ApolloClient:
            def config_changed_handler(entry: Dict[str, Any]) -> Any:
                logger.info(f"get entry: {entry}")
                # 获取阿波罗实例
                apollo_client: ApolloClient = inject.instance(ApolloClient)
                # 重新绑定配置
                inject.clear_and_configure(my_config)
                # 停止当前线程
                apollo_client.stop()

            _instance: ApolloClient = ApolloClient(
                app_id="unittest",
                config_server_url="http://apollo.local.domain:13043"
            )
            _instance.set_config_changed_handler(config_changed_handler)
            _instance.start()
            return _instance

        def my_config(binder):
            binder.bind_to_constructor(ApolloClient, init_apollo)
            binder.bind_to_constructor(Config, init_config)

        # 将实例绑定到inject
        # inject.configure(my_config)

        app = Flask(__name__)

        @app.route('/', methods=['GET'])
        def info():
            config: Config = inject.instance(Config)
            return make_response(asdict(config))

        # # 该测试用例暂不支持自动化
        # app.run("0.0.0.0", 8080)

    @classmethod
    def tearDownClass(cls):
        # 清理
        inject.clear()

    def setUp(self):
        self.passed: bool = False

    def tearDown(self):
        # 打印结果
        logger.info(
            f"func {self.__class__.__name__}.{self._testMethodName}.........{'passed' if self.passed else 'failed'}"
        )

    def test_transaction_decorator(self):
        """
        测试事务注解
        """

        self.passed = True


if __name__ == '__main__':
    unittest.main()
