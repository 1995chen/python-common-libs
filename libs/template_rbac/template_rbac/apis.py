# -*- coding: UTF-8 -*-


import logging
import base64
import json
from typing import Any, Dict, Callable

from flask import redirect
from werkzeug.wrappers.response import Response
from flask_restful import Resource, reqparse
from template_exception import AuthorizedFailException

from .helpers import url_query_join

logger = logging.getLogger(__name__)


class TemplateSSOLogin(Resource):
    template_rbac = None

    @classmethod
    def get(cls) -> Response:
        """
        SSO登录Get 请求方法
        """
        parser = reqparse.RequestParser()
        parser.add_argument('code', type=str, default=None)
        parser.add_argument('state', type=str, default='')
        # 前端覆盖默认的重定向url
        parser.add_argument('redirect_url', type=str, default='')
        # 切换用户,仅测试环境生效
        parser.add_argument('target_user', type=str, default='')
        args = parser.parse_args()

        # 获得code
        code = args.pop('code')
        logger.info('获取SSO登录成功后,重定向返回code值: %s ' % code)

        # 重定向到登录
        if code is None:
            state_dict: Dict[str, Any] = dict()
            state_dict['state'] = args['state']
            state_dict['redirect_url'] = args['redirect_url']
            # 支持调试模式下切换用户
            if cls.template_rbac.debug_mode:
                state_dict['target_user'] = args['target_user']
            # 对state_dict进行base64加密
            state_base64: str = base64.b64encode(json.dumps(state_dict).encode('utf-8')).decode('utf-8')
            redirect_url: str = url_query_join(cls.template_rbac.sso_auth_url, state=state_base64)
            logger.info(f"redirect to {redirect_url}")
            return redirect(redirect_url)
        logger.info(f"auth code is {code}")

        # 定义默认值
        state_dict: Dict[str, Any] = {
            'state': '',
            'redirect_url': '',
            'target_user': '',
        }
        # 解析state
        if args['state']:
            try:
                state_json: str = base64.b64decode(args['state']).decode('utf-8')
                state_dict: Dict[str, Any] = json.loads(state_json)
            except Exception:
                logger.warning(f"invalid state({args['state']})", exc_info=True)
                raise AuthorizedFailException("invalid state")

        # 详细处理
        redirect_path: str = cls.template_rbac.after_get_code(
            state_dict['redirect_url'], state_dict['state'],
            state_dict.get('target_user'), code
        )
        # 返回前端页面
        return redirect(redirect_path)

    # 定义post方法
    post: Callable = get


class TemplateSSOLogout(Resource):
    template_rbac = None

    @classmethod
    def get(cls) -> Any:
        """
        登出
        """
        return cls.template_rbac.do_logout_handler()
