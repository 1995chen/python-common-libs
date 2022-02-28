# -*- coding: UTF-8 -*-


import logging
from typing import Dict, Any
from urllib.parse import (
    urlencode, urlparse, parse_qsl, urlunparse, urljoin
)

import jwt
from template_exception import (
    KeyParamsTypeInvalidException, TokenInvalidException
)

logger = logging.getLogger(__name__)


def decode_token(jwt_token: str, jwt_secret: str) -> Dict[str, Any]:
    """
    jwt token解码
    :param jwt_token:
    :param jwt_secret:
    :return:
    """
    if not isinstance(jwt_token, str):
        raise KeyParamsTypeInvalidException('jwt_token', str)
    try:
        jwt_obj = jwt.decode(jwt_token, key=jwt_secret, verify=True, algorithms=['HS256'])
    except (jwt.InvalidSignatureError, Exception):
        logger.error(f"invalid token {jwt_token}", exc_info=True)
        raise TokenInvalidException(jwt_token)
    return jwt_obj


def url_path_append(url_or_path: str, path: str) -> str:
    """
    将前后两端URL路径追加拼接在一起
    :param url_or_path:
    :param path:
    :return:
    """
    return urljoin(f"{url_or_path.rstrip('/')}/", path.lstrip('/'))


def url_query_join(url_or_path: str, **kwargs: Any) -> str:
    """
    对URL或URL的path进行拼接,将query参数拼入传人的url或path中
    :param url_or_path:
    :param kwargs: 需要拼接的query参数的键值对
    :return: dst url string
    """
    # 将URL进行拆分
    url_parts = list(urlparse(url_or_path))
    # 获得query参数构成的字典
    query = dict(parse_qsl(url_parts[4]))
    # 新增query参数
    query.update(kwargs)
    # 将query参数放入url数组中
    url_parts[4] = urlencode(query)
    # 构建url
    return urlunparse(url_parts)
