# -*- coding: UTF-8 -*-


import os
import pickle
import logging
import json
from typing import Optional, Callable, Any, Dict, List, Set

import requests
from dacite import from_dict, Config
from template_exception import (
    HandlerUnCallableException, KeyParamsTypeInvalidException, KeyParamsValueInvalidException,
    RemoteServerException, KeyParamsValueOutOfRangeException
)

from .enum import ICacheKey, IMessageType, IReceiveIDType
from .model import ILarkMsgResult, ILarkMsgData

logger = logging.getLogger(__name__)


class LarkClient:
    # 单次查询最大数量
    MAX_COUNT_PER_QUERY = 50

    def __init__(
            self, app_id: str, app_secret: str,
            cache_timeout: int = 86400, token_timeout: Optional[int] = None,
    ):
        """
        初始化方法
        app_id: 飞书APP ID
        app_secret: 飞书APP Secret
        cache_timeout: 客户端缓存信息超时时间,默认为1天
        token_timeout: tenant_access_token超时时间,默认使用飞书返回的超时时间
        """
        # 飞书APP ID
        self.app_id = app_id
        # 飞书APP 密钥
        self.app_secret = app_secret
        self.token_timeout = token_timeout
        self.cache_timeout = cache_timeout
        # 设定缓存的handler
        self.store_cache_handler: Optional[Callable] = None
        # 获取缓存handler
        self.get_cache_handler: Optional[Callable] = None

    def set_store_cache_handler(self, handler: Callable) -> None:
        """
        设置存储缓存的handler
        :param handler: 可执行的方法
        :return:
        """
        if not callable(handler):
            raise HandlerUnCallableException(f"{type(self).__name__}.set_store_cache_handler")
        self.store_cache_handler = handler

    def set_get_cache_handler(self, handler: Callable) -> None:
        """
        设置获得缓存的handler
        :param handler: 可执行的方法
        :return:
        """
        if not callable(handler):
            raise HandlerUnCallableException(f"{type(self).__name__}.set_get_cache_handler")
        self.get_cache_handler = handler

    @staticmethod
    def __check_param_type(require_type: type, **kwargs) -> None:
        """
        校验参数类型
        :param kwargs:
        :return:
        """

        for _k, _v in kwargs.items():
            if not isinstance(_v, require_type):
                raise KeyParamsTypeInvalidException(_k, require_type)

    @staticmethod
    def __check_param_empty(**kwargs) -> None:
        """
        校验参数是否为空
        :param kwargs:
        :return:
        """
        for _k, _v in kwargs.items():
            if not _v:
                raise KeyParamsValueInvalidException(_k, _v)

    def __get_key_full_name(self, key: str) -> str:
        """
        获得key的缓存全名称
        :param key: 原始key名称
        :return: 存储在数据库中的key名称
        """
        return f"{type(self).__name__}.{self.app_id}.{key}"

    def __set_cache(self, key: str, value: Any, timeout: Optional[int]) -> None:
        """
        存储缓存
        :param key: 键
        :param value: 结果
        :param timeout: 超时时间
        :return:
        """
        # 判断类型
        self.__check_param_type(str, key=key)
        # 判断空值
        self.__check_param_empty(key=key)
        # 执行回调方法
        if callable(self.store_cache_handler):
            return self.store_cache_handler(self.__get_key_full_name(key), pickle.dumps(value), timeout)

    def __get_cache(self, key: str) -> Any:
        """
        查询缓存
        :param key: 键
        :return:
        """
        # 判断类型
        self.__check_param_type(str, key=key)
        # 判断空值
        self.__check_param_empty(key=key)
        # 执行回调方法
        if callable(self.get_cache_handler):
            _value: Any = None
            # noinspection PyBroadException
            try:
                _data_bytes: Any = self.get_cache_handler(self.__get_key_full_name(key))
                # 对bytes数据进行解码
                if isinstance(_data_bytes, bytes):
                    _value = pickle.loads(_data_bytes)
            except Exception:
                logger.warning(f"failed to get cache {key}", exc_info=True)
            return _value
        return None

    def get_tenant_access_token(self, force_reload: bool = False) -> str:
        """
        获取token
        :param force_reload: 强制获取
        :return:
        """
        _tenant_access_token: Optional[str] = self.__get_cache(ICacheKey.TENANT_ACCESS_TOKEN.value)
        # 优先读取缓存
        if _tenant_access_token and force_reload:
            return _tenant_access_token
        # 请求飞书查询
        # noinspection PyBroadException
        try:
            url = 'https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal/'
            data = {
                "app_id": self.app_id,
                "app_secret": self.app_secret
            }
            headers = {"content-type": "application/json;charset=UTF-8"}
            result = requests.post(url, json=data, headers=headers).json()
            # 判断是否正常返回
            if result['code'] != 0 or not result.get('tenant_access_token'):
                logger.warning(f"failed to get tenant_access_token, result is {result}")
                raise RemoteServerException(result)
            _tenant_access_token: str = result["tenant_access_token"]
            # 预留20分钟的时间缓冲
            _token_timeout: Optional[int] = self.token_timeout
            # 未设置超时时间则取飞书返回的token超时时间
            if not _token_timeout:
                try:
                    _token_timeout = int(result['expire']) - 20 * 60
                except (KeyError, TypeError, ValueError):
                    _token_timeout = 3600
            self.__set_cache(ICacheKey.TENANT_ACCESS_TOKEN.value, _tenant_access_token, _token_timeout)
            return _tenant_access_token
        except Exception as e:
            logger.warning(f"failed to get tenant_access_token", exc_info=True)
            raise e

    def get_multi_user_openid(self, emails: List[str], force_reload: bool = False) -> Dict[str, str]:
        """
        最多一次支持获取50条
        根据域账号获取用户email 手机号列表
        {
            email -> open_id,
        }
        :param emails: 邮箱列表
        :param force_reload: 强制更新
        :return: 返回邮箱与open_id的映射表
        """
        # 判断类型
        self.__check_param_type(list, emails=emails)
        result: Dict[str, str] = dict()
        # 空数据直接返回
        if not emails:
            return result
        # 一次性获取数据大于50条
        if len(emails) > LarkClient.MAX_COUNT_PER_QUERY:
            raise KeyParamsValueOutOfRangeException('emails', emails, LarkClient.MAX_COUNT_PER_QUERY)
        # 定义需要查询飞书的邮箱
        _pre_search_emails: Set[str] = set()
        _pre_search_emails.update(emails)
        # 读取缓存数据
        _email_open_id_mapping: Optional[Dict[str, str]] = self.__get_cache(ICacheKey.EMAIL_OPEN_ID_MAPPING.value)
        if _email_open_id_mapping is None:
            _email_open_id_mapping = dict()
        # 优先读取缓存
        if _email_open_id_mapping and not force_reload:
            for _e in emails:
                if _email_open_id_mapping.get(_e):
                    result[_e] = _email_open_id_mapping[_e]
                    _pre_search_emails.remove(_e)
            # 全部命中缓存
            if not _pre_search_emails:
                return result
        # 用户信息字典
        params = {
            'emails': emails
        }
        headers = {
            'content-type': 'application/json;charset=UTF-8',
            'Authorization': f"Bearer {self.get_tenant_access_token()}"
        }
        try:
            res = requests.get(
                "https://open.feishu.cn/open-apis/user/v1/batch_get_id",
                params=params,
                headers=headers
            )
            json_data = res.json()
            if json_data['code'] != 0:
                raise RemoteServerException(json_data)
            email_users = json_data['data']['email_users']
            for email in email_users:
                result[email] = email_users[email][0]['open_id']
                # 更新缓存
                _email_open_id_mapping[email] = result[email]
            # 保存缓存到数据库
            self.__set_cache(ICacheKey.EMAIL_OPEN_ID_MAPPING.value, _email_open_id_mapping, self.cache_timeout)
            return result
        except Exception as e:
            logger.warning(f"failed to get open_id by emails", exc_info=True)
            raise e

    def get_user_open_id(self, email: str, force_reload: bool = False) -> Optional[str]:
        """
        获取单个人的open_id
        :param email: 邮箱
        :param force_reload: 是否强制刷新
        :return:
        """
        # 判断类型
        self.__check_param_type(str, email=email)
        # 空数据直接返回
        self.__check_param_empty(email=email)

        infos: Dict[str, str] = self.get_multi_user_openid([email], force_reload)
        return infos.get(email)

    def upload_image(self, fp: str) -> str:
        """上传图片
        Args:
            fp: 文件上传路径
        Return resource key
        Raise:
            Exception
                * file not found
                * request error
        """
        # 判断类型
        self.__check_param_type(str, fp=fp)
        # 空数据直接返回
        self.__check_param_empty(fp=fp)
        # 判断文件是否存在
        if not os.path.exists(fp):
            raise KeyParamsValueInvalidException('fp', fp)
        try:
            # 读取待上传文件
            with open(fp, 'rb') as f:
                image = f.read()
            # 请求接口上传
            res = requests.post(
                url='https://open.feishu.cn/open-apis/image/v4/put/',
                headers={'Authorization': "Bearer %s" % self.get_tenant_access_token()},
                files={
                    "image": image
                },
                data={
                    "image_type": "message"
                },
                stream=True
            )
            json_data = res.json()
            # 校验是否成功
            if json_data["code"] != 0:
                raise RemoteServerException(json_data)
            return json_data['data']['image_key']
        except Exception as e:
            logger.warning(f"failed to upload image", exc_info=True)
            raise e

    def send_msg(
            self, receive_id_type: IReceiveIDType, receive_id: str, msg_type: IMessageType, content: Any
    ) -> ILarkMsgResult:
        """
        发送消息
        :param receive_id_type: 消息接收者id类型 open_id/user_id/union_id/email/chat_id
        :param receive_id: 依据receive_id_type的值，填写对应的消息接收者id
        :param msg_type: 消息类型 包括：text、post、image、file、audio、media、sticker、
                        interactive、share_chat、share_user等
        :param content: 消息内容，json结构序列化后的字符串。不同msg_type对应不同内容。消息类型
                        包括：text、post、image、file、audio、media、sticker、interactive、share_chat、share_user等
        :return:
        """
        # 判断类型
        self.__check_param_type(str, receive_id=receive_id)
        self.__check_param_type(IReceiveIDType, receive_id_type=receive_id_type)
        self.__check_param_type(IMessageType, msg_type=msg_type)
        # 空数据直接返回
        self.__check_param_empty(
            receive_id_type=receive_id_type, receive_id=receive_id, msg_type=msg_type, content=content
        )

        # 用户信息字典
        body = {
            'receive_id': receive_id,
            "msg_type": msg_type.value,
            "content": json.dumps(content),
        }
        headers = {
            'content-type': 'application/json;charset=utf-8',
            'Authorization': f"Bearer {self.get_tenant_access_token()}"
        }

        try:
            _res = requests.post(
                f"https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type={receive_id_type.value}",
                json=body,
                headers=headers
            )
            json_data = _res.json()
            _result: ILarkMsgResult = ILarkMsgResult()
            _result.code = json_data['code']
            _result.success = True if json_data['code'] == 0 else False
            _result.msg = json_data['msg']
            if 'data' in json_data:
                _result.data = from_dict(
                    ILarkMsgData, json_data['data'],
                    config=Config(type_hooks={IMessageType: IMessageType})
                )
            return _result
        except Exception as e:
            logger.warning(f"failed to send lark msg", exc_info=True)
            raise e

    def reply_msg(
            self, message_id: str, msg_type: IMessageType, content: Any
    ) -> ILarkMsgResult:
        """
        回复消息
        :param message_id: 待回复的消息的ID
        :param msg_type: 消息类型 包括：text、post、image、file、audio、media、sticker、
                        interactive、share_chat、share_user等
        :param content: 消息内容，json结构序列化后的字符串。不同msg_type对应不同内容。消息类型
                        包括：text、post、image、file、audio、media、sticker、interactive、share_chat、share_user等
        :return:
        """
        # 判断类型
        self.__check_param_type(str, message_id=message_id)
        self.__check_param_type(IMessageType, msg_type=msg_type)
        # 空数据直接返回
        self.__check_param_empty(message_id=message_id, msg_type=msg_type, content=content)

        # 用户信息字典
        body = {
            "msg_type": msg_type.value,
            "content": json.dumps(content),
        }
        headers = {
            'content-type': 'application/json;charset=utf-8',
            'Authorization': f"Bearer {self.get_tenant_access_token()}"
        }

        try:
            _res = requests.post(
                f"https://open.feishu.cn/open-apis/im/v1/messages/{message_id}/reply",
                json=body,
                headers=headers
            )
            json_data = _res.json()
            _result: ILarkMsgResult = ILarkMsgResult()
            _result.code = json_data['code']
            _result.success = True if json_data['code'] == 0 else False
            _result.msg = json_data['msg']
            if 'data' in json_data:
                _result.data = from_dict(
                    ILarkMsgData, json_data['data'],
                    config=Config(type_hooks={IMessageType: IMessageType})
                )
            return _result
        except Exception as e:
            logger.warning(f"failed to reply lark msg to {message_id}", exc_info=True)
            raise e

    def revoke_msg(self, message_id: str) -> ILarkMsgResult:
        """
        撤回消息
        :param message_id: 待撤回的消息的ID
        :return:
        """
        # 判断类型
        self.__check_param_type(str, message_id=message_id)
        # 空数据直接返回
        self.__check_param_empty(message_id=message_id)

        # 用户信息字典
        body = {

        }
        headers = {
            'content-type': 'application/json;charset=utf-8',
            'Authorization': f"Bearer {self.get_tenant_access_token()}"
        }

        try:
            _res = requests.delete(
                f"https://open.feishu.cn/open-apis/im/v1/messages/{message_id}",
                json=body,
                headers=headers
            )
            json_data = _res.json()
            _result: ILarkMsgResult = ILarkMsgResult()
            _result.code = json_data['code']
            _result.success = True if json_data['code'] == 0 else False
            _result.msg = json_data['msg']
            if 'data' in json_data:
                _result.data = from_dict(
                    ILarkMsgData, json_data['data'],
                    config=Config(type_hooks={IMessageType: IMessageType})
                )
            return _result
        except Exception as e:
            logger.warning(f"failed to revoke lark msg to {message_id}", exc_info=True)
            raise e

    def send_text_msg(self, receive_id_type: IReceiveIDType, receive_id: str, content: str) -> ILarkMsgResult:
        """
        发送普通消息
        :param receive_id_type: 消息接收者id类型 open_id/user_id/union_id/email/chat_id
        :param receive_id: 依据receive_id_type的值，填写对应的消息接收者id
        :param content: 消息内容，json结构序列化后的字符串。不同msg_type对应不同内容。消息类型
                        包括：text、post、image、file、audio、media、sticker、interactive、share_chat、share_user等
        :return:
        """
        return self.send_msg(receive_id_type, receive_id, IMessageType.TEXT, {"text": content})

    def send_interactive_msg(
            self, receive_id_type: IReceiveIDType, receive_id: str, content: Dict[str, Any]
    ) -> ILarkMsgResult:
        """
        发送卡片消息
        :param receive_id_type: 消息接收者id类型 open_id/user_id/union_id/email/chat_id
        :param receive_id: 依据receive_id_type的值，填写对应的消息接收者id
        :param content: 消息内容，json结构序列化后的字符串。不同msg_type对应不同内容。消息类型
                        包括：text、post、image、file、audio、media、sticker、interactive、share_chat、share_user等
        :return:
        """
        return self.send_msg(receive_id_type, receive_id, IMessageType.INTERACTIVE, content)

    def reply_text_msg(self, message_id: str, content: str) -> ILarkMsgResult:
        """
        回复普通消息
        :param message_id: 待回复消息id
        :param content: 消息内容，json结构序列化后的字符串。不同msg_type对应不同内容。消息类型
                        包括：text、post、image、file、audio、media、sticker、interactive、share_chat、share_user等
        :return:
        """
        return self.reply_msg(message_id, IMessageType.TEXT, {"text": content})

    def reply_interactive_msg(self, message_id: str, content: Dict[str, Any]) -> ILarkMsgResult:
        """
        回复卡片消息
        :param message_id: 待回复消息id
        :param content: 消息内容，json结构序列化后的字符串。不同msg_type对应不同内容。消息类型
                        包括：text、post、image、file、audio、media、sticker、interactive、share_chat、share_user等
        :return:
        """
        return self.reply_msg(message_id, IMessageType.INTERACTIVE, content)
