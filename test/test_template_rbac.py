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

        # 这里以keycloak为例
        # keycloak配置查看地址
        # https://sso.local.domain/auth/realms/{realm}/.well-known/openid-configuration
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
                jwt_secret="abcd1234"
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
        # sso_instance.refresh_token(
        #     "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9."
        #     "eyJpYXQiOjE2NDYwMzQ3MzksImlzcyI6Imh0dHBzOi8vZmxhc2stdGVtcGxhdGUubG9jYWwu"
        #     "ZG9tYWluIiwianRpIjoiOWE2ZWI0NGQtNTBjZi00YmZmLWFkYzUtYjJiYWM1ZDY5ZDdjIiwi"
        #     "ZGF0YSI6eyJhY2Nlc3NfdG9rZW4iOiJleUpoYkdjaU9pSlNVekkxTmlJc0luUjVjQ0lnT2lB"
        #     "aVNsZFVJaXdpYTJsa0lpQTZJQ0pJTUdwdWVXUkRhRzVsVERoSE5HRnJUakZITlZGcE1VMDFV"
        #     "VnB1Ym5Sck5ERktjMWhDU3pSeFRVRnpJbjAuZXlKbGVIQWlPakUyTkRZd016VXdNemtzSW1s"
        #     "aGRDSTZNVFkwTmpBek5EY3pPU3dpWVhWMGFGOTBhVzFsSWpveE5qUTJNRE15T1RRMExDSnFk"
        #     "R2tpT2lJeU4yVTVZVGxqT0Mxa1lqQXpMVFJsWXpRdE9URTRNUzA0WlRCa1lqWmpZakZpTjJV"
        #     "aUxDSnBjM01pT2lKb2RIUndjem92TDNOemJ5NXNiMk5oYkM1a2IyMWhhVzR2WVhWMGFDOXla"
        #     "V0ZzYlhNdmNISnZaSFZqZEdsdmJpSXNJbUYxWkNJNld5SnlaV0ZzYlMxdFlXNWhaMlZ0Wlc1"
        #     "MElpd2ljbUZ1WTJobGNpSXNJbWhoY21KdmNpSXNJbUp5YjJ0bGNpSXNJbUZqWTI5MWJuUWlY"
        #     "U3dpYzNWaUlqb2lOekUyWm1FMk9ESXRaVE5tTUMwMFltTTBMVGc1WmpndFpUSTROV0k1TnpN"
        #     "ME1HUTVJaXdpZEhsd0lqb2lRbVZoY21WeUlpd2lZWHB3SWpvaVpteGhjMnRmZEdWdGNHeGhk"
        #     "R1VpTENKelpYTnphVzl1WDNOMFlYUmxJam9pTVdGak1qUmhaR010TldRM1pDMDBNMkZpTFdJ"
        #     "NU5qZ3RZVEptTmpVNU1HVmlORGd6SWl3aVlXTnlJam9pTUNJc0ltRnNiRzkzWldRdGIzSnBa"
        #     "Mmx1Y3lJNld5SXZLaUpkTENKeVpXRnNiVjloWTJObGMzTWlPbnNpY205c1pYTWlPbHNpYjJa"
        #     "bWJHbHVaVjloWTJObGMzTWlMQ0oxYldGZllYVjBhRzl5YVhwaGRHbHZiaUpkZlN3aWNtVnpi"
        #     "M1Z5WTJWZllXTmpaWE56SWpwN0luSmxZV3h0TFcxaGJtRm5aVzFsYm5RaU9uc2ljbTlzWlhN"
        #     "aU9sc2lkbWxsZHkxcFpHVnVkR2wwZVMxd2NtOTJhV1JsY25NaUxDSjJhV1YzTFhKbFlXeHRJ"
        #     "aXdpYldGdVlXZGxMV2xrWlc1MGFYUjVMWEJ5YjNacFpHVnljeUlzSW1sdGNHVnljMjl1WVhS"
        #     "cGIyNGlMQ0p5WldGc2JTMWhaRzFwYmlJc0ltTnlaV0YwWlMxamJHbGxiblFpTENKdFlXNWha"
        #     "MlV0ZFhObGNuTWlMQ0p4ZFdWeWVTMXlaV0ZzYlhNaUxDSjJhV1YzTFdGMWRHaHZjbWw2WVhS"
        #     "cGIyNGlMQ0p4ZFdWeWVTMWpiR2xsYm5Seklpd2ljWFZsY25rdGRYTmxjbk1pTENKdFlXNWha"
        #     "MlV0WlhabGJuUnpJaXdpYldGdVlXZGxMWEpsWVd4dElpd2lkbWxsZHkxbGRtVnVkSE1pTENK"
        #     "MmFXVjNMWFZ6WlhKeklpd2lkbWxsZHkxamJHbGxiblJ6SWl3aWJXRnVZV2RsTFdGMWRHaHZj"
        #     "bWw2WVhScGIyNGlMQ0p0WVc1aFoyVXRZMnhwWlc1MGN5SXNJbkYxWlhKNUxXZHliM1Z3Y3lK"
        #     "ZGZTd2ljbUZ1WTJobGNpSTZleUp5YjJ4bGN5STZXeUprWVhSaFltRnpaU0lzSW1SbFptRjFi"
        #     "SFFpTENKemVYTjBaVzBpTENKd2NtOWtkV04wYVc5dUlpd2laR1YyWld4dmNDSXNJbVJoYzJo"
        #     "aWIyRnlaQ0pkZlN3aWFHRnlZbTl5SWpwN0luSnZiR1Z6SWpwYkltRmtiV2x1SWwxOUxDSmlj"
        #     "bTlyWlhJaU9uc2ljbTlzWlhNaU9sc2ljbVZoWkMxMGIydGxiaUpkZlN3aVlXTmpiM1Z1ZENJ"
        #     "NmV5SnliMnhsY3lJNld5SnRZVzVoWjJVdFlXTmpiM1Z1ZENJc0luWnBaWGN0WVhCd2JHbGpZ"
        #     "WFJwYjI1eklpd2lkbWxsZHkxamIyNXpaVzUwSWl3aWJXRnVZV2RsTFdGalkyOTFiblF0Ykds"
        #     "dWEzTWlMQ0p0WVc1aFoyVXRZMjl1YzJWdWRDSXNJblpwWlhjdGNISnZabWxzWlNKZGZYMHNJ"
        #     "bk5qYjNCbElqb2laVzFoYVd3Z2NISnZabWxzWlNJc0ltVnRZV2xzWDNabGNtbG1hV1ZrSWpw"
        #     "bVlXeHpaU3dpYm1GdFpTSTZJa3hwWVc1bklFTm9aVzRpTENKd2NtVm1aWEp5WldSZmRYTmxj"
        #     "bTVoYldVaU9pSmphR1Z1YkdsaGJtY2lMQ0puYVhabGJsOXVZVzFsSWpvaVRHbGhibWNpTENK"
        #     "bVlXMXBiSGxmYm1GdFpTSTZJa05vWlc0aUxDSmxiV0ZwYkNJNkltTm9aVzVzTWpRME9ETTJO"
        #     "VEE0T0VCbmJXRnBiQzVqYjIwaWZRLmVtNGpRM2NLMlctaXBzSWpDUkdtZTA3ak5raElmQXdq"
        #     "RmViZ3Q5djY5dHFsaGtKS1VRazNTRnVIcHoycHlUQThuZ2YxZlFaNXRYdHB6S2JnLVBvTlVm"
        #     "WDZJVHg4SXZEN3ZxY3pRQzdqVGVaLTBibHFLM3FjbVhHRnVVTVBMUmN3dVBkZjZuZl9vYU5Z"
        #     "Ym8wQUo0a0ctMmRGMkVqZk9CSzZuX2VvNG5hRFBMRW52ejA2UnZ0eFRuTm94U3FrTk9JSDZS"
        #     "R3dDS2QzSTU5dTVTQVNZT2lhRUE5ZVJsdWM3NWJOeVBrUlpoaTl5RlFhaDhIeXR4YlM0MXVy"
        #     "UVZNREZVdTFGcnVoYVEzbFN5RkpZc3lCcUlQOFRjT2QybVlPY1NXV0JTWEl1TkI0eHBMTHRT"
        #     "RklsUEZ3N0tsMGZUemliSmRYaDNUSkM3X0djdDE5bEt0WTVxS0lYdyIsImV4cGlyZXNfYXQi"
        #     "OjE2NDYwMzQ3MzksInVzZXJuYW1lIjoiY2hlbmxpYW5nIiwiZW1haWwiOiJjaGVubDI0NDgz"
        #     "NjUwODhAZ21haWwuY29tIn0sImV4cCI6MTY0NjEyMTEzOX0.hd0lL4Px61yL9elovMD3A_Ne"
        #     "bgHydLTBxDvK-RBGd5U"
        # )
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
