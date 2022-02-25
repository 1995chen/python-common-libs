# TemplateMigration 使用说明

## 代码示例

实现handler

```python
# -*- coding: utf-8 -*-


import inject
import template_logging
from template_migration import Migration

logger = template_logging.getLogger(__name__)


def init_data_handler(*args, **kwargs) -> None:
    """
    初始化数据handler
    """
    logger.info("do init_data_handler done")


# 注册inject
def init_migrate() -> Migration:
    # 初始化
    migration_instance: Migration = Migration(
        database_uri='mysql+pymysql://root:123456@127.0.0.1:7000/default',
        project='test_project',
        workspace='./'
    )
    # 设置handler
    migration_instance.set_do_init_data_handler(init_data_handler)
    return migration_instance


def my_config(binder):
    binder.bind(Migration, init_migrate)


if __name__ == '__main__':
    inject.configure(my_config)

    # 执行migrate
    migration_instance: Migration = inject.instance(Migration)
    migration_instance.do_migrate()
```
