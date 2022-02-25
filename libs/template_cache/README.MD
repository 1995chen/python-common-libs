# TemplateCache 使用说明

## 代码示例

```python
from typing import Any, Optional, Callable

import inject
from template_cache import Cache

# 存储缓存仓库
cache_store = dict()


def get_cache_handler(key: str, timeout: Optional[int], **user_kwargs) -> Any:
    """
    获得缓存的handler
    """
    return cache_store.get(key, None)


def store_cache_handler(key: str, value: Any, timeout: Optional[int], **user_kwargs) -> Any:
    """
    存储cache的handler
    """
    cache_store[key] = value


def generate_cache_key_handler(func: Callable, *args: Any, **kwargs: Any) -> str:
    return func.__module__ + '.' + func.__name__


def my_config(binder):
    cache_instance: Cache = Cache()
    # 设置handler
    cache_instance.set_get_cache_handler(get_cache_handler)
    cache_instance.set_store_cache_handler(store_cache_handler)
    cache_instance.set_generate_cache_key_handler(generate_cache_key_handler)
    binder.bind(Cache, cache_instance)


if __name__ == '__main__':
    inject.configure(my_config)

    cache: Cache = inject.instance(Cache)


    @cache.use_cache()
    def test_add_func(a: int, b: int):
        """
        这是一个测试方法，接下来会对该方法进行缓存
        """
        return a + b


    v1 = test_add_func(1, 2)
    c1 = test_add_func(1, 2)
    print(v1, c1)

```
