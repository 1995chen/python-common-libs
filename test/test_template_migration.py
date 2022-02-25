# -*- coding: UTF-8 -*-


import os
import unittest
import shutil
from typing import Optional

import inject
import template_logging
from template_migration import Migration
from sqlalchemy.orm import scoped_session, Session, sessionmaker
from sqlalchemy import create_engine

# 创建日志目录
os.makedirs('./logs/', exist_ok=True)
template_logging.init_logger()
logger = template_logging.getLogger(__name__)


class MainDBSession(scoped_session, Session):
    pass


class TestTemplateMigrationMethods(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """
            进行该测试用例整体的初始化
        """
        cls.db_path: str = 'db'
        cls.migration_script_path: str = 'migrations'
        cls.db_url = f"sqlite:///{cls.db_path}/unittest.db"
        # 清空数据库文件以及migration脚本目录
        shutil.rmtree(cls.db_path, ignore_errors=True)
        shutil.rmtree(cls.migration_script_path, ignore_errors=True)
        os.makedirs(cls.db_path, exist_ok=True)
        os.makedirs(cls.migration_script_path, exist_ok=True)

        def init_main_db_session():
            engine = create_engine(cls.db_url, pool_recycle=3600)
            return scoped_session(sessionmaker(engine))

        def init_migrate() -> Migration:
            def init_data_handler(*args, **kwargs) -> None:
                """
                初始化数据handler
                """
                session = inject.instance(MainDBSession)
                # 创建一张表
                session.execute("""
                    CREATE TABLE `test_do_init_migrate` (
                      `id` INTEGER PRIMARY KEY AUTOINCREMENT,
                      `value` TEXT
                    );
                """)
                # 初始化数据
                session.execute(f"""
                    INSERT INTO `test_do_init_migrate` (`value`) VALUES ('do init');
                """)
                session.commit()
                logger.info("do init_data_handler done")

            # 初始化
            migration_instance: Migration = Migration(
                database_uri=cls.db_url,
                project='unittest',
                workspace='./'
            )
            # 设置handler
            migration_instance.set_do_init_data_handler(init_data_handler)
            return migration_instance

        def my_config(binder):
            binder.bind_to_constructor(Migration, init_migrate)
            binder.bind_to_constructor(MainDBSession, init_main_db_session)

        # 将实例绑定到inject
        inject.configure(my_config)

    @classmethod
    def tearDownClass(cls):
        # 清理
        inject.clear()
        db_path = object.__getattribute__(cls, 'db_path')
        migration_script_path = object.__getattribute__(cls, 'migration_script_path')
        # 清空数据库文件以及migration脚本目录
        shutil.rmtree(db_path, ignore_errors=True)
        shutil.rmtree(migration_script_path, ignore_errors=True)

    def setUp(self):
        # 获得migrate
        self.migration_instance: Optional[Migration] = inject.instance(Migration)
        # 获得session
        self.main_session: Optional[MainDBSession] = inject.instance(MainDBSession)

        self.passed: bool = False

    def tearDown(self):
        # 打印结果
        logger.info(
            f"func {self.__class__.__name__}.{self._testMethodName}.........{'passed' if self.passed else 'failed'}"
        )

    def test_do_init_migrate(self):
        """
        测试初始化
        """
        self.migration_instance.do_migrate()
        # 查询数据是否初始化
        init_result = self.main_session.execute(f"select * from test_do_init_migrate")
        init_result = [_r for _r in init_result]
        self.assertEqual(len(init_result), 1)
        self.assertEqual(init_result[0][0], 1)
        self.assertEqual(init_result[0][1], 'do init')

        # 再次初始化
        self.migration_instance.do_migrate()
        # 查询数据是否初始化
        init_result = self.main_session.execute(f"select * from test_do_init_migrate")
        init_result = [_r for _r in init_result]
        self.assertEqual(len(init_result), 1)
        self.assertEqual(init_result[0][0], 1)
        self.assertEqual(init_result[0][1], 'do init')

        self.passed = True

    def test_do_migrate(self):
        """
        测试后序migrate
        """
        # 查看是否初始化过
        if not self.migration_instance.is_inited():
            # 执行初始化
            self.migration_instance.do_migrate()

        # 先写入一个migrate文件到对应目录中
        migration_script = """
# -*- coding: UTF-8 -*-


import os
import importlib
from typing import Any

import inject
import template_logging

test_template_migration: Any = importlib.import_module('test_template_migration')

logger = template_logging.getLogger(__name__)


def do_insert():
    try:
        session = inject.instance(test_template_migration.MainDBSession)

        # 创建一张表
        session.execute(
            "CREATE TABLE `test_do_migrate` "
            "(`id` INTEGER PRIMARY KEY AUTOINCREMENT, `value` TEXT"
            ");"
        )
        # 初始化数据
        session.execute(f"INSERT INTO `test_do_migrate` (`value`) VALUES ('test_do_migrate');")
        session.commit()
        logger.info("do_insert success")
    except Exception as e:
        logger.error(f"Failed do_insert", exc_info=True)
        raise e


def do():
    logger.info(f"do migration by {os.path.basename(__file__)}")
    do_insert()
        """
        # 写文件
        with open(f"./migrations/migration_prod_1.py", 'w') as f:
            f.write(migration_script)
        self.migration_instance.do_migrate()
        # 校验数据
        result = self.main_session.execute(f"select * from test_do_migrate")
        result = [_r for _r in result]
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][0], 1)
        self.assertEqual(result[0][1], 'test_do_migrate')

        # 再次执行migrate
        self.migration_instance.do_migrate()
        # 查看migration脚本是否重复执行
        result = self.main_session.execute(f"select * from test_do_migrate")
        result = [_r for _r in result]
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][0], 1)
        self.assertEqual(result[0][1], 'test_do_migrate')

        self.passed = True


if __name__ == '__main__':
    unittest.main()
