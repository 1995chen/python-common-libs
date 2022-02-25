# -*- coding: UTF-8 -*-


import functools
import threading
import logging
from enum import Enum
from typing import Optional, Callable, List, Any
from dataclasses import dataclass

from sqlalchemy.orm import Query
from sqlalchemy import desc, asc
from template_exception import (
    HandlerUnCallableException, InvalidQueryObjectException, KeyParamsTypeInvalidException,
    KeyParamsValueInvalidException
)

logger = logging.getLogger(__name__)

# 默认返回第一页
DEFAULT_PAGE: int = 1
# 默认页大小
DEFAULT_LIMIT: int = 20
# 默认偏移量
DEFAULT_OFFSET: int = 0


class ISortType(Enum):
    """
    排序类型
    """
    DESC: 'ISortType' = "desc"
    ASC: 'ISortType' = "asc"


@dataclass
class ISortParam:
    """
    排序参数
    """
    label: str
    type: ISortType

    def __post_init__(self):
        # 判断类型
        if not isinstance(self.label, str):
            raise KeyParamsTypeInvalidException('label', str)
        if not self.label:
            raise KeyParamsValueInvalidException('label', self.label)
        if not isinstance(self.type, ISortType):
            raise KeyParamsTypeInvalidException('type', ISortType)


@dataclass
class IBasePaginationParam:
    """
    [分页参数] 基类
    """
    limit: int = DEFAULT_LIMIT
    order_by: Optional[List[ISortParam]] = None

    def __post_init__(self):
        """
        基础的参数校验
        :return:
        """
        # 判断类型
        if not isinstance(self.limit, int):
            raise KeyParamsTypeInvalidException('limit', int)
        # 判断值
        if self.limit < 0:
            raise KeyParamsValueInvalidException('limit', self.limit)
        if self.order_by:
            if not isinstance(self.order_by, list):
                raise KeyParamsTypeInvalidException('order_by', list)


@dataclass
class IPagePaginationParam(IBasePaginationParam):
    """
    [分页参数] 按页号
    该类由外部handler使用
    """
    page: int = DEFAULT_PAGE

    def __post_init__(self):
        """
        基础的参数校验
        :return:
        """
        # 判断类型
        if not isinstance(self.page, int):
            raise KeyParamsTypeInvalidException('page', int)
        # 判断值
        if self.page < 0:
            raise KeyParamsValueInvalidException('page', self.page)


@dataclass
class IOffsetPaginationParam(IBasePaginationParam):
    """
    [分页参数] 按offset偏移量
    该类由外部handler使用
    """
    offset: int = DEFAULT_OFFSET

    def __post_init__(self):
        """
        基础的参数校验
        :return:
        """
        # 判断类型
        if not isinstance(self.offset, int):
            raise KeyParamsTypeInvalidException('offset', int)
        # 判断值
        if self.offset < 0:
            raise KeyParamsValueInvalidException('offset', self.offset)


@dataclass
class IPaginationParam(IBasePaginationParam):
    """
    插件内使用的dataclass
    """
    page: int = DEFAULT_PAGE
    offset: int = DEFAULT_OFFSET


@dataclass
class IPaginationRes:
    """
    插件内返回分页标准结果
    """
    param: IPaginationParam
    count: int
    records: List[Any]


class Pagination:
    def __init__(self):
        """
        初始化方法
        """
        # 存储token, 解耦flask
        self.registry = threading.local()

        # 格式化分页数据handler
        self.do_after_paginate_handler: Optional[Callable] = None

        # 实现以下handler中的任意一个即可
        # 通过页号获得分页参数的handler
        self.get_page_paginate_params_handler: Optional[Callable] = None
        # 通过偏移量获得分页参数的handler
        self.get_offset_paginate_params_handler: Optional[Callable] = None

    def set_get_page_paginate_params_handler(self, handler: Callable) -> None:
        """
        设置handler
        该handler用于处理用户分页参数并按约定提供分页数据
        主要处理以page方式的分页
        :param handler:
        :return:
        """
        if not callable(handler):
            raise HandlerUnCallableException(f"{type(self).__name__}.set_get_page_paginate_params_handler")
        self.get_page_paginate_params_handler = handler

    def set_get_offset_paginate_params_handler(self, handler: Callable) -> None:
        """
        设置handler
        该handler用于处理用户分页参数并按约定提供分页数据
        主要处理以offset方式的分页
        :param handler:
        :return:
        """
        if not callable(handler):
            raise HandlerUnCallableException(f"{type(self).__name__}.set_get_offset_paginate_params_handler")
        self.get_offset_paginate_params_handler = handler

    def set_do_after_paginate_handler(self, handler: Callable) -> None:
        """
        设置handler
        该handler用于对分页后的数据进行二次加工
        :param handler:
        :return:
        """
        if not callable(handler):
            raise HandlerUnCallableException(f"{type(self).__name__}.set_do_after_paginate_handler")
        self.do_after_paginate_handler = handler

    def __do_after_paginate_handler(self, pagination_res: IPaginationRes, **user_kwargs) -> Any:
        """
        服务内执行该方法调用handler处理分页后数据
        :param pagination_res:
        :param user_kwargs: 用户自定义参数
        :return:
        """
        if not callable(self.do_after_paginate_handler):
            logger.warning('handler do_after_paginate_handler Not Implemented, return origin pagination_res')
            return pagination_res
        return self.do_after_paginate_handler(pagination_res, **user_kwargs)

    def __get_pagination_params_by_handler(self, **user_kwargs) -> Optional[IPaginationParam]:
        """
        服务内执行该方法调用handler获取分页数据
        :param user_kwargs: 用户自定义参数
        :return:
        """
        pagination_param: Optional[IPaginationParam] = IPaginationParam()
        if callable(self.get_page_paginate_params_handler):
            page_pagination_param: IPagePaginationParam = self.get_page_paginate_params_handler(**user_kwargs)
            pagination_param.page = page_pagination_param.page
            pagination_param.limit = page_pagination_param.limit
            pagination_param.order_by = page_pagination_param.order_by
            pagination_param.offset = (pagination_param.page - 1) * pagination_param.limit
            return pagination_param
        if callable(self.get_offset_paginate_params_handler):
            offset_pagination_param: IOffsetPaginationParam = self.get_offset_paginate_params_handler(**user_kwargs)
            pagination_param.limit = offset_pagination_param.limit
            pagination_param.order_by = offset_pagination_param.order_by
            pagination_param.offset = offset_pagination_param.offset
            pagination_param.page = pagination_param.offset // pagination_param.limit + 1
            return pagination_param
        logger.warning('you may not implement pagination params handler')
        # 返回默认的参数
        return None

    def set_page_pagination_params(self, page_pagination_param: IPagePaginationParam) -> None:
        """
        手动传入分页参数
        在不实现分页参数handler的情况下，可以直接设置分页参数
        该方法的优先级最高
        :param page_pagination_param: 带页号的分页参数
        :return:
        """
        if not isinstance(page_pagination_param, IPagePaginationParam):
            raise KeyParamsTypeInvalidException('page_pagination_param', IPagePaginationParam)
        # 做参数转换
        pagination_param: Optional[IPaginationParam] = IPaginationParam()
        pagination_param.page = page_pagination_param.page
        pagination_param.limit = page_pagination_param.limit
        pagination_param.order_by = page_pagination_param.order_by
        pagination_param.offset = (pagination_param.page - 1) * pagination_param.limit
        self.registry.pagination_param = pagination_param

    def set_offset_pagination_params(self, offset_pagination_param: IOffsetPaginationParam) -> None:
        """
        手动传入分页参数
        在不实现分页参数handler的情况下，可以直接设置分页参数
        该方法的优先级最高
        :param offset_pagination_param: 带偏移量的分页参数
        :return:
        """
        if not isinstance(offset_pagination_param, IOffsetPaginationParam):
            raise KeyParamsTypeInvalidException('offset_pagination_param', IOffsetPaginationParam)
        # 做参数转换
        pagination_param: Optional[IPaginationParam] = IPaginationParam()
        pagination_param.limit = offset_pagination_param.limit
        pagination_param.order_by = offset_pagination_param.order_by
        pagination_param.offset = offset_pagination_param.offset
        pagination_param.page = pagination_param.offset // pagination_param.limit + 1
        self.registry.pagination_param = pagination_param

    def get_pagination_params(self, **user_kwargs) -> IPaginationParam:
        """
        获得分页参数
        插件内获得分页参数的唯一入口, 优先从thread local获取
        :param user_kwargs: 用户自定义参数
        :return:
        """
        # 优先从thread local中获取
        pagination_param: Optional[IPaginationParam] = getattr(self.registry, 'pagination_param', None)
        if pagination_param is not None:
            return pagination_param
        # 从handler中获取
        pagination_param = self.__get_pagination_params_by_handler(**user_kwargs)
        # 返回默认的分页数据
        return pagination_param or IPaginationParam()

    def paginate(
            self, query: Query, return_original: bool = False, order_by: Optional[List[ISortParam]] = None,
            **user_kwargs
    ) -> Any:
        """
        分页方法
        :param query: sqlalchemy query object
        :param return_original: 是否返回原始数据 if True will not call user define handler
        :param order_by: 排序参数[这里设置的排序优先级最高]
        :param user_kwargs: 用户自定义参数
        :return: IPaginationRes or Any user defined Types
        """
        if not isinstance(query, Query):
            raise InvalidQueryObjectException(query)
        # 获得总数
        count: int = query.count()
        # 获得分页参数
        pagination_param: Optional[IPaginationParam] = self.get_pagination_params(**user_kwargs)
        # 用户传入排序参数
        if order_by:
            pagination_param.order_by = order_by
        # 排序
        query_orders = list()
        if pagination_param.order_by:
            for _order in pagination_param.order_by:
                # 定义排序方法
                _sort_func: Callable = asc
                if _order.type == ISortType.DESC:
                    _sort_func = desc
                query_orders.append(_sort_func(_order.label))
            query = query.order_by(*query_orders)
        # 分页
        records: List[Any] = query.offset(pagination_param.offset).limit(pagination_param.limit).all()
        pagination_res: IPaginationRes = IPaginationRes(pagination_param, count, records)
        # 返回原始数据
        if return_original:
            return pagination_res
        return self.__do_after_paginate_handler(pagination_res, **user_kwargs)

    def clear(self) -> None:
        """
        请求结束后可以调用该方法进行清理
        :return:
        """
        if hasattr(self.registry, 'pagination_param'):
            del self.registry.pagination_param

    def with_paginate(
            self, return_original: bool = False, order_by: Optional[List[ISortParam]] = None,
            **user_kwargs
    ) -> Callable:
        """
        注解
        :param return_original: 是否返回原始数据 if True will not call user define handler
        :param order_by: 排序参数
        :param user_kwargs: 用户自定义参数
        :return: IPaginationRes or Any user defined Types
        """

        def wrapper_outer(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                # 获取原始方法返回
                query: Query = func(*args, **kwargs)
                # 分页
                paginate_res: Any = self.paginate(query, return_original, order_by, **user_kwargs)
                return paginate_res

            return wrapper

        return wrapper_outer
