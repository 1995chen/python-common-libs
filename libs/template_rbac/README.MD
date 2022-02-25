# TemplateRbac 使用说明

## OAuth2接入

代码示例

```python
import inject
from template_rbac import OAuth2SSO
from flask import Flask

app = Flask(__name__)


def my_config(binder):
    oauth2_instance: OAuth2SSO = OAuth2SSO(
        "xxxxx",
        "xxxxx",
        "https://www.baidu.com",
        "/api/login",
        "xxxxx",
        True
    )
    # 设置handler
    # oauth2_instance.set_generate_token_handler()
    binder.bind(OAuth2SSO, oauth2_instance)


@app.route('/', methods=['GET'])
def info():
    from flask import make_response
    return make_response({
        'hello': "hello",
    })


if __name__ == '__main__':
    inject.configure(my_config)

    sso_cfg = inject.instance(OAuth2SSO)
    # 注册
    app.register_blueprint(sso_cfg.get_resources())

    app.run("0.0.0.0", 443, ssl_context='adhoc')

```

## 飞书接入

代码示例

```python
import inject
from template_rbac import LarkSSO
from flask import Flask

app = Flask(__name__)


def my_config(binder):
    lark_instance: LarkSSO = LarkSSO(
        "xxxxx",
        "xxxxx",
        "https://www.baidu.com",
        "/api/login",
        "xxxxx",
        True
    )
    # 设置handler
    # lark_instance.set_generate_token_handler()
    binder.bind(LarkSSO, lark_instance)


@app.route('/', methods=['GET'])
def info():
    from flask import make_response
    return make_response({
        'hello': "hello",
    })


if __name__ == '__main__':
    inject.configure(my_config)

    sso_cfg = inject.instance(LarkSSO)
    # 注册
    app.register_blueprint(sso_cfg.get_resources())

    app.run("0.0.0.0", 443, ssl_context='adhoc')

```

## 一些handler

### set_generate_token_handler

```python
import typing


def set_generate_token_handler(handler: typing.Callable):
    pass


# 这里handler方法会接收到一个字典对象
# payload是jwt toke的内容
# 该handler的执行在jwt加密之前
def handler(payload: typing.Dict)
    pass
```

### set_before_redirect_handler

```python
import typing


def set_before_redirect_handler(handler: typing.Callable):
    pass


# 这里handler方法会接收到一个字典对象
# args是query string的内容
# 该handler在认证通过后，返回重定向url前执行,args 会带入到重定向的query string中
def handler(args: typing.Dict)
    pass
```

### logout_handler

该handler必须实现,在注销登录时调用

```python
import typing


def set_logout_handler(self, handler: typing.Callable):
    pass


def handler()
    pass
```

# Auth 使用说明

代码示例

```python
from typing import Optional, Any, Dict
import inject
from template_rbac import LarkSSO, Auth, AuthStore
from flask import Flask, request

app = Flask(__name__)


# 定义一些handler
def get_user_roles_handler(user_info: Any):
    pass
    return user_info['roles']


def user_define_validator_handler(user_info: Any, jwt_obj: Dict[str, Any]):
    pass
    print(user_info)
    print(jwt_obj)
    pass


def get_user_info_handler(jwt_obj: Dict[str, Any]):
    info = jwt_obj['data']
    info['uid'] = 'uid'
    info['roles'] = ["2222", "xxxx"]
    return info


def my_config(binder):
    binder.bind(LarkSSO, LarkSSO(
        "xxxxxxx",
        "yyyyyy",
        "http://127.0.0.1:8888",
        "/api/login",
        "xxxxx",
        None,
        True
    ))

    auth: Auth = Auth("xxxxx")
    auth.set_get_user_roles_handler(get_user_roles_handler)
    auth.set_user_define_validator_handler(user_define_validator_handler)
    auth.set_get_user_info_handler(get_user_info_handler)
    binder.bind(Auth, auth)


@app.before_request
def before_request():
    auth: Auth = inject.instance(Auth)
    token: Optional[str] = request.headers.get("Authorization") or request.args.get("token")
    # 豁免认证
    if not auth.check_run_auth(request.endpoint, app.view_functions):
        return
    # 设置token
    auth.set_token(token)


if __name__ == '__main__':
    inject.configure(my_config)

    sso_cfg = inject.instance(LarkSSO)
    # 注册
    app.register_blueprint(sso_cfg.get_resources())

    auth: Auth = inject.instance(Auth)


    @app.route('/', methods=['GET'])
    @auth.auth(require_roles=["1", "2"])
    def info():
        from flask import make_response
        from flask_restful import reqparse

        parser = reqparse.RequestParser()
        parser.add_argument('token', type=str, default='')
        parser.add_argument('state', type=str, default='')
        auth_store: AuthStore = auth.get_auth_store()
        print(auth_store)
        return make_response({
            'hello': "hello",
        })


    app.run("0.0.0.0", 8888)

```

## @auth.auth(require_roles=[])

该注解需要配合set_get_user_roles_handler中设置的handler一起使用,如何注解中require_roles与set_get_user_roles_handler 返回的角色有交集，则认证成功

## auth.check_run_auth

该方法主要用于在before_request跳过一些豁免认证的请求，该方法需要与exclude_from_auth使用

## auth.set_token(token)

该方法会存储token到thread local中，并配合set_get_user_info_handler将用户的详情也存入threadlocal中
，该方法默认会调用user_define_validator_handler，主要用于调用一些用户的自定义验证
