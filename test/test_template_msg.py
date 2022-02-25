# -*- coding: UTF-8 -*-


import os
import unittest
from typing import Optional, Any, Dict
from datetime import datetime

import inject
import template_logging
from template_msg import LarkClient, ILarkMsgResult, IReceiveIDType

# 创建日志目录
os.makedirs('./logs/', exist_ok=True)
template_logging.init_logger()
logger = template_logging.getLogger(__name__)


class TestTemplateMsgMethods(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """
            进行该测试用例整体的初始化
        """
        # 测试邮箱
        cls.test_mail: str = 'chenl2448365088@gmail.com'
        cls.json_template: Dict[str, Any] = {
            "config": {
                "wide_screen_mode": True
            },
            "header": {
                "title": {
                    "tag": "plain_text",
                    "content": "该消息来自单元测试"
                }
            },
            "elements": [
                {
                    "tag": "hr"
                },
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"项目: python-common-libs\n当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    }
                },
                {
                    "tag": "action",
                    "actions": [
                        {
                            "tag": "button",
                            "text": {
                                "tag": "plain_text",
                                "content": "象征性的按钮"
                            },
                            "type": "primary",
                            "url": ""
                        }
                    ]
                }
            ]
        }
        # 存储缓存仓库
        cls.cache_store: Dict[str, Any] = dict()

        def store_cache_handler(key: str, value: Any, timeout: Optional[int]) -> Any:
            """
            存储cache的handler
            """
            # 存储缓存
            cls.cache_store[key] = value

        def get_cache_handler(key: str) -> Any:
            """
            获得缓存的handler
            """
            _value: Any = cls.cache_store.get(key, None)
            return _value

        def my_config(binder):
            # 这是一个测试的飞书账号
            client: LarkClient = LarkClient(
                app_id="cli_a292c56398fa900c",
                app_secret="HuLcM8OJ4LRHos678o5k3cvLVMcgPaJZ"
            )
            # 配置handler
            client.set_store_cache_handler(store_cache_handler)
            client.set_get_cache_handler(get_cache_handler)
            binder.bind(LarkClient, client)

        # 将实例绑定到inject
        inject.configure(my_config)

    @classmethod
    def tearDownClass(cls):
        # 清理
        inject.clear()
        cls.cache_store = None

    def setUp(self):
        self.passed: bool = False
        self.lark_client: Optional[LarkClient] = inject.instance(LarkClient)

    def tearDown(self):
        # 销毁
        self.lark_client = None
        # 打印结果
        logger.info(
            f"func {self.__class__.__name__}.{self._testMethodName}.........{'passed' if self.passed else 'failed'}"
        )

    def test_send_test_msg(self):
        """
        测试发送文本消息
        """
        # 获得open_id
        open_id: str = self.lark_client.get_user_open_id(self.test_mail)
        # 发送文本消息
        send_res: ILarkMsgResult = self.lark_client.send_text_msg(
            IReceiveIDType.OPEN_ID, open_id, "今晚7点下班留下来开个会[UNITTEST]"
        )
        self.assertEqual(send_res.code, 0)

        self.passed = True

    def test_send_interactive_msg(self):
        """
        测试发送卡片消息
        """
        # 获得open_id
        open_id: str = self.lark_client.get_user_open_id(self.test_mail)
        # 发送文本消息
        self.json_template['elements'][1]['text']['content'] = (
            f"项目: python-common-libs\n"
            f"当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        send_res: ILarkMsgResult = self.lark_client.send_interactive_msg(
            IReceiveIDType.OPEN_ID, open_id,
            self.json_template
        )
        self.assertEqual(send_res.code, 0)

        self.passed = True

    def test_reply_text_msg(self):
        """
        测试回复文本消息
        """
        # 获得open_id
        open_id: str = self.lark_client.get_user_open_id(self.test_mail)
        # 发送文本消息
        send_res: ILarkMsgResult = self.lark_client.send_text_msg(
            IReceiveIDType.OPEN_ID, open_id, "今晚7点下班留下来开个会,收到请回答[UNITTEST]"
        )
        self.assertEqual(send_res.code, 0)
        # 回复消息
        reply_res: ILarkMsgResult = self.lark_client.reply_text_msg(send_res.data.message_id, "好的,冲冲冲")
        self.assertEqual(reply_res.code, 0)

        self.passed = True

    def test_reply_interactive_msg(self):
        """
        测试回复卡片消息
        """
        # 获得open_id
        open_id: str = self.lark_client.get_user_open_id(self.test_mail)
        # 发送卡片消息
        self.json_template['elements'][1]['text']['content'] = (
            f"项目: python-common-libs\n"
            f"当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"备注: 收到请回答!"
        )
        send_res: ILarkMsgResult = self.lark_client.send_interactive_msg(
            IReceiveIDType.OPEN_ID, open_id,
            self.json_template
        )
        self.assertEqual(send_res.code, 0)

        # 回复卡片消息
        self.json_template['elements'][1]['text']['content'] = (
            f"项目: python-common-libs\n"
            f"当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"备注: 收到, 冲冲冲!"
        )
        reply_res: ILarkMsgResult = self.lark_client.reply_interactive_msg(
            send_res.data.message_id,
            self.json_template
        )
        self.assertEqual(reply_res.code, 0)

        self.passed = True

    def test_revoke_msg(self):
        """
        测试撤回消息
        """
        # 获得open_id
        open_id: str = self.lark_client.get_user_open_id(self.test_mail)
        # 发送文本消息
        send_res: ILarkMsgResult = self.lark_client.send_text_msg(
            IReceiveIDType.OPEN_ID, open_id, "冲冲冲[UNITTEST]"
        )
        self.assertEqual(send_res.code, 0)

        # 撤回消息
        revoke_res: ILarkMsgResult = self.lark_client.revoke_msg(send_res.data.message_id)
        self.assertEqual(revoke_res.code, 0)

        self.passed = True


if __name__ == '__main__':
    unittest.main()
