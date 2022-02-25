# -*- coding: UTF-8 -*-


from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import func, Column, Integer, String, DateTime, Boolean

# 定义Base
Base = declarative_base()


class MigrationLog(Base):
    """
    数据库migrate需要的Model
    """
    __tablename__ = 'migration_logs'
    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键')
    create_user = Column(String(128), nullable=False, default='system', index=True, comment='创建用户')
    update_user = Column(String(128), nullable=False, default='system', onupdate='system', index=True, comment='更新用户')
    create_time = Column(DateTime, nullable=False, default=func.now(), comment='创建时间')
    update_time = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now(), comment='修改时间')
    is_disabled = Column(Integer, nullable=False, default='0', index=True, comment='是否被禁用：启用 1：禁用')
    project = Column(String(32), nullable=False, default='', index=True)
    version = Column(Integer, nullable=False, index=True)
    script = Column(String(64), nullable=False, default='')
    success = Column(Boolean, nullable=False, default='')
