# -*- coding: UTF-8 -*-


import os
import re
import logging
from typing import List, Optional, Callable

from sqlalchemy import func, create_engine
from sqlalchemy.orm import sessionmaker, scoped_session, Session
from template_transaction import CommitContext
from template_exception import HandlerUnCallableException

from .models import MigrationLog, Base

logger = logging.getLogger(__name__)


class MigrationSession(scoped_session, Session):
    pass


class Migration:
    """
    服务数据迁移脚本
    """

    def __init__(
            self, database_uri: str, project: str, workspace: str,
            isolation_level: Optional[str] = None
    ) -> None:
        """
        初始化方法
        database_uri: 数据库连接URL
        project: 项目名称
        workspace: migrate脚本工作空间[数据迁移脚本在 workspace/migrations/ 目录下]
        """
        # 创建engine
        self.engine = create_engine(database_uri, pool_recycle=3600, isolation_level=isolation_level)
        # 创建Session
        self.session: Session = MigrationSession(sessionmaker(self.engine))
        self.project = project
        # 脚本存放路径
        self.script_path = os.path.join(workspace, 'migrations')
        # 自动创建目录
        if not os.path.exists(self.script_path):
            os.mkdir(self.script_path)
        self.do_init_data_handler: Optional[Callable] = None

    def set_do_init_data_handler(self, handler: Callable) -> None:
        """
        设置初始化数据handler
        :param handler:
        :return:
        """
        if not callable(handler):
            raise HandlerUnCallableException(f"{type(self).__name__}.set_do_init_data_handler")
        self.do_init_data_handler = handler

    def _generate_table(self) -> None:
        """
        创建表
        :return:
        """
        Base.metadata.create_all(bind=self.engine)
        logger.info("generate_table success")

    def _drop_table(self) -> None:
        """
        删除表
        :return:
        """
        Base.metadata.drop_all(bind=self.engine)
        logger.info("drop_table success")

    def _init_data(self, *args, **kwargs) -> None:
        """
        初始化服务基础数据
        """
        # 执行用户自定义handler
        if callable(self.do_init_data_handler):
            logger.info(f"call user defined init handler")
            self.do_init_data_handler(*args, **kwargs)
        # 添加migrate记录
        _migrate = MigrationLog(version=0, script='sys_init', success=True, project=self.project)
        self.session.add(_migrate)
        self.session.commit()
        # 添加migrate记录
        self._add_migration_log()
        logger.info(f"init_data success!")

    def is_inited(self) -> bool:
        """
        返回服务是否初始化过
        """
        _migration_log: MigrationLog = self.session.query(MigrationLog).filter(
            MigrationLog.project == self.project).first()
        return True if _migration_log else False

    def _add_migration_log(self) -> None:
        """
        该方法仅会创建migrate记录, 并不会执行其中脚本
        """
        _session: Session = self.session
        _project: str = self.project
        with CommitContext(_session):
            # 每次重新创建数据库后需将当前所有迁移脚本设备已处理
            regexp = re.compile(r'migration_prod_(\d+).py$')
            max_version = _session.query(MigrationLog).filter_by(success=True, project=_project).with_entities(
                func.max(MigrationLog.version)).first()[0]
            max_version = max_version if max_version is not None else -1
            matches = {}
            migration_list: List[str] = os.listdir(self.script_path)
            for f in migration_list:
                match = regexp.match(f)
                if match is not None:
                    matches[f] = int(match.group(1))
            files = sorted([x for x in migration_list if matches.get(x) is not None], key=lambda x: matches[x])
            for f in files:
                version = matches[f]
                if version > max_version:
                    # 保存数据
                    _migrate = MigrationLog(version=version, script=f, success=True, project=_project)
                    _session.add(_migrate)
                    _session.commit()
        logger.info(f"success add migrate log")

    def __execute_migration_scripts(self) -> None:
        """
        执行migration脚本
        """
        _session: Session = self.session
        _project: str = self.project
        with CommitContext(_session):
            # 找出符合命名规则的migrate脚本
            regexp = re.compile(r'migration_prod_(\d+).py$')
            failed_fp = '/tmp/migration.failed'

            migrations_logs = _session.query(MigrationLog).filter(MigrationLog.project == _project).all()

            # 执行成功记录
            success_versions = sorted(set([_i.version for _i in filter(lambda _x: _x.success, migrations_logs)]))
            # 执行失败记录，且该版本后来也没有成功
            fail_versions = sorted(
                set([
                    _i.version
                    for _i in filter(
                        lambda _x: not _x.success and _x.version not in success_versions, migrations_logs
                    )])
            )

            # 当前执行成功的migration中的最大版本号
            max_success_version = -1
            if success_versions:
                max_success_version = max(success_versions)

            # migration文件名与版本号映射
            matches = dict()
            migration_file_list = os.listdir(self.script_path)
            for f in migration_file_list:
                match = regexp.match(f)
                if match is not None:
                    matches[f] = int(match.group(1))

            # 无执行记录的migration号
            executed_versions = success_versions + fail_versions
            no_executed_versions = sorted([v for v in matches.values() if v not in executed_versions])

            logger.info('max successful version: %s' % str(max_success_version))
            logger.info('successful versions: %s' % str(success_versions))
            logger.info('failed versions: %s' % str(fail_versions))
            logger.info('non-executed versions: %s' % str(no_executed_versions))

            with open(failed_fp, 'w') as fp:
                line = str(fail_versions)
                fp.write(line)

            files = sorted(filter(lambda x: matches.get(x) is not None, migration_file_list), key=lambda x: matches[x])
            for f in files:
                version = matches[f]
                if version > max_success_version:
                    migrate_func = os.path.splitext(os.path.basename(f))[0]
                    # noinspection PyBroadException
                    try:
                        migrations = __import__(f'migrations.{migrate_func}')
                        migrations_prod = getattr(migrations, migrate_func)
                        migrations_prod.do()
                        success = True
                    except Exception as e:
                        logger.error(f"migration failed for {version}", exc_info=True)
                        success = False
                        raise e
                    finally:
                        # 保存数据
                        _migrate = MigrationLog(version=version, script=f, project=_project, success=success)
                        _session.add(_migrate)
                        _session.commit()

            logger.info('Migrate successfully')

    def do_migrate(self, *args, **kwargs) -> None:
        """
        执行migrate操作
        当服务没有初始化时, 仅调用初始化脚本，不回执行任何migrate脚本
        因此, 初始化脚本必须随服务版本变动而更新
        :return:
        """
        # 创建表
        self._generate_table()
        # 判断服务是否初始化
        _is_inited: bool = self.is_inited()
        logger.info(f"init state is {_is_inited}")
        if not _is_inited:
            self._init_data(*args, **kwargs)
            return
        # 执行脚本
        self.__execute_migration_scripts()
