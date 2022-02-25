# TemplateTransaction 使用说明

## 说明

该库可以实现数据库操作后自动提交

## 代码示例

```python

import inject
from template_transaction import CommitContext, autocommit
from sqlalchemy.orm import scoped_session, Session


class MainDBSession(scoped_session, Session):
    """
    这是一个定义的Session Demo类
    """
    pass


# 使用方式一: 直接使用上下文管理器
def func_1():
    session = inject.instance(MainDBSession)
    with CommitContext(session):
        # do something
        pass


# 使用方式二: 使用注解
@autocommit(MainDBSession)
def func_2():
    pass
```

