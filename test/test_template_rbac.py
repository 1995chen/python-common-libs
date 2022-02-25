# -*- coding: UTF-8 -*-


import os
import unittest

import inject
import template_logging
from template_rbac import OAuth2SSO
from flask import Flask, make_response

# 创建日志目录
os.makedirs('./logs/', exist_ok=True)
template_logging.init_logger()
logger = template_logging.getLogger(__name__)


class TestTemplateRbacMethods(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """
            进行该测试用例整体的初始化
        """

        def my_config(binder):
            oauth2_instance: OAuth2SSO = OAuth2SSO(
                client_id="flask_template",
                client_secret="34ddefb0-4063-40db-9b93-4b12b81cc147",
                authorization_endpoint="https://sso.local.domain/auth/realms/production/protocol/openid-connect/auth",
                token_endpoint="https://sso.local.domain/auth/realms/production/protocol/openid-connect/token",
                userinfo_endpoint="https://sso.local.domain/auth/realms/production/protocol/openid-connect/userinfo",
                app_root_url="http://127.0.0.1:8080/",
                api_auth_path="/api/login",
                api_logout_path="/api/logout",
                jwt_secret="123asd13"
            )
            # 设置初始化方法
            binder.bind(OAuth2SSO, oauth2_instance)

        # 将实例绑定到inject
        inject.configure(my_config)

        app = Flask(__name__)

        @app.route('/', methods=['GET'])
        def info():
            return make_response({
                'hello': "hello",
            })

        sso_instance = inject.instance(OAuth2SSO)
        # 注册
        app.register_blueprint(sso_instance.get_resources())

        logger.info(f"auth url is {sso_instance.sso_auth_url}")
        # 该测试用例暂不支持自动化
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
