# TemplateApollo 使用说明

## 说明

该库修改了携程Apollo客户端源码,支持配置变更时调用handler

## 代码示例

```python
from typing import Dict, Any, List
from dataclasses import dataclass, Field

import inject
import template_logging
from template_apollo import ApolloClient
from dacite import from_dict
from dacite.dataclasses import get_fields

logger = template_logging.getLogger(__name__)


@dataclass
class Config:
    NAME: str = None
    DB: str = None


@inject.autoparams()
def init_config(apollo_client: ApolloClient) -> Config:
    _fields: List[Field] = get_fields(Config)
    config_dict: Dict[str, Any] = dict()
    for _field in _fields:
        _v: Any = apollo_client.get_value(_field.name)
        if _v:
            # 类型转换
            config_dict[_field.name] = _field.type(_v)
    _config = from_dict(Config, config_dict)
    return _config


def init_apollo() -> ApolloClient:
    def config_changed_handler(entry: Dict[str, Any]) -> Any:
        logger.info(f"get entry: {entry}")
        # 获取阿波罗实例
        _apollo_instance: ApolloClient = inject.instance(ApolloClient)
        # 重新绑定配置
        inject.clear_and_configure(my_config)
        # 停止当前线程
        _apollo_instance.stop()

    _instance: ApolloClient = ApolloClient(
        app_id="unittest",
        config_server_url="http://apollo.local.domain:13043"
    )
    _instance.set_config_changed_handler(config_changed_handler)
    _instance.start()
    return _instance


def my_config(binder):
    binder.bind_to_constructor(ApolloClient, init_apollo)
    binder.bind_to_constructor(Config, init_config)


# 将实例绑定到inject
inject.configure(my_config)

if __name__ == '__main__':
    _apollo_client: ApolloClient = inject.instance(ApolloClient)
    _apollo_client.get_value('some_key')
```

