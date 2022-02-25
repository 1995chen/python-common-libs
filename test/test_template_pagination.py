# -*- coding: UTF-8 -*-


import os
import unittest
import shutil
from typing import Optional, List, Any

import inject
import template_logging
from sqlalchemy.orm import scoped_session, Session, sessionmaker, Query
from sqlalchemy import Column, Integer, create_engine
from sqlalchemy.ext.declarative import declarative_base
from template_pagination import (
    IPagePaginationParam, IPaginationRes, ISortParam,
    ISortType, Pagination, IOffsetPaginationParam
)

# 创建日志目录
os.makedirs('./logs/', exist_ok=True)
template_logging.init_logger()
logger = template_logging.getLogger(__name__)

# 定义Base
Base = declarative_base()


class TestDoPagination(Base):
    """
    数据库migrate需要的Model
    """
    __tablename__ = 'test_do_pagination'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键')
    value = Column(Integer)


class MainDBSession(scoped_session, Session):
    pass


class TestTemplatePaginationMethods(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """
            进行该测试用例整体的初始化
        """

        cls.db_path: str = 'db'
        cls.db_url = f"sqlite:///{cls.db_path}/unittest.db"
        cls.engine = create_engine(cls.db_url, pool_recycle=3600)

        # 清空数据库文件以及migration脚本目录
        shutil.rmtree(cls.db_path, ignore_errors=True)
        os.makedirs(cls.db_path, exist_ok=True)

        def init_main_db_session():
            return scoped_session(sessionmaker(cls.engine))

        def init_pagination() -> Pagination:

            def do_after_paginate_handler(pagination_res: IPaginationRes) -> IPaginationRes:
                """
                分页后操作, 可以进行一些分页后处理
                一些兼容的事情在这里做
                """
                return pagination_res

            def get_page_paginate_params_handler() -> IPagePaginationParam:
                """
                这是一个简单的实现
                传递分页参数
                可以不实现该handler,
                直接在flask before_request中手动调用set_page_pagination_params/set_offset_pagination_params
                也是一条支持的路径,手动调用set的优先级更高
                """
                page: int = 2
                limit: int = 3
                order_by: Optional[List[ISortParam]] = None

                # 这里假设以id:desc,value:asc
                sort_str: str = "value:asc,id:desc"
                sort_arr: Optional[List[str]] = sort_str.split(',') if sort_str else None

                # 构造参数
                pagination_param: IPagePaginationParam = IPagePaginationParam(limit, order_by, page)
                if not sort_arr:
                    return pagination_param
                order_by = list()
                # 获取排序
                for express in sort_arr:
                    _label, _func_str = express.split(':')
                    _func_type: ISortType = ISortType.DESC if str(_func_str).lower() == 'desc' else ISortType.ASC
                    _sort_param: ISortParam = ISortParam(_label, _func_type)
                    order_by.append(_sort_param)
                pagination_param.order_by = order_by
                return pagination_param

            pagination: Pagination = Pagination()
            pagination.set_get_page_paginate_params_handler(get_page_paginate_params_handler)
            pagination.set_do_after_paginate_handler(do_after_paginate_handler)
            return pagination

        def my_config(binder):
            binder.bind_to_constructor(Pagination, init_pagination)
            binder.bind_to_constructor(MainDBSession, init_main_db_session)

        # 将实例绑定到inject
        inject.configure(my_config)

        session = inject.instance(MainDBSession)
        # 创建测试表
        Base.metadata.create_all(bind=cls.engine)

        # 初始化测试数据
        session.add(TestDoPagination(id=1, value=5))
        session.add(TestDoPagination(id=2, value=4))
        session.add(TestDoPagination(id=3, value=2))
        session.add(TestDoPagination(id=4, value=6))
        session.add(TestDoPagination(id=5, value=9))
        session.add(TestDoPagination(id=6, value=6))
        session.add(TestDoPagination(id=7, value=4))
        session.add(TestDoPagination(id=8, value=2))
        session.add(TestDoPagination(id=9, value=4))
        session.commit()
        logger.info("do init test data done")

    @classmethod
    def tearDownClass(cls):
        cls.engine = None
        # 清理
        inject.clear()
        db_path = object.__getattribute__(cls, 'db_path')
        # 清空数据库文件以及migration脚本目录
        shutil.rmtree(db_path, ignore_errors=True)

    def setUp(self):
        # 获得pagination
        self.pagination: Optional[Pagination] = inject.instance(Pagination)
        # 获得session
        self.main_session: Optional[MainDBSession] = inject.instance(MainDBSession)

        self.passed: bool = False

    def tearDown(self):
        # 打印结果
        logger.info(
            f"func {self.__class__.__name__}.{self._testMethodName}.........{'passed' if self.passed else 'failed'}"
        )

    def valid_pagination_result(self, paginate_res: IPaginationRes):
        # 验证查询条目
        self.assertEqual(paginate_res.count, 9)
        self.assertEqual(len(paginate_res.records), 3)
        # 验证分页条件
        self.assertEqual(paginate_res.param.page, 2)
        self.assertEqual(paginate_res.param.offset, 3)
        self.assertEqual(paginate_res.param.limit, 3)
        self.assertEqual(len(paginate_res.param.order_by), 2)
        self.assertEqual(paginate_res.param.order_by[0].label, 'value')
        self.assertEqual(paginate_res.param.order_by[0].type, ISortType.ASC)
        self.assertEqual(paginate_res.param.order_by[1].label, 'id')
        self.assertEqual(paginate_res.param.order_by[1].type, ISortType.DESC)
        # 验证查询的结果
        self.assertEqual(paginate_res.records[0].id, 7)
        self.assertEqual(paginate_res.records[0].value, 4)
        self.assertEqual(paginate_res.records[1].id, 2)
        self.assertEqual(paginate_res.records[1].value, 4)
        self.assertEqual(paginate_res.records[2].id, 1)
        self.assertEqual(paginate_res.records[2].value, 5)

    def test_pagination_decorator(self):
        """
        测试分页注解
        """

        @self.pagination.with_paginate()
        def test_query() -> Any:
            session = inject.instance(MainDBSession)
            query: Query = session.query(TestDoPagination)
            return query

        # 查询结果
        paginate_res: IPaginationRes = test_query()
        # 验证
        self.valid_pagination_result(paginate_res)

        self.passed = True

    def test_page_pagination_params(self):
        """
        测试直接调用分页
        """

        @self.pagination.with_paginate()
        def test_query() -> Any:
            session = inject.instance(MainDBSession)
            query: Query = session.query(TestDoPagination)
            return query

        # 手动设置分页参数
        self.pagination.set_page_pagination_params(IPagePaginationParam(
            page=2, limit=3, order_by=[
                ISortParam('value', ISortType.ASC),
                ISortParam('id', ISortType.DESC),
            ]
        ))
        paginate_res: IPaginationRes = test_query()
        # 验证
        self.valid_pagination_result(paginate_res)

        self.passed = True

    def test_offset_pagination_params(self):
        """
        测试直接调用分页
        """

        @self.pagination.with_paginate()
        def test_query() -> Any:
            session = inject.instance(MainDBSession)
            query: Query = session.query(TestDoPagination)
            return query

        # 手动设置分页参数
        self.pagination.set_offset_pagination_params(IOffsetPaginationParam(
            offset=3, limit=3, order_by=[
                ISortParam('value', ISortType.ASC),
                ISortParam('id', ISortType.DESC),
            ]
        ))
        paginate_res: IPaginationRes = test_query()
        # 验证
        self.valid_pagination_result(paginate_res)

        self.passed = True


if __name__ == '__main__':
    unittest.main()
