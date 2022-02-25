# -*- coding: UTF-8 -*-


import os
import unittest
import shutil
from typing import Optional, Any

import inject
import template_logging
from sqlalchemy.orm import scoped_session, Session, sessionmaker
from sqlalchemy import Column, Integer, create_engine
from sqlalchemy.ext.declarative import declarative_base
from template_transaction import CommitContext, autocommit

# 创建日志目录
os.makedirs('./logs/', exist_ok=True)
template_logging.init_logger()
logger = template_logging.getLogger(__name__)

# 定义Base
Base = declarative_base()


class TestTransaction(Base):
    """
    数据库migrate需要的Model
    """
    __tablename__ = 'test_transaction'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键')
    value = Column(Integer)


class MainDBSession(scoped_session, Session):
    pass


# 定义一个异常
class MyException(Exception):
    pass


class TestTemplateTransactionMethods(unittest.TestCase):

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

        def my_config(binder):
            binder.bind_to_constructor(MainDBSession, init_main_db_session)

        # 将实例绑定到inject
        inject.configure(my_config)

        # 创建测试表
        Base.metadata.create_all(bind=cls.engine)

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
        # 获得session
        self.main_session: Optional[MainDBSession] = inject.instance(MainDBSession)

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

        @autocommit(MainDBSession)
        def test_query() -> Any:
            self.main_session.add(TestTransaction(id=2, value=4))
            self.main_session.add(TestTransaction(id=3, value=2))
            raise MyException()

        # 创建一条测试数据
        self.main_session.add(TestTransaction(id=1, value=5))
        # 验证数据成功创建
        result: TestTransaction = self.main_session.query(TestTransaction).filter(TestTransaction.id == 1).first()
        self.assertEqual(result.id, 1)
        self.assertEqual(result.value, 5)

        # 断言预期的异常
        with self.assertRaises(MyException):
            test_query()
        # 查询数据是否回滚
        result: TestTransaction = self.main_session.query(TestTransaction).filter(TestTransaction.id == 2).first()
        self.assertIsNone(result)
        result: TestTransaction = self.main_session.query(TestTransaction).filter(TestTransaction.id == 3).first()
        self.assertIsNone(result)

        self.passed = True

    def test_transaction_context(self):
        """
        测试事务上下文
        """

        def test_query() -> Any:
            with CommitContext(self.main_session):
                self.main_session.add(TestTransaction(id=5, value=9))
                self.main_session.add(TestTransaction(id=6, value=6))
                raise MyException()

        # 创建一条测试数据
        self.main_session.add(TestTransaction(id=4, value=6))
        # 验证数据成功创建
        result: TestTransaction = self.main_session.query(TestTransaction).filter(
            TestTransaction.id == 4).first()
        self.assertEqual(result.id, 4)
        self.assertEqual(result.value, 6)

        # 断言预期的异常
        with self.assertRaises(MyException):
            test_query()
        # 查询数据是否回滚
        result: TestTransaction = self.main_session.query(TestTransaction).filter(
            TestTransaction.id == 5).first()
        self.assertIsNone(result)
        result: TestTransaction = self.main_session.query(TestTransaction).filter(
            TestTransaction.id == 6).first()
        self.assertIsNone(result)

        self.passed = True


if __name__ == '__main__':
    unittest.main()
