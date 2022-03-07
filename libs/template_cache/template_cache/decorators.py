# -*- coding: UTF-8 -*-


import functools
import hashlib
import pickle
import logging
import threading
from typing import Optional, Callable, Any

from template_exception import (
    HandlerUnCallableException, KeyParamsTypeInvalidException
)

logger = logging.getLogger(__name__)


class Cache:
    def __init__(self):
        """
        初始化方法
        """
        # 设定缓存的handler
        self.store_cache_handler: Optional[Callable] = None
        # 计算缓存key
        self.generate_cache_key_handler: Optional[Callable] = None
        # 获取缓存handler
        self.get_cache_handler: Optional[Callable] = None
        # 存储token, 解耦flask
        self.registry = threading.local()

    def set_force_reload(self, value: bool) -> None:
        """
        设置token, 此操作在before request中做
        强制刷新缓存仅对当前线程生效
        用于判断用户是否登录,并且应用用户的自定义校验方法
        """
        # 必须是一个bool类型
        if not isinstance(value, bool):
            raise KeyParamsTypeInvalidException('value', bool)
        self.registry.force_reload = value

    def get_force_reload(self) -> bool:
        """
        获得存储的thread local对象
        """
        return getattr(self.registry, 'force_reload', False)

    def set_store_cache_handler(self, handler: Callable) -> None:
        if not callable(handler):
            raise HandlerUnCallableException(f"{type(self).__name__}.set_store_cache_handler")
        self.store_cache_handler = handler

    def set_generate_cache_key_handler(self, handler: Callable) -> None:
        if not callable(handler):
            raise HandlerUnCallableException(f"{type(self).__name__}.set_generate_cache_key_handler")
        self.generate_cache_key_handler = handler

    def set_get_cache_handler(self, handler: Callable) -> None:
        if not callable(handler):
            raise HandlerUnCallableException(f"{type(self).__name__}.set_get_cache_handler")
        self.get_cache_handler = handler

    def __generate_cache_key(self, func: Callable, *args: Any, **kwargs: Any) -> str:
        """
        根据参数生成缓存key
        :param func: 方法体
        :param args: 参数
        :param kwargs: 字典参数
        :return: 字符串
        """
        # 调用回调方法
        if callable(self.generate_cache_key_handler):
            return self.generate_cache_key_handler(func, *args, **kwargs)
        logger.warning('UnImplement handler generate_cache_key_handler, use default')
        # 使用默认的key生成方法
        cache_key = pickle.dumps((args, kwargs))
        # key 过长优化
        cache_key = func.__module__ + '.' + func.__name__ + '.' + hashlib.md5(cache_key).hexdigest()
        return cache_key

    def store_cache(self, key: str, value: Any, timeout: Optional[int] = None, **user_kwargs) -> Any:
        """
        存储缓存
        :param key: 待存储缓存
        :param value: 待存储缓存
        :param timeout: 超时时间
        :param user_kwargs: 用户自定义参数[该参数回传递给handler]
        :return: 该返回结果根据存储数据中间件决定
        """
        if not callable(self.store_cache_handler):
            logger.error('NotImplementedError store_cache_handler')
            raise NotImplementedError('store_cache_handler')
        return self.store_cache_handler(key, value, timeout, **user_kwargs)

    def get_cache(self, key: str, timeout: Optional[int] = None, **user_kwargs) -> Any:
        """
        获得缓存
        :param key: 缓存key
        :param timeout: 超时时间[可用于重置缓存时间]
        :param user_kwargs: 用户自定义参数
        :return:
        """
        if not callable(self.get_cache_handler):
            logger.error('NotImplementedError get_cache_handler')
            raise NotImplementedError('get_cache_handler')
        return self.get_cache_handler(key, timeout, **user_kwargs)

    def use_cache(self, timeout: Optional[int] = 60, **user_kwargs) -> Callable:
        """
        缓存装饰器
        该装饰器对方法调用进行缓存
        :param timeout: 超时时间
        :param user_kwargs: 用户自定义参数
        :return:
        """

        def wrapper_outer(func):

            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                # 生成缓存key
                _cache_key: str = self.__generate_cache_key(func, *args, **kwargs)
                # 查询缓存
                _cache_value: Optional[Any] = self.get_cache(_cache_key, timeout, **user_kwargs)
                if _cache_value and not self.get_force_reload():
                    return pickle.loads(_cache_value)
                # 调用方法
                func_value: Any = func(*args, **kwargs)
                # 缓存
                if func_value:
                    self.store_cache(_cache_key, pickle.dumps(func_value), timeout, **user_kwargs)
                return func_value

            return wrapper

        return wrapper_outer
