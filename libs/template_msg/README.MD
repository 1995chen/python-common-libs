# TemplateMsg 使用说明

## 代码示例

```python
from typing import Any, Optional

import inject

# 存储缓存仓库
cache_store = dict()


def store_cache_handler(key: str, value: Any, timeout: Optional[int]) -> Any:
    """
    存储cache的handler
    """
    # 存储缓存
    cache_store[key] = value


def get_cache_handler(key: str) -> Any:
    """
    获得缓存的handler
    """
    _value: Any = cache_store.get(key, None)
    return _value


def my_config(binder):
    client: LarkClient = LarkClient(app_id="xxxx", app_secret="yyyy")
    # 配置handler
    client.set_store_cache_handler(store_cache_handler)
    client.set_get_cache_handler(get_cache_handler)
    binder.bind(LarkClient, client)


if __name__ == '__main__':
    inject.configure(my_config)

    from template_msg import LarkClient, ILarkMsgResult, IReceiveIDType

    lark_client: LarkClient = inject.instance(LarkClient)
    # 获得open_id
    open_id: str = lark_client.get_user_open_id("xxxx")
    open_id: str = lark_client.get_user_open_id("yyyy")
    # 发送消息
    send_res: ILarkMsgResult = lark_client.send_text_msg(IReceiveIDType.OPEN_ID, open_id, "今晚7点下班留下来开个会[Test]")
    # 回复消息
    reply_res: ILarkMsgResult = lark_client.reply_text_msg(send_res.data.message_id, "OK")
    # 撤回消息
    revoke_res: ILarkMsgResult = lark_client.revoke_msg(reply_res.data.message_id)

```
