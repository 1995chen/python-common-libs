# TemplateLogging 使用说明

## 正常接入

代码示例

```python
import template_logging
from flask import Flask, make_response

app = Flask(__name__)
# 初始化日志
template_logging.init_logger()
logger = template_logging.getLogger(__name__)


@app.route('/', methods=['GET'])
def info():
    logger.info("hello....")
    return make_response({
        'hello': "hello",
    })


if __name__ == '__main__':
    logger.info("hello-info")
    logger.warning("hello-warning")
    app.run("0.0.0.0", 8888)


```

## 覆盖celery等第三方日志

代码示例

```python
import template_logging
from flask import Flask, make_response

app = Flask(__name__)
# 初始化日志
template_logging.init_logger()
logger = template_logging.getLogger(__name__)
# 在程序运行时执行以下代码
template_logging.getLogger("template_rbac.base")
template_logging.getLogger("template_rbac.api")
template_logging.getLogger("template_rbac.lark")


@app.route('/', methods=['GET'])
def info():
    logger.info("hello....")
    return make_response({
        'hello': "hello",
    })


if __name__ == '__main__':
    logger.info("hello-info")
    logger.warning("hello-warning")
    app.run("0.0.0.0", 8888)

```

## 本地环境使用
设置环境变量来覆盖默认的日志位置
```shell
LOG_CONFIG_PATH=/Users/xxx/logs
```
