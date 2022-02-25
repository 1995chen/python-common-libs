# TemplateBabel 使用说明

## 创建Babel配置文件
vim babel.cfg
```shell
[python: **.py]
```
## 创建翻译文件所在目录
```shell
mkdir translations
```

## 生成pot文件
```shell
pybabel extract -F babel.cfg . -o translations/messages.pot
pybabel init -l en_US -d ./translations -i ./translations/messages.pot
# 必须创建默认的zh_CN语言支持
pybabel init -l zh_CN -d ./translations -i ./translations/messages.pot
```

## 生成mo文件
```shell
pybabel compile -f -d ./translations
```

## Sample

```python
import template_logging
from template_babel import TemplateBabel, get_text as _
import threading
import inject

logger = template_logging.getLogger(__name__)
thread_local = threading.local()


def my_config(binder):
    binder.bind(TemplateBabel, TemplateBabel("messages", "./translations"))


if __name__ == '__main__':
    inject.configure(my_config)

    translate_cfg = inject.instance(TemplateBabel)
    logger.info(_("hello"))
    translate_cfg.set_lang("en_US")
    logger.info(_("hello"))
    translate_cfg.set_lang("zh_CN")
    setattr(thread_local, "lang", "zh_CN")
    logger.warning(_("hello"))

```